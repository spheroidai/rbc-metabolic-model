# Task Execution Tracker

Use this file as the working plan for the current task.
Every non-trivial task should be represented here before implementation.

---

## Current Task
- Task: Implement and prepare the new upstream-core glycolysis probe benchmark
- Goal: Test whether the unresolved `G6P` / `AMP` / `PYR` mismatch is driven by the upstream HK/PFK hexose-phosphate gate and ATP coupling before reopening lower-glycolysis, purine, or transport freedom
- User-visible outcome: A minimal new upstream probe path in calibration plus ready-to-run policy and benchmark manifest files
- Constraints: Keep scope minimal, preserve monitor gating, preserve report/eval compatibility, avoid lower-glycolysis/purine/transport redesign, and avoid strategy changes beyond the dedicated probe manifest
- Risks: The probe may still improve score without resolving the shared `G6P` branch-point behavior, and ATP-coupling terms may compensate numerically without fixing the true bottleneck

---

## Calibration / Model Context
- Policy / config under test: `config/policy_core_upstream_probe.json`
- Benchmark manifest: `config/rbc_core_upstream_probe_benchmarks.json`
- Target scope: `core_glycolysis_energy`
- Parameter scope: `core_upstream_glycolysis_probe`
- Optimization strategy: `joint_vmax_km`
- Baseline artifact path: `Simulations/brodbar/calibration/best_params.json`
- Protected metrics / guardrails: `glycolysis_energy`, `glycolysis`, `extracellular`, endpoint protection, `allowed_optimization_strategies=["joint_vmax_km"]`
- Exact validation command: `python scripts/run_calibration_eval.py --policy config/policy_core_upstream_probe.json --manifest config/rbc_core_upstream_probe_benchmarks.json`

---

## Evidence / Context
- Reported issue or request: Define the next narrow upstream-core probe after the mixed lower-glycolysis probe showed only modest improvement and left `G6P`, `AMP`, and `PYR` as the dominant residual blockers
- Relevant files: `src/MM_calibration.py`, `config/policy_core_upstream_probe.json`, `config/rbc_core_upstream_probe_benchmarks.json`, `tasks/todo.md`
- Relevant components/services: calibration scope selection, benchmark harness, objective bundle monitor gating
- Current benchmark evidence: `EGLC` and `ELAC` remain relatively good, while the dominant unresolved block sits at the upstream hexose-phosphate gate and adenylate coupling rather than in transport or lower-glycolysis pacing alone
- Notes from documentation (Context7): None needed for this step
- Notes from browser verification (Playwright): Not applicable

---

## Plan
- [x] Define the narrow upstream-core probe hypothesis and allowed parameter set
- [x] Add the new upstream probe scope in `src/MM_calibration.py`
- [x] Create the dedicated upstream policy and benchmark manifest files
- [ ] Run syntax and JSON verification
- [ ] Record the exact rerun command and summarize the new scope

---

## Implementation Notes
### Step 1
- Status: Completed
- Notes: Chose a strict upstream gate scope around HK/PFK entry pacing and ATP coupling, without reopening lower-glycolysis, purine, or transport compensators.

### Step 2
- Status: Completed
- Notes: Added `core_upstream_glycolysis_probe` to `src/MM_calibration.py` as a phase-1-only parameter scope containing only `km_GLC_HK`, `km_G6P`, `km_F6P`, `km_ATP_HK`, `km_ATP_PFK`, `vmax_VHK`, and `vmax_VPFK`.

### Step 3
- Status: Completed
- Notes: Created `config/policy_core_upstream_probe.json` and `config/rbc_core_upstream_probe_benchmarks.json` using the same `joint_vmax_km` strategy and benchmark structure as the previous focused probe for clean comparison.

---

## Verification Checklist
- [ ] Syntax / type checks pass if applicable
- [ ] Lint passes if applicable
- [ ] Build passes if applicable
- [ ] Relevant unit/integration tests pass
- [ ] Benchmark or report comparison completed
- [ ] Exact commands recorded
- [ ] Browser flow verified with Playwright if applicable
- [ ] UI visually checked if applicable
- [ ] No obvious regression found

---

## Files Changed
- `src/MM_calibration.py`
- `config/policy_core_upstream_probe.json`
- `config/rbc_core_upstream_probe_benchmarks.json`
- `tasks/todo.md`
