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

**Milestone 3 is active.** Turn a pose comparison into **per-joint directional feedback** —
the top-K most-divergent joints, each with the move the user should make to match the
reference. M1 delivered *estimation*, M2 *scoring*; M3 delivers the first **actionable
feedback**, the pivot from "how close" (a scalar) to "what to change" (localized,
directional). It stays deterministic (template cues, no LLM) and reuses M2's normalization so
feedback and score agree by construction.

---

## Active Milestone

### Milestone 3 — Per-joint directional feedback

**Why this, why now.** M2 collapses two poses into a single score; that tells a user *how
far off* they are but not *what to do*. Feedback is the payoff of the whole arc, and the
narrowest load-bearing slice is per-joint direction: which joints diverge most and which way
to move them. Doing it deterministically now — before any natural-language or "good pose"
judgment layer — keeps it testable and gives any later coaching UI/LLM an honest substrate to
consume.

**The contract (concrete).**
1. **Shared normalization.** Reuse M2's normalization (mid-hip root, torso-length scale,
   2-D) so feedback and score agree by construction. The one refactor: expose
   `pose_comparison._normalize_pose` as public `normalize_pose`; `compare_poses` calls the
   public name.
2. **Displacement.** Per landmark, `(dx, dy) = reference_norm − user_norm` — the move the
   **user** makes to reach the reference. `magnitude = hypot(dx, dy)`.
3. **Ranking.** Sort by magnitude descending; return only genuinely-divergent joints
   (`magnitude ≥ IDENTITY_TOL`, reused from M2), capped at `top_k` (default 3).
4. **Direction cue (deterministic, image-frame).** Image convention x→right, y→**down**:
   `dy < 0` → "up", `dy > 0` → "down"; `dx < 0` → "left", `dx > 0` → "right". Name an axis
   only if `|component| ≥ DIRECTION_MIN_FRACTION × magnitude` (named constant `0.2`) so a
   near-pure-horizontal move reads "right", not "right and barely up". Words ordered
   vertical-then-horizontal ("up and right"). Template strings — **no LLM**.
5. **Output.** `pose_feedback(user_pose, reference_pose, top_k=3) -> list[dict]` of
   `{name, dx, dy, magnitude, direction}`. Thin CLI (`--image-a` user, `--image-b`
   reference) runs `estimate_pose` on each and prints lines like
   `LEFT_WRIST: move up and right (off by 0.42)`.
6. **Degenerate input** inherits M2's `ValueError` (missing hips/shoulders, ~zero torso) via
   the shared `normalize_pose`.

**Acceptance criteria.**
- **Refactor safety:** all existing M2 tests still pass (the rename is mechanical;
  `compare_poses` behavior unchanged).
- **Identity:** `pose_feedback(p, p)` → `[]` (nothing ≥ `IDENTITY_TOL`).
- **Localization:** a synthetic pose with one landmark perturbed → that landmark is the
  top-ranked entry.
- **Direction correctness:** a reference landmark purely above the user's → cue exactly
  `"up"`; purely to image-right → `"right"`; a 45° case → both axes named in the fixed order.
- **Top-K cap:** with more than K divergent joints, exactly the K largest (by magnitude) are
  returned.
- **Degenerate:** missing anchors / zero torso → `ValueError`.
- `python scripts/gate.py` green (`ruff` clean + `pytest`, all test files).

**Out of scope for M3** (later milestones — do not let these creep in): LLM / natural-language
fluency beyond fixed templates; body-part grouping ("raise your left arm"); anatomical /
mirrored left-right; any "good pose" pass/fail **judgment** or thresholds; multi-person;
video; UI.

**Decomposition — one issue, one Codex dispatch.** Footprint: `pose_comparison.py`
(mechanical `_normalize_pose → normalize_pose` refactor) + new `pose_feedback.py` +
`tests/test_pose_feedback.py`; imports but does not modify `pose_estimation.py`. The refactor
and the new module are one cohesive change (the refactor exists to serve feedback), so
splitting would be artificial — no dependency edge.

**Definition of done for M3:** the issue merged via PR, the gate green on the new tests (and
M2's still green), and any friction logged live in the ledger. Stop there — do not roll into
judgment / natural-language cues.

---

## Staff Engineer Recommendations

**Keep the refactor mechanical.** `_normalize_pose → normalize_pose` is a pure rename +
visibility change to create a single source of truth for the normalization contract now that
there are two consumers. Resist widening it (no options, no new return shape) — the gate runs
M2's tests, so a regression fails loudly.

**Deterministic cues only.** Template strings and a single fraction constant. The pull to an
LLM cue-generator or a body-part taxonomy is a later-milestone concern; this milestone must
stay deterministically testable.

---

## Milestone History

**M2 — Pose comparison (scoring vs. a reference) — shipped.** `pose_comparison.py`
(`compare_poses` → visibility-weighted mean normalized landmark distance: mid-hip root,
torso-length scale, 2-D; `IDENTITY_TOL = 1e-9`; `ValueError` guards; a thin CLI reusing
`estimate_pose`) + 7 invariance/structure tests. Scoped in PR #10, shipped via PR #12. A
smooth **"warm-harness"** milestone — a single clean Codex dispatch, no pivot, no new template
friction; the living-log pilot worked. Full record: ledger.

**M1 — Single image → pose keypoints (JSON) — shipped.** `pose_estimation.py`
(`estimate_pose` → 33 landmarks `{name,x,y,z,visibility}` + argparse CLI) behind a Python
lint/test gate (`scripts/gate.py`, `pyproject.toml`). Shipped via PR #7 (gate) and PR #8
(product); retrospective in PR #9. Notable pivot: the installed `mediapipe==0.10.35` is a
**Tasks-API-only** build (no legacy `solutions` module), so M1 shipped on the MediaPipe
**Tasks API** against a committed `models/pose_landmarker_lite.task` model for offline
hermeticity. Full record: [`docs/handpass-ledger.md`](docs/handpass-ledger.md).

---

## Risks

- **M3 refactor touches M2's shipped file.** Renaming `_normalize_pose → normalize_pose` in
  `pose_comparison.py` risks regressing scoring. Mitigation: the rename is mechanical and the
  gate runs M2's tests, so any behavioral change fails loudly.
- **Direction-cue thresholds.** The `DIRECTION_MIN_FRACTION` constant could yield awkward cues.
  Mitigation: one named constant, tested on pure-axis and diagonal cases; no config surface.
- **Over-engineering (standing risk).** Each milestone brings a fresh instance (M3's is the
  pull to LLM phrasing / body-part taxonomy / anatomical mirroring). Mitigation: narrowest
  load-bearing slice; the friction gate governs any harness/template addition — ledger rows
  are observations, not build orders; promote only on recurrence (≥2 hand-passes) or measured
  cost.
- **Toolchain is venv-local, not on PATH (standing).** ruff/pytest/python resolve only inside
  `.venv/Scripts` (Windows layout). The gate and every verification step run with the venv
  active. Ties into the Mac→PC migration open decision.

---

## Open Decisions

- **Gate architecture — per-language copies vs a shared language-agnostic runner (OPEN
  DESIGN QUESTION, do not resolve).** The Portability Brief left open whether a future
  template ships per-language gate copies or a shared runner that calls per-language linters.
  Held open; hand-pass n=2 (a third language) is what would inform it.
- **Does the Windows codex sandbox permit direct venv-Python execution? (open probe).** In M2,
  Codex *claimed* it ran ruff/pytest in-sandbox ("7 passed") — unconfirmed, not logged as
  fact (per the "verify by executing" lesson). If true, the agent could self-verify and
  lighten the SE's host-verification burden. Settle it *deliberately* on a future dispatch
  (have the agent write out a value obtainable only by executing, then check on the host) —
  never from self-report. (Kept out of the M3 handoff to keep it clean.)
- **Merge execution — SE runs `gh pr merge`.** The PO's GitHub UI squash-merges repeatedly
  failed to land (#7, #12, #13 each reported merged but stayed OPEN). Standing arrangement:
  on the PO's "merge X" instruction, the SE executes `gh pr merge X --squash --delete-branch`
  after review. The PO's instruction is the merge authority; only the mechanical step moved.
- **Role separation — settled, keep as-is.** Confirmed across two milestones of real product
  code (author Codex / reviewer SE / merger-executed-by-SE / decision PO); M1 additionally
  stress-tested it. The only blur is mechanical (Windows edit-only sandbox → SE does the
  agent's git). No change warranted.
- **Verify feasibility claims by executing them (process).** M1 orientation logged
  `mediapipe.solutions.pose` as feasible without running it, and it was false. Before a
  milestone depends on a library capability, exercise the **exact** API in the venv.
- **Living-log convention — adopted.** Per-PR Part B appends on the feature branch + a
  review-gate check that the row survives the merge. Validated in M2; standing practice.
- **Reproducing the environment across machines (Mac→PC).** Pre-friction — observe and log
  toolchain drift in the migration log before deciding anything.
- **`new-issue.sh` omits the template's `## Dependencies` section.** Still **held** pending
  hand-pass n=2. Won't recur in M3 (single-issue milestone, no dependency edge); the gap is
  milestone-shape-dependent.
- **Estimator swap beyond MediaPipe** — deferred until a second estimator is actually needed.
  The seam is isolated behind one function; no plugin system exists and none is justified yet.

---

## Planning Rules

Keep this document concise: strategic direction, current priorities, engineering
recommendations, active risks, open questions. It is not a TODO list, changelog, or
implementation tracker — those belong in GitHub Issues, PRs, and commit history. Update it
only on a material change to objective, milestone, strategy, risk, or open decision.
