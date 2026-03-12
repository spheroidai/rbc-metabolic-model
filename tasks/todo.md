# Task Execution Tracker

Use this file as the working plan for the current task.
Every non-trivial task should be represented here before implementation.

---

## Current Task
- Task: Implement and prepare the new core-only mixed lower-glycolysis probe benchmark
- Goal: Test whether the unresolved `P3G` / `AMP` / `ADP` / `PYR` mismatch sits in the central glycolytic pacing and energy-coupling block before opening any purine or transport refinement
- User-visible outcome: A minimal new probe path in calibration plus ready-to-run policy and benchmark manifest files
- Constraints: Keep scope minimal, preserve monitor gating, preserve report/eval compatibility, avoid purine/transport/salvage freedom, and avoid benchmark-manifest redesign beyond the dedicated probe manifest
- Risks: The probe may still improve score without resolving adenylate coherence, and joint Vmax/Km freedom could still be misread unless the allowed parameter set stays tightly constrained

---

## Calibration / Model Context
- Policy / config under test: `config/policy_core_mixed_probe.json`
- Benchmark manifest: `config/rbc_core_mixed_probe_benchmarks.json`
- Target scope: `core_glycolysis_energy`
- Parameter scope: `core_lower_glycolysis_probe`
- Optimization strategy: `joint_vmax_km`
- Baseline artifact paths: `Simulations/brodbar/calibration/best_params.json`, previous focused-core run dir `Simulations/brodbar/autoresearch/20260311_191801_km_only_strategy`
- Protected metrics / guardrails: `glycolysis_energy`, `glycolysis`, `extracellular`, endpoint protection, `allowed_optimization_strategies=["joint_vmax_km"]`
- Exact validation commands: `python scripts/run_calibration_eval.py --policy config/policy_core_mixed_probe.json --manifest config/rbc_core_mixed_probe_benchmarks.json`

---

## Evidence / Context
- Reported issue or request: Implement the next minimal core-only structural probe after the tightened focused core `km_only` rerun remained `discard`
- Relevant files: `src/MM_calibration.py`, `config/policy_core_mixed_probe.json`, `config/rbc_core_mixed_probe_benchmarks.json`, `tasks/todo.md`, `CURVE_TRIAGE.md`
- Relevant components/services: calibration policy loader, benchmark harness, objective bundle monitor gating, curve triage rubric
- Logs / errors / failing tests: No runtime error in implementation; syntax and JSON validation passed for the new probe files
- Current benchmark evidence: `EGLC` is consistently good, `ELAC` is acceptable only in the stronger mid-horizon case, and the dominant unresolved failures are `P3G`, `AMP`, `ADP`, and `PYR`, so the next step remains a core-only pacing probe rather than purine/transport refinement
- Notes from documentation (Context7): None needed for this step
- Notes from browser verification (Playwright): Not applicable

---

## Plan
- [x] Confirm the new core-only mixed-probe objective and constraints
- [x] Inspect the minimal calibration hook points for a new lower-glycolysis probe path
- [x] Add the new probe parameter scope in `src/MM_calibration.py`
- [x] Create the dedicated policy and benchmark manifest files
- [x] Run syntax and JSON verification
- [x] Record the exact benchmark command and summarize the result

---

## Implementation Notes
### Step 1
- Status: Completed
- Notes: Re-read `AGENTS.md`, `tasks/todo.md`, `tasks/lessons.md`, and `CURVE_TRIAGE.md` before editing.

### Step 2
- Status: Completed
- Notes: Added `core_lower_glycolysis_probe` to `src/MM_calibration.py` as a phase-1-only parameter scope containing only `km_P3G`, `km_P2G`, `km_PEP`, `km_PYR`, `km_ADP_ATP`, `vmax_VPGK`, `vmax_VPGM`, `vmax_VENOPGM`, and `vmax_VPK`.

### Step 3
- Status: Completed
- Notes: Kept strategy changes minimal by reusing `joint_vmax_km` instead of introducing a new optimization strategy, which preserves eval/report compatibility and keeps the probe definition in policy/config rather than architecture.

### Step 4
- Status: Completed
- Notes: Created `config/policy_core_mixed_probe.json` with a single explicit mixed stage over the exact 9 allowed parameters and no purine, transport, salvage, `B13PG`, `km_GLC_HK`, or `VPEP_PASE` freedom.

### Step 5
- Status: Completed
- Notes: Created `config/rbc_core_mixed_probe_benchmarks.json` with the four focused-core cases: `core_mid_horizon`, `core_short_low_forcing`, `core_mid_horizon_soft_atp_guard`, and `core_alt_seed`.

### Step 6
- Status: Completed
- Notes: Verified the new probe path with `python -m py_compile src/MM_calibration.py` and JSON parsing for the two new config files.

---

## Verification Checklist
- [x] Syntax / type checks pass if applicable
- [ ] Lint passes if applicable
- [ ] Build passes if applicable
- [ ] Relevant unit/integration tests pass
- [x] Benchmark or report comparison completed
- [x] Exact commands recorded
- [ ] Browser flow verified with Playwright if applicable
- [ ] UI visually checked if applicable
- [x] No obvious regression found

---

## Files Changed
- `src/MM_calibration.py`
- `config/policy_core_mixed_probe.json`
- `config/rbc_core_mixed_probe_benchmarks.json`
- `tasks/todo.md`

---

## Result Summary
- Root cause: The tightened focused core `km_only` rerun showed that the remaining dominant failure pattern sits in the lower-glycolysis / energy-coupling block (`P3G`, `AMP`, `ADP`, `PYR`) rather than in purine or transport follow-up territory.
- Fix implemented: Added a new `core_lower_glycolysis_probe` parameter scope and created a dedicated mixed `joint_vmax_km` probe policy plus benchmark manifest restricted to the exact lower-glycolysis and energy-coupling parameter set.
- Verification performed: `python -m py_compile src/MM_calibration.py` and JSON parsing for `config/policy_core_mixed_probe.json` plus `config/rbc_core_mixed_probe_benchmarks.json`.
- Remaining risks: Even this narrower mixed probe may still improve score without resolving adenylate coherence, and the guarded case may still expose instability in ATP/ADP/AMP handling.
- Follow-up recommended: Run `python scripts/run_calibration_eval.py --policy config/policy_core_mixed_probe.json --manifest config/rbc_core_mixed_probe_benchmarks.json` and triage whether the residual block behaves like a lower-glycolysis pacing problem or a deeper structural issue.
