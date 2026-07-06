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

**Milestones 1 and 2 are complete.** M1 delivered *estimation* (image → keypoints JSON); M2
delivered *scoring* (two poses → a normalization-aware similarity number). **No milestone is
currently active.** Milestone 3 is not yet scoped — the natural next link in the arc is
**coaching feedback** (turning a score/per-joint difference into human guidance), but scoping
it is a separate Product Owner decision and is deliberately *not* opened here.

---

## Milestone History

**M2 — Pose comparison (scoring vs. a reference) — shipped.** `pose_comparison.py`
(`compare_poses` → visibility-weighted mean normalized landmark distance: mid-hip root,
torso-length scale, 2-D; `IDENTITY_TOL = 1e-9`; `ValueError` guards; a thin CLI reusing
`estimate_pose`) + 7 invariance/structure tests. Scoped in PR #10, shipped via PR #12. A
smooth **"warm-harness"** milestone — a single clean Codex dispatch, no pivot, all criteria
green on first host verification, **no new template friction**. The central risk
(normalization) was de-risked exactly as intended, pinned by synthetic invariance tests. The
living-log pilot (see Open Decisions) worked.

**M1 — Single image → pose keypoints (JSON) — shipped.** `pose_estimation.py`
(`estimate_pose` → 33 landmarks `{name,x,y,z,visibility}` + argparse CLI) behind a Python
lint/test gate (`scripts/gate.py`, `pyproject.toml`). Shipped via PR #7 (gate) and PR #8
(product); retrospective in PR #9. Notable pivot: the installed `mediapipe==0.10.35` is a
**Tasks-API-only** build (no legacy `solutions` module), so M1 shipped on the MediaPipe
**Tasks API** against a committed `models/pose_landmarker_lite.task` model for offline
hermeticity. Full record: [`docs/handpass-ledger.md`](docs/handpass-ledger.md).

---

## Risks

- **Over-engineering (standing risk).** Each milestone brings a fresh instance of the pull to
  build speculative generality (M2's was joint-angle systems / Procrustes / weighting
  frameworks; a feedback milestone will bring its own). Mitigation: narrowest load-bearing
  slice; the friction gate governs any harness/template addition — ledger rows are
  observations, not build orders; promote only on recurrence (≥2 hand-passes) or measured cost.
- **Toolchain is venv-local, not on PATH (standing).** ruff/pytest/python resolve only inside
  `.venv/Scripts` (Windows layout). The gate and every verification step run with the venv
  active. Ties into the Mac→PC migration open decision.

---

## Open Decisions

- **Gate architecture — per-language copies vs a shared language-agnostic runner (OPEN
  DESIGN QUESTION, do not resolve).** The Portability Brief left open whether a future
  template ships per-language gate copies or a shared runner that calls per-language linters.
  Held open; hand-pass n=2 (a third language) is what would inform it.
- **Living-log convention — RESOLVED: adopt per-PR appends.** The M2 pilot worked. The Part B
  row was written the moment the dispatch completed, committed on the feature branch as a
  separate SE commit, folded into PR #12, and survived the squash to `main` — no retro-time
  reconstruction (contrast M1's six reconstructed rows). **Adopted as standing practice** for
  feature work, with a review-gate check that the row is present and correctly axised. Caveat:
  validated on one *low-friction* milestone; a high-friction milestone would test it harder,
  but the mechanism is low-cost and demonstrably fixes the M1 reconstruction problem.
- **Does the Windows codex sandbox permit direct venv-Python execution? (open probe).** In M2,
  Codex *claimed* it ran ruff/pytest in-sandbox ("7 passed") — but that is **unconfirmed** and
  could be inferred from the code, so per the "verify by executing" lesson it is not logged as
  fact. If true, the agent could self-verify and lighten the SE's host-verification burden,
  nuancing the standing edit-only-sandbox finding. Settle it *deliberately* on a future
  dispatch (e.g. have the agent write out a value obtainable only by executing, then check on
  the host) — never from self-report.
- **Role separation — settled, keep as-is.** Held again in M2 (author Codex / reviewer SE /
  merger PO) — now confirmed across two milestones of real product code; M1 additionally
  stress-tested it (a dispatch escalated a constraint conflict rather than violating scope).
  The only blur is mechanical (the Windows edit-only sandbox makes the SE do the agent's git —
  a machine artifact, not a role flaw). No change warranted.
- **Verify feasibility claims by executing them (process).** M1 orientation logged
  `mediapipe.solutions.pose` as feasible without running it, and it was false. Before a
  milestone depends on a library capability, exercise the **exact** API in the venv.
- **Reproducing the environment across machines (Mac→PC).** Pre-friction — observe and log
  toolchain drift in the migration log before deciding anything.
- **`new-issue.sh` omits the template's `## Dependencies` section.** Still **held** pending
  hand-pass n=2. Did **not** recur in M2 (single-issue milestone, no dependency edge), so the
  gap is milestone-shape-dependent — it bites only multi-issue milestones; evidence unchanged.
- **Estimator swap beyond MediaPipe** — deferred until a second estimator is actually needed.
  The seam is isolated behind one function; no plugin system exists and none is justified yet.

---

## Planning Rules

Keep this document concise: strategic direction, current priorities, engineering
recommendations, active risks, open questions. It is not a TODO list, changelog, or
implementation tracker — those belong in GitHub Issues, PRs, and commit history. Update it
only on a material change to objective, milestone, strategy, risk, or open decision.
