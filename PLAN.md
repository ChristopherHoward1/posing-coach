# Posing Coach — Engineering Operating Plan

## Project Vision

Build a **posing coach**: software that looks at a person in an image (later, video) and
helps them improve a pose. The long arc is capture → pose estimation → scoring against a
reference → actionable coaching feedback.

This repository plays a **second, deliberate role**: it is the **first hand-instantiation
of the `agentic-coding-template` engineering harness onto a Python project** (the template
was previously exercised only on bash projects). So every milestone builds the product
*and* stress-tests the ported harness. Portability observations are logged in
[`docs/handpass-ledger.md`](docs/handpass-ledger.md) — that ledger is the empirical spec
for a future Python-flavored template, not a mandate to change the template now.

This plan is jointly maintained by the Product Owner and the Staff Engineer.

---

## Current Objective

**Milestone 2 is active.** Turn two poses into a single, normalization-aware similarity
score. M1 delivered *estimation* (image → keypoints); M2 delivers the next load-bearing
link — *scoring vs. a reference* — because that is what turns a keypoint extractor into a
*coach*, and everything downstream (coaching feedback) depends on it. M2 deliberately
surfaces the hardest hidden risk of the whole product — **pose normalization** (making a
score invariant to body size and camera framing) — in the narrowest possible slice.

---

## Active Milestone

### Milestone 2 — Pose comparison (scoring vs. a reference)

**Why this, why now.** Scoring is the pivot from "we can see the pose" to "we can say how
close it is to a target." It is the direct dependency of coaching feedback, and its
correctness hinges entirely on normalization — the one piece of hard engineering hiding in
the product. Doing the *narrowest* scoring slice now de-risks normalization before any
feedback logic is built on top of a score we don't trust.

**The contract (concrete — normalization *is* the milestone).**
1. **Translation-invariant:** re-center every landmark on the **mid-hip** (mean of
   `LEFT_HIP`/`RIGHT_HIP`).
2. **Scale-invariant:** divide coordinates by a **torso length** (mid-hip → mid-shoulder
   distance).
3. **Score** = visibility-weighted mean Euclidean distance across the 33 landmarks, in
   **2-D (x, y)**. Lower = more similar; `0.0` = identical after normalization.
4. **Deliberately NOT normalized:** rotation (a lean is *signal*, not noise) and **z**
   (monocular depth from a single image is too noisy to score on). Named deferrals, not
   oversights.

**Shape.**
- **Core:** `compare_poses(pose_a, pose_b) -> float` operating on M1 keypoint lists (the
  `{name,x,y,z,visibility}` structure), applying the contract above.
- **CLI:** takes **two image paths**, runs M1's `estimate_pose` on each, prints the score.
  A "reference" is simply the second image path the caller supplies — there is **no** stored
  reference-pose library and **no** reference-loading mechanism (explicitly out of scope).

**Acceptance criteria** (thresholds fixed here, not discovered in test code; single named
constant `IDENTITY_TOL = 1e-9`):
- **Identity:** `compare_poses(p, p)` for a real fixture pose → `< IDENTITY_TOL`.
- **Translation-invariance:** a purely translated copy of a synthetic pose → `< IDENTITY_TOL`.
- **Scale-invariance:** a uniformly scaled copy of a synthetic pose → `< IDENTITY_TOL`.
- **Directional sanity:** a defined landmark perturbation **increases** the score
  (strictly `> IDENTITY_TOL`, and above a small floor for a visible perturbation).
- **End-to-end:** the fixture image scored **against itself** via `estimate_pose`
  → `< IDENTITY_TOL` (compares the computed pose to itself, so no inference-noise tolerance
  is needed — hence the tight bound rather than a loose `0.01`).
- **Degenerate input:** missing / near-zero-visibility hips or shoulders (→ ~zero torso
  length) has **defined, tested** behavior — raises `ValueError`, not a divide-by-zero.
- `python scripts/gate.py` green (`ruff` clean + `pytest`).

The translation/scale/identity criteria run on **synthetic constructed keypoints** (no model,
fast + hermetic); the end-to-end criterion exercises the real `estimate_pose` pipeline.

**Out of scope for M2** (later milestones — do not let these creep in): natural-language or
coaching feedback; any "good pose" pass/fail **judgment** or thresholds; rotation- or
3-D-invariance; multi-person; video; UI; stored reference-pose libraries / reference loading.

**Decomposition — one issue, one Codex dispatch.** Unlike M1 there is no harness half (the
gate exists). Footprint: new `pose_comparison.py` + `tests/test_pose_comparison.py`; it
*imports but does not modify* `pose_estimation.py`. Single, cleanly-scoped handoff — no
dependency edge to manage.

**Process improvement piloted in M2 (closes an M1 open decision).** The living-log broke
down in M1 (implementation friction was reconstructed at the retro). Fix: any ledger Part B
friction row is appended **on the feature branch and folded into the same PR**, and the M2
review checklist explicitly verifies *"Part B row present in the final diff and correctly
axised"* so a squash or review edit can't silently drop the finding.

**Definition of done for M2:** the issue merged via PR, the gate green on the new tests, and
any friction logged live in the ledger. Stop there — do not roll into feedback/judgment.

---

## Staff Engineer Recommendations

**One issue, not two.** M2 is a single cohesive product module with no harness plumbing;
splitting it would add ceremony without separation of concerns.

**Keep the metric a distance, and keep it to one metric.** A visibility-weighted mean
landmark distance is interpretable and directly testable. Resist joint-angle systems,
Procrustes alignment, or a weighting framework — those are feedback-milestone or
premature-generality work. Angles will earn their place when we translate a score into
"straighten your elbow," not before.

**Test the contract, not a photo.** The invariance guarantees are exact arithmetic, so they
belong in synthetic-keypoint unit tests with a near-epsilon tolerance; the real image is for
the end-to-end integration check only.

---

## Milestone History

**M1 — Single image → pose keypoints (JSON) — shipped.** `pose_estimation.py`
(`estimate_pose` → 33 landmarks `{name,x,y,z,visibility}` + argparse CLI) behind a Python
lint/test gate (`scripts/gate.py`, `pyproject.toml`). Shipped via PR #7 (gate) and PR #8
(product); retrospective in PR #9. Notable pivot: the installed `mediapipe==0.10.35` is a
**Tasks-API-only** build (no legacy `solutions` module), so M1 shipped on the MediaPipe
**Tasks API** against a committed `models/pose_landmarker_lite.task` model for offline
hermeticity. Full record: [`docs/handpass-ledger.md`](docs/handpass-ledger.md).

---

## Risks

- **Normalization robustness (M2's central risk).** The score is only as trustworthy as the
  torso-length scale and mid-hip root; occluded hips/shoulders make both unstable.
  Mitigation: visibility-weighting, the degenerate-input guard (raise on near-zero torso),
  and synthetic invariance tests that pin the exact contract.
- **Over-engineering (standing risk).** The pull to build angle systems / Procrustes /
  weighting frameworks is the current concrete instance. Mitigation: one metric, one
  normalization, tested; the friction gate governs any harness/template addition — ledger
  rows are observations, not build orders.
- **Toolchain is venv-local, not on PATH (standing).** ruff/pytest/python resolve only inside
  `.venv/Scripts` (Windows layout). The gate and every verification step run with the venv
  active. Ties into the Mac→PC migration open decision.

---

## Open Decisions

- **Gate architecture — per-language copies vs a shared language-agnostic runner (OPEN
  DESIGN QUESTION, do not resolve).** The Portability Brief left open whether a future
  template ships per-language gate copies or a shared runner that calls per-language linters.
  Held open; hand-pass n=2 (a third language) is what would inform it.
- **Living-log convention — being trialed in M2.** M1 showed it captured planning friction
  live but reconstructed implementation friction at the retro. M2 pilots the fix: per-PR
  Part B appends on the feature branch + a review gate that the row survives into the merge.
  Assess after M2 whether the pilot worked before treating it as settled.
- **Role separation survived the Python port — keep the model as-is.** M1 proved it on real
  product code (author Codex / reviewer SE / merger PO), including a stress test where the
  first dispatch escalated a constraint conflict instead of violating scope. The only blur is
  mechanical (the Windows edit-only sandbox makes the SE do the agent's git — a machine
  artifact, not a role flaw). No change warranted.
- **Verify feasibility claims by executing them (process).** M1 orientation logged
  `mediapipe.solutions.pose` as feasible without running it, and it was false. Before a
  milestone depends on a library capability, exercise the **exact** API in the venv.
- **Reproducing the environment across machines (Mac→PC).** Pre-friction — observe and log
  toolchain drift in the migration log before deciding anything.
- **`new-issue.sh` omits the template's `## Dependencies` section.** Recurred on Issue #3;
  still **held** pending hand-pass n=2. (M2 is a single issue, so no dependency edge is
  needed this milestone.)
- **Estimator swap beyond MediaPipe** — deferred until a second estimator is actually needed.
  The seam is isolated behind one function; no plugin system exists and none is justified yet.

---

## Planning Rules

Keep this document concise: strategic direction, current priorities, engineering
recommendations, active risks, open questions. It is not a TODO list, changelog, or
implementation tracker — those belong in GitHub Issues, PRs, and commit history. Update it
only on a material change to objective, milestone, strategy, risk, or open decision.
