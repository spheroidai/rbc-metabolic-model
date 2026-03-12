# AGENTS.md — Windsurf Operating Rules for GPT-5.4 High Thinking

## Mission
Build correct, minimal, maintainable software changes with strong reasoning, disciplined scope control, and explicit verification.

The standard is not “code that runs once.”
The standard is “code a strong senior engineer would approve.”

---

## Model Profile

This project is worked on with:
- **Windsurf**
- **GPT-5.4 High Thinking** as the coding agent
- MCPs:
  - **Context7** for up-to-date technical documentation and API/framework reference
  - **Playwright** for browser automation, UI inspection, and end-to-end verification

Use these strengths deliberately:
- GPT-5.4 High Thinking: reasoning-heavy debugging, architecture, root-cause analysis, refactors, multi-step planning
- Context7: confirm current framework/library behavior before implementing
- Playwright: validate real UI flows, rendering, interactions, regressions

---

## 1. Default Execution Mode

### Plan-first by default for non-trivial work
Enter plan mode before making changes for any task involving:
- 3+ meaningful steps
- architecture or schema changes
- multiple files or systems
- unclear root cause
- stateful UI flows
- backend/frontend interaction
- risk of regressions
- refactors with behavior impact

For small isolated changes, direct execution is allowed, but verification is still required.

### Core rule
Do not jump into implementation just because code can be edited quickly.
First determine:
1. the objective
2. the current behavior
3. the likely root cause or design constraint
4. the best implementation path
5. the verification path

### Re-plan rule
If new evidence invalidates the plan:
- stop
- update the plan
- continue only once the new path is coherent

Do not keep pushing through a broken assumption.

---

## 2. Planning Standard

Before implementation, produce a short working plan.

The plan should cover:
- the problem to solve
- the likely root cause or target area
- the files/components likely involved
- the constraints
- the risks
- the validation strategy
- the execution order

### Planning rules
- Break work into checkable items
- Prefer small reversible steps
- Distinguish facts from assumptions
- Prefer the simplest complete solution
- Avoid speculative redesign unless evidence supports it

### Planning artifacts
Maintain:
- `tasks/todo.md` for active execution
- `tasks/lessons.md` for persistent learning

---

## 3. Documentation and Research Policy

### Use Context7 whenever current docs matter
Before implementing or changing behavior involving frameworks, libraries, SDKs, APIs, or tooling:
- consult **Context7**
- prefer official/current documentation patterns
- verify version-sensitive behavior before coding

This is especially important for:
- Next.js
- React
- TypeScript
- Vercel-related patterns
- Supabase
- LangChain / LangGraph
- Playwright usage
- package configuration
- framework conventions that may have changed

### Rules
- Do not rely on stale memory when current docs are likely relevant
- Do not invent APIs or options
- Align implementation with actual documented behavior

---

## 4. Debugging Policy

When given a bug:
do not ask the user to manually debug what the codebase, logs, tests, or browser inspection can reveal.

### Default debugging workflow
1. Reconstruct the reported issue
2. Inspect relevant logs, stack traces, failing tests, and code paths
3. Identify the most likely root cause
4. Validate the hypothesis against evidence
5. Implement the smallest complete fix
6. Verify the fix in the most direct way possible

### Root-cause rules
- Fix causes, not symptoms
- Avoid blind trial-and-error editing
- Do not stack multiple speculative fixes
- If evidence is weak, investigate more before changing code
- If CI or local tests fail, treat that as primary evidence

### Strong default
A bug report is a request to diagnose and resolve, not a request to ask the user for step-by-step guidance.

---

## 5. Scope Control

Keep changes tight.

### Rules
- Make the smallest effective change
- Avoid unrelated edits in the same patch
- Preserve existing conventions unless there is a compelling reason not to
- Avoid broad rewrites unless the current structure clearly blocks a correct solution
- Minimize blast radius

### Prefer
- targeted fixes
- local refactors
- explicit logic
- small clean abstractions

### Avoid
- cosmetic churn
- opportunistic refactors during a bug fix
- renaming/moving files without benefit
- mixing cleanup with critical changes

---

## 6. Elegance Standard

For non-trivial work, ask:
- Is there a simpler design?
- Is this the right abstraction level?
- Is this solving the real problem?
- Is the solution easy to understand and maintain?

### Balanced rule
If a fix feels brittle or hacky, step back and find the cleaner solution.
If the task is simple, do not over-engineer it.

Elegance means:
- less complexity
- better local reasoning
- lower coupling
- easier verification
- clearer future maintenance

It does not mean unnecessary abstraction.

---

## 7. Verification Before Done

Never mark work complete without proof.

### Required verification
Use the right combination for the task:
- tests
- type checks
- lint
- build validation
- logs
- API checks
- before/after behavior comparison
- Playwright flow verification
- visual inspection when UI is affected

### Definition of done
The task is done only when:
- the intended issue is addressed
- the implementation is coherent with the codebase
- verification has been performed
- obvious regressions were considered
- results are documented

### Final quality gate
Ask:
**Would a strong staff engineer approve this after review?**

If not, refine.

---

## 8. Playwright Verification Policy

Use **Playwright** whenever the task affects:
- UI rendering
- forms
- navigation
- authentication flows
- dashboard behavior
- multi-step interaction
- state transitions visible in browser
- regressions best detected through real interaction

### Use Playwright to
- reproduce UI bugs
- inspect rendered behavior
- verify flows end-to-end
- confirm fixes in browser
- detect interaction regressions
- validate selectors, forms, and navigation outcomes

### Rules
- Prefer direct browser verification over guesswork for UI issues
- Use Playwright after changes that materially affect user-facing flows
- If the issue is visual or interaction-based, do not rely only on static code inspection

---

## 9. Communication Standard

Communicate like an execution-focused senior engineer.

### At the start
State:
- what you think is happening
- what you will inspect or change
- how you will verify it

### During work
Provide concise updates:
- what was found
- what changed
- what remains
- what risk or uncertainty exists

### At the end
Summarize:
- root cause
- files changed
- implementation summary
- verification performed
- residual risks or follow-ups

### Style
- direct
- structured
- honest about uncertainty
- not verbose for its own sake
- not vague about verification

---

## 10. Lessons and Self-Improvement

Every correction should improve future performance.

### After any user correction or avoidable miss

Update `tasks/lessons.md` with:

- what went wrong
- the failure pattern
- the new preventive rule
- the early detection signal

### Goal

Reduce repeated mistakes across the same project.

### Mandatory mindset

Do not just fix the current issue.
Also improve the operating rule that caused the miss.

---

## 11. Windsurf-Specific Working Style

Because this project is worked on in Windsurf with GPT-5.4 High Thinking:

### Preferred operating posture

- Think deeply before changing important code
- Keep plans explicit for multi-step tasks
- Use MCPs actively instead of guessing
- Verify in-browser when UI is involved
- Keep final changes minimal and defensible

### Use the right tool for the right problem

- **GPT-5.4 High Thinking**: analysis, architecture, debugging, refactor design, reasoning under ambiguity
- **Context7**: current docs, framework behavior, API validation
- **Playwright**: reproduction, browser verification, E2E flow validation

### Anti-pattern
Do not use deep reasoning as an excuse for slow speculative wandering.
Reason deeply, then act decisively.

---

## 12. Task Workflow

For every meaningful task:

1. Write or update the checklist in `tasks/todo.md`
2. Confirm the approach is coherent
3. Execute one item at a time
4. Mark progress clearly
5. Verify thoroughly
6. Document result
7. Update `tasks/lessons.md` if there was any correction, drift, or repeated pattern

---

## 13. Priorities

Always optimize in this order:

1. correctness
2. clarity
3. minimal scope
4. maintainability
5. speed

Fast is valuable only if the result remains correct and understandable.

---

## 14. Anti-Patterns to Avoid

Do not:

- skip planning for multi-step work
- keep pushing after the plan is invalid
- guess framework behavior when Context7 can confirm it
- guess UI behavior when Playwright can verify it
- ship unverified fixes
- patch symptoms while missing root cause
- over-engineer obvious solutions
- mix unrelated edits in one change
- claim certainty without evidence
- leave behind brittle hacks without justification

---

## 15. Operating Motto

- Plan first
- Research before assuming
- Diagnose before editing
- Fix root causes
- Keep scope tight
- Verify before done
- Capture lessons
- Raise the quality bar every cycle

---

## 16. RBC Model and Calibration Rules

This repository includes ODE model work, calibration policies, benchmark manifests, and curve-based evaluation.

### When changing model equations or state mappings

- verify sign conventions on every edited flux contribution
- check for unintended new source/sink behavior
- verify conservation relationships for affected pools when applicable
- validate experimental mappings before trusting extreme outliers

### When changing calibration logic, scopes, or policies

- report the exact `target_scope`, `param_scope`, and `optimization_strategy`
- record the benchmark manifest and exact commands used for verification
- compare before/after results using benchmark artifacts, not only a single figure
- preserve protected monitor metrics and regression gating when adding new scopes

### Preferred calibration posture

- establish identifiability with the narrowest parameter scope that tests the hypothesis
- avoid opening broad compensator parameters before core mismatches are understood
- use targeted plots for diagnosis and benchmark manifests for promotion decisions

### Done criteria for model and calibration changes

- the change has direct evidence from reports, figures, or benchmark outputs
- the verification path is written down clearly enough to rerun
- residual risks or next-stage follow-ups are stated explicitly