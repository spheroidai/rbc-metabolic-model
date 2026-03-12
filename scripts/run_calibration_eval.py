import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from MM_calibration import run_calibration


# Keep TSV schema stable for backward compatibility.
RESULT_FIELDS = [
    'timestamp',
    'policy_name',
    'manifest_name',
    'aggregate_score',
    'mean_final_loss',
    'mean_improvement_pct',
    'best_case',
    'worst_case',
    'status',
    'run_dir',
]


def read_json(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def append_results_row(results_tsv: Path, row: dict):
    ensure_parent(results_tsv)
    file_exists = results_tsv.exists()
    with open(results_tsv, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS, delimiter='\t')
        if not file_exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, '') for field in RESULT_FIELDS})


def read_best_score(results_tsv: Path, manifest_name: Optional[str] = None):
    if not results_tsv.exists():
        return None
    with open(results_tsv, newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        scores = []
        for row in reader:
            if manifest_name and row.get('manifest_name') != manifest_name:
                continue
            try:
                scores.append(float(row['aggregate_score']))
            except (KeyError, TypeError, ValueError):
                continue
    if not scores:
        return None
    return min(scores)


def get_policy_stage_plan(policy: dict) -> Optional[list]:
    stage_plan = policy.get('stage_plan')
    if isinstance(stage_plan, list) and stage_plan:
        return stage_plan
    return None


def get_base_strategy(policy: dict) -> str:
    return policy.get('base_run', {}).get('optimization_strategy', 'legacy')


def merge_run_config(policy: dict, overrides: dict, out_dir: Path):
    base_run = dict(policy.get('base_run', {}))
    merged = dict(base_run)
    merged.update(overrides)
    merged['out_dir'] = str(out_dir)

    # Pass top-level stage plan through to run_calibration when present,
    # unless explicitly overridden by the case.
    if 'stage_plan' not in merged:
        policy_stage_plan = get_policy_stage_plan(policy)
        if policy_stage_plan is not None:
            merged['stage_plan'] = policy_stage_plan

    return merged


def apply_guardrails(run_kwargs: dict, policy: dict):
    guardrails = policy.get('guardrails', {}) or {}

    if guardrails.get('require_generate_plots_false', False):
        run_kwargs['generate_plots'] = False

    t_max = run_kwargs.get('t_max')
    min_t_max = guardrails.get('min_t_max')
    max_t_max = guardrails.get('max_t_max')
    if t_max is not None:
        if min_t_max is not None and float(t_max) < float(min_t_max):
            raise ValueError(f"t_max={t_max} violates min_t_max={min_t_max}")
        if max_t_max is not None and float(t_max) > float(max_t_max):
            raise ValueError(f"t_max={t_max} violates max_t_max={max_t_max}")

    curve_fit_strength = run_kwargs.get('curve_fit_strength')
    max_curve_fit_strength = guardrails.get('max_curve_fit_strength')
    if curve_fit_strength is not None and max_curve_fit_strength is not None:
        if float(curve_fit_strength) > float(max_curve_fit_strength):
            raise ValueError(
                f"curve_fit_strength={curve_fit_strength} violates "
                f"max_curve_fit_strength={max_curve_fit_strength}"
            )

    allowed_strategies = guardrails.get('allowed_optimization_strategies')
    strategy = run_kwargs.get('optimization_strategy', 'legacy')
    if allowed_strategies and strategy not in allowed_strategies:
        raise ValueError(
            f"optimization_strategy='{strategy}' not allowed by guardrails: {allowed_strategies}"
        )

    return run_kwargs


def metabolite_scale_weight(per_metabolite_row: dict, scoring: dict):
    exp_mean_abs = float(
        per_metabolite_row.get(
            'exp_mean_abs',
            per_metabolite_row.get('norm_factor', 0.0),
        )
    )
    scale_rules = scoring.get('scale_weight_rules', [])
    for rule in scale_rules:
        max_exp_mean_abs = rule.get('max_exp_mean_abs')
        if max_exp_mean_abs is None or exp_mean_abs <= float(max_exp_mean_abs):
            return float(rule.get('weight', 1.0))
    return 1.0


def compute_robust_target_loss(case_report: dict, scoring: dict):
    per_metabolite = case_report.get('per_metabolite', [])
    if not per_metabolite:
        return None
    nrmse_cap = float(scoring.get('robust_nrmse_cap', 10.0))
    weighted_nrmses = []
    for row in per_metabolite:
        weighted_nrmses.append(
            min(float(row.get('nrmse', 0.0)), nrmse_cap)
            * metabolite_scale_weight(row, scoring)
        )
    top_k = int(scoring.get('robust_top_k', 0))
    if top_k > 0:
        weighted_nrmses = sorted(weighted_nrmses, reverse=True)[:top_k]
    if not weighted_nrmses:
        return None
    return sum(weighted_nrmses) / len(weighted_nrmses)


def count_discarded_stages_or_phases(case_report: dict) -> Tuple[int, int]:
    stage_reports = case_report.get('stage_reports')
    if isinstance(stage_reports, list) and stage_reports:
        total = len(stage_reports)
        accepted = sum(1 for stage in stage_reports if stage.get('accepted', True))
        return accepted, total

    phases = case_report.get('phases', {})
    if isinstance(phases, dict) and phases:
        total = 0
        accepted = 0
        for phase_data in phases.values():
            total += 1
            if phase_data.get('accepted'):
                accepted += 1
        return accepted, total

    return 0, 0


def compute_case_score(case_report: dict, scoring: dict):
    monitor_metrics = case_report.get('monitor_metrics', {})
    score_breakdown = {}

    final_loss_weight = float(scoring.get('final_loss_weight', scoring.get('target_loss_weight', 1.0)))
    final_loss_component = final_loss_weight * float(case_report['final_loss'])
    score_breakdown['final_loss_component'] = final_loss_component
    score = final_loss_component

    robust_target_loss = compute_robust_target_loss(case_report, scoring)
    if robust_target_loss is not None:
        robust_target_component = float(scoring.get('robust_target_weight', 0.0)) * robust_target_loss
        score_breakdown['robust_target_loss'] = robust_target_loss
        score_breakdown['robust_target_component'] = robust_target_component
        score += robust_target_component

    endpoint_component = float(scoring.get('endpoint_weight', 0.0)) * float(
        monitor_metrics.get('endpoint_nrmse', 0.0)
    )
    score_breakdown['endpoint_component'] = endpoint_component
    score += endpoint_component

    for metric_name, metric_weight in scoring.get('monitor_weights', {}).items():
        metric_component = float(metric_weight) * float(monitor_metrics.get(metric_name, 0.0))
        score_breakdown[f'{metric_name}_component'] = metric_component
        score += metric_component

    accepted_count, total_count = count_discarded_stages_or_phases(case_report)
    discarded = max(total_count - accepted_count, 0)
    discard_component = float(scoring.get('discard_penalty', 0.0)) * discarded
    score_breakdown['discard_component'] = discard_component
    score += discard_component

    score_breakdown['total_score'] = score
    return score, score_breakdown


def evaluate_case(case: dict, policy: dict, run_root: Path, scoring: dict):
    case_dir = run_root / case['name']
    run_kwargs = merge_run_config(policy, case.get('run_overrides', {}), case_dir)
    run_kwargs = apply_guardrails(run_kwargs, policy)

    run_calibration(**run_kwargs)

    report_path = case_dir / 'calibration_report.json'
    if not report_path.exists():
        raise FileNotFoundError(f"Expected calibration report not found: {report_path}")

    report = read_json(report_path)
    score, score_breakdown = compute_case_score(report, scoring)

    return {
        'name': case['name'],
        'description': case.get('description', ''),
        'weight': float(case.get('weight', 1.0)),
        'score': score,
        'score_breakdown': score_breakdown,
        'report': report,
        'report_path': str(report_path),
        'effective_run_kwargs': run_kwargs,
    }


def summarize_cases(case_results: list):
    if not case_results:
        raise ValueError("Manifest contains no cases to evaluate.")

    total_weight = sum(case['weight'] for case in case_results)
    weighted_score = sum(case['score'] * case['weight'] for case in case_results) / max(total_weight, 1e-12)
    mean_final_loss = sum(float(case['report']['final_loss']) for case in case_results) / len(case_results)
    mean_improvement_pct = sum(float(case['report']['improvement_pct']) for case in case_results) / len(case_results)
    best_case = min(case_results, key=lambda case: case['score'])
    worst_case = max(case_results, key=lambda case: case['score'])

    return {
        'aggregate_score': weighted_score,
        'mean_final_loss': mean_final_loss,
        'mean_improvement_pct': mean_improvement_pct,
        'best_case': best_case['name'],
        'worst_case': worst_case['name'],
    }


def main():
    parser = argparse.ArgumentParser(description='Fixed eval harness for RBC calibration outer-loop autoresearch')
    parser.add_argument('--policy', type=str, default=str(ROOT / 'config' / 'rbc_autoresearch_policy.json'))
    parser.add_argument('--manifest', type=str, default=str(ROOT / 'config' / 'rbc_calibration_benchmarks.json'))
    args = parser.parse_args()

    policy_path = Path(args.policy).resolve()
    manifest_path = Path(args.manifest).resolve()
    policy = read_json(policy_path)
    manifest = read_json(manifest_path)

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    run_root = ROOT / 'Simulations' / 'brodbar' / 'autoresearch' / f"{timestamp}_{policy['policy_name']}"
    run_root.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(policy_path, run_root / 'policy_snapshot.json')
    shutil.copyfile(manifest_path, run_root / 'manifest_snapshot.json')

    case_results = []
    for case in manifest.get('cases', []):
        print(f"\n=== Running case: {case['name']} ===")
        case_results.append(
            evaluate_case(
                case=case,
                policy=policy,
                run_root=run_root,
                scoring=manifest.get('scoring', {}),
            )
        )

    summary = summarize_cases(case_results)

    results_tsv = ROOT / Path(manifest['results_tsv'])
    best_prior_score = read_best_score(results_tsv, manifest_name=manifest.get('manifest_name'))
    if best_prior_score is None:
        status = 'baseline'
    elif summary['aggregate_score'] <= best_prior_score:
        status = 'keep'
    else:
        status = 'discard'

    base_strategy = get_base_strategy(policy)

    summary_payload = {
        'timestamp': timestamp,
        'policy_name': policy['policy_name'],
        'manifest_name': manifest['manifest_name'],
        'manifest_description': manifest.get('description') or manifest.get('notes', ''),
        'optimization_strategy': base_strategy,
        'parameter_classes': policy.get('base_run', {}).get('parameter_classes'),
        'stage_plan': get_policy_stage_plan(policy),
        'status': status,
        'summary': summary,
        'case_results': [
            {
                'name': case['name'],
                'description': case.get('description', ''),
                'weight': case['weight'],
                'score': case['score'],
                'score_breakdown': case['score_breakdown'],
                'report_path': case['report_path'],
                'effective_run_kwargs': case['effective_run_kwargs'],
                'optimization_strategy': case['report'].get(
                    'optimization_strategy',
                    case['effective_run_kwargs'].get('optimization_strategy', base_strategy),
                ),
                'parameter_classes': case['report'].get(
                    'parameter_classes',
                    case['effective_run_kwargs'].get('parameter_classes'),
                ),
                'final_loss': case['report']['final_loss'],
                'improvement_pct': case['report']['improvement_pct'],
                'monitor_metrics': case['report'].get('monitor_metrics', {}),
            }
            for case in case_results
        ],
    }
    with open(run_root / 'eval_summary.json', 'w') as f:
        json.dump(summary_payload, f, indent=2)

    append_results_row(
        results_tsv,
        {
            'timestamp': timestamp,
            'policy_name': policy['policy_name'],
            'manifest_name': manifest['manifest_name'],
            'aggregate_score': summary['aggregate_score'],
            'mean_final_loss': summary['mean_final_loss'],
            'mean_improvement_pct': summary['mean_improvement_pct'],
            'best_case': summary['best_case'],
            'worst_case': summary['worst_case'],
            'status': status,
            'run_dir': str(run_root),
        },
    )

    print('\n=== RBC outer-loop evaluation summary ===')
    print(f"policy: {policy['policy_name']}")
    print(f"optimization_strategy: {base_strategy}")
    if get_policy_stage_plan(policy):
        print(f"stage_plan: {len(get_policy_stage_plan(policy))} stages")
    print(f"aggregate_score: {summary['aggregate_score']:.6f}")
    print(f"mean_final_loss: {summary['mean_final_loss']:.6f}")
    print(f"mean_improvement_pct: {summary['mean_improvement_pct']:.3f}")
    print(f"best_case: {summary['best_case']}")
    print(f"worst_case: {summary['worst_case']}")
    print(f"status: {status}")
    print(f"run_dir: {run_root}")


if __name__ == '__main__':
    main()