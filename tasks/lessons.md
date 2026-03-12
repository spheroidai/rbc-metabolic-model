# Project Lessons

Use this file to capture recurring mistakes, corrections, and durable operating rules.
Update it after any user correction, preventable miss, failed assumption, or repeated debugging pattern.

---

## Entry Template

### [YYYY-MM-DD] Lesson Title
- Context:
- What went wrong:
- Pattern behind the mistake:
- New preventive rule:
- Early detection signal:
- What to do differently next time:

---

## Lessons

### [2026-03-11] Experimental mapping errors can dominate calibration
- Context: Calibration behavior was being judged from extreme outliers in glycolysis intermediates.
- What went wrong: An experimental mapping issue can make the optimizer chase non-physiologic states.
- Pattern behind the mistake: Trusted the target mapping before validating whether the experimental column was biologically plausible.
- New preventive rule: Validate suspicious experimental mappings before tuning parameters around a catastrophic outlier.
- Early detection signal: A short-lived intermediate is being fit to a large stable concentration curve or is orders of magnitude above expected scale.
- What to do differently next time: Check the experimental-to-model mapping and metabolite scale first, then decide whether the target belongs in the objective.

### [2026-03-11] New target scopes must preserve monitor gating
- Context: A focused calibration target was added for core glycolysis and energy behavior.
- What went wrong: It is easy to add a new target scope without also wiring monitor objectives and regression limits.
- Pattern behind the mistake: Changed the primary objective path but forgot the acceptance and protection path.
- New preventive rule: When adding a target scope, verify monitor objectives, protected metrics, and regression gating in the same change.
- Early detection signal: A new scope runs, but acceptance logic no longer protects key pathway metrics or reports become less informative.
- What to do differently next time: Inspect the full objective bundle path, not only the main target selection logic.

### [2026-03-11] Establish identifiability before opening compensators
- Context: Broad calibration flexibility can improve score without resolving the core mismatch.
- What went wrong: Opening transport or salvage compensators too early can hide the real glycolysis or energy defect.
- Pattern behind the mistake: Increased search freedom before the hypothesis about the core pathway was tested cleanly.
- New preventive rule: Start with the narrowest parameter scope that can test the core hypothesis and only widen the search after that pass is stable.
- Early detection signal: Loss improves mainly through side-path parameters while core shapes or energy trajectories remain wrong.
- What to do differently next time: Run a focused benchmark first, then add a narrow second pass only if the evidence supports it.

### [2026-03-11] Benchmark artifacts matter more than a single figure
- Context: Calibration decisions were being made from a mixture of plots and individual runs.
- What went wrong: A single figure can overstate improvement or hide regressions outside the inspected subset.
- Pattern behind the mistake: Promoted conclusions from local visual impressions instead of the benchmark harness output.
- New preventive rule: Use manifest-driven benchmark outputs, reports, and before/after comparisons to judge whether a change should be kept.
- Early detection signal: A run looks better in one plot, but robustness across seeds, horizons, or guarded cases is unknown.
- What to do differently next time: Record the exact manifest, commands, and benchmark evidence before concluding that a calibration change worked.

### [2026-03-11] ODE sign edits require immediate conservation checks
- Context: Redox cofactor equations and related flux signs are easy to edit incorrectly.
- What went wrong: A sign or source/sink mistake can silently break pool conservation and distort long-horizon behavior.
- Pattern behind the mistake: Focused on local equation intent without checking the total conserved pool after the edit.
- New preventive rule: After editing ODE signs or state mappings, verify conservation identities and inspect for unintended net creation or loss.
- Early detection signal: Conserved pools drift strongly over time without a biologic mechanism that explains the change.
- What to do differently next time: Pair every ODE sign change with an explicit conservation check and a before/after verification note.

### [2026-03-11] Do not promote a core calibration if EGLC and ELAC still fail
- Context: A focused `km_only` benchmark improved aggregate score and final loss.
- What went wrong: Score improvement was not enough to justify promotion because key extracellular anchors still looked biologically wrong.
- Pattern behind the mistake: Interpreting benchmark progress as pathway resolution before checking whether core glucose input and lactate output were actually reproduced.
- New preventive rule: Never promote a focused RBC calibration to a wider follow-up if **EGLC** and **ELAC** still fail curve triage, even when the aggregate score improves.
- Early detection signal: Aggregate loss improves but EGLC depletion and ELAC accumulation remain visibly incorrect, while AMP/P3G/PYR stay problematic.
- What to do differently next time: Use physiological anchors first, then score second, when deciding whether a calibration campaign is promotion-ready.
