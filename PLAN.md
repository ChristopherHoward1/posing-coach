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

**Milestones 1–4 are complete.** M1 delivered *estimation* (image → keypoints JSON), M2
*scoring* (a normalization-aware similarity number), M3 the arc's first *actionable* feedback
(per-joint directional cues), and M4 the arc's first *anatomical* feedback (interior joint
angles vs. a reference pose). **No milestone is currently active.** The remaining arc links —
a "good pose" judgment layer, natural-language coaching, or the **orientation-angles**
milestone M4 scoped a home for (torso lean + shoulder/hip leveling, where the image-frame
directional machinery would have ≥2 consumers) — each stay unopened pending a separate Product
Owner decision.

---

## Milestone History

**M4 — Interior joint-angle feedback — shipped.** The arc's first *anatomical* feedback —
angle, not position (a bent vs. straight elbow is signal M3's displacement view structurally
can't express). `pose_angles.py` (`joint_angles` → 8 vertex-named interior angles, bilateral
elbow/knee/shoulder-abduction/hip, magnitudes in [0,180] via `atan2(abs(cross),dot)`;
`angle_feedback` → reference-relative open/close sorted by |delta|; thin CLI; **no LLM**).
Interior-only slice: all orientation angles deferred, so **no `normalize_pose` call** (interior
angles are normalization-invariant) and no directional/image-frame cues. New files only —
nothing shipped was touched (cleaner than M3's refactor). Clean single Codex dispatch; gate
green (22 passed = prior 14 + M4's 8). Scoped in PR #19, shipped via PR #21; issue #20
auto-closed. Full record: ledger.

**M3 — Per-joint directional feedback — shipped.** The arc's first *actionable* feedback — the
pivot from "how close" (a scalar) to "what to change" (localized, directional).
`pose_feedback.py` (`pose_feedback` → top-K most-divergent joints, each with a magnitude and an
image-frame direction cue; deterministic template strings, **no LLM**) reusing M2's
normalization, now exposed as the public `normalize_pose` — feedback is its real second
consumer. The mechanical `_normalize_pose → normalize_pose` refactor landed on `main` with M2's
scoring tests still green. Shipped via PR #16; issue #15 auto-closed. Full record: ledger.

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

- **Over-engineering (standing risk).** Each milestone brings a fresh instance (M3's was the
  pull to LLM phrasing / body-part taxonomy / anatomical mirroring; M4's was the pull to bundle
  orientation angles + image-frame framing machinery in early — resolved at scoping by shipping
  interior angles only and deferring all orientation angles to a milestone where that machinery
  has ≥2 consumers; the next milestone will bring its own). Mitigation: narrowest load-bearing
  slice; the friction gate governs any harness/template addition — ledger rows are observations,
  not build orders; promote only on recurrence (≥2 hand-passes) or measured cost.
- **Toolchain is venv-local, not on PATH (standing).** ruff/pytest/python resolve only inside
  `.venv/Scripts` (Windows layout). The gate and every verification step run with the venv
  active. Ties into the Mac→PC migration open decision.

---

## Open Decisions

- **Gate architecture — per-language copies vs a shared language-agnostic runner (OPEN
  DESIGN QUESTION, do not resolve).** The Portability Brief left open whether a future
  template ships per-language gate copies or a shared runner that calls per-language linters.
  Held open; hand-pass n=2 (a third language) is what would inform it.
- **Sandbox venv-Python execution — ACCEPTED CONSTRAINT, mitigated (was: open probe).** The
  open question: does the Windows codex sandbox permit direct venv-Python execution? In M2,
  Codex *claimed* it ran ruff/pytest in-sandbox ("7 passed") — unconfirmed and not logged as
  fact (per the "verify by executing" lesson). **Friction-justification test:** across M1–M3,
  Codex's unreliable execution self-reporting has cost nothing concrete — host-side
  verification has caught or compensated every instance, and no bad merge, wasted cycle, or
  undetected failure has reached `main` because of it. The SE verifies on the host regardless,
  so the sandbox's self-report reliability sits on **no critical path**. Reframed from open
  probe to accepted constraint: the deliberate probe (have the agent write out a value
  obtainable only by executing, then check on the host) stays **OPTIONAL** — run it only if it
  ever becomes cheap to settle in passing, never as motivated work. Unresolved is not the same
  as unjustified.
- **Merge execution — RESOLVED (SE runs `gh pr merge`).** *Root cause:* the PO's GitHub UI
  squash-merges reported the PR as merged but left it OPEN — #7, #12, #13, three occurrences.
  *Fix:* on the PO's "merge X" instruction, the SE executes `gh pr merge X --squash
  --delete-branch` after review, then verifies the outcome against GitHub state; the PO retains
  merge authority (their instruction is the trigger), only the mechanical step moved.
  *Evidence:* n=3 clean CLI merges since the switch, including #16, where the reported outcome
  and GitHub state agreed. The reported-merged-but-still-OPEN gap has not recurred. Kept here as
  a **closed record**, not an open watch-item, so it is not re-litigated from memory next
  session.
- **Role separation — settled, keep as-is.** Confirmed across three milestones of real product
  code (author Codex / reviewer SE / merger-executed-by-SE / decision PO); M1 additionally
  stress-tested it. The only blur is mechanical (Windows edit-only sandbox → SE does the
  agent's git). No change warranted.
- **PR-filing role — RESOLVED (Option A: CLAUDE.md reworded to match practice).** *Conflict:*
  CLAUDE.md said "the filer is the Product Owner, not the Staff Engineer," yet every
  implementation PR (#8/#12/#16/#19/#21) was SE-filed under the PO's single `ChristopherHoward1`
  account — the "PO files" line was a donor/Mac **two-actor assumption** (agent pushes its own
  branch; a separate human files) that doesn't fit a one-account setup where the Windows sandbox
  is edit-only and the SE already does *all* mechanical git under that account. *Resolution (PO
  decision):* the CLAUDE.md Implementation Handoff paragraph now states the SE performs the
  mechanical git (commit attributed to the agent / push / file PR / execute merge on the PO's
  instruction), with author/reviewer separation resting on **commit attribution + PO merge
  authority**, not on who runs `gh`. Reworded in this retro PR (#22). Kept as a closed record so
  it is not re-litigated from memory. Logged in the ledger as a template-design-flaw edge.
- **Verify feasibility claims by executing them (process).** M1 orientation logged
  `mediapipe.solutions.pose` as feasible without running it, and it was false. Before a
  milestone depends on a library capability, exercise the **exact** API in the venv.
- **Living-log convention — adopted; proven for low-friction, honestly untested under load
  (n=3).** Per-PR Part B append on the feature branch + a review-gate check that the row
  survives the merge. Held across M2, M3, and M4 (n=3) — but all three were low-friction
  implementations, so the mechanism is well-established for the easy case and has still never
  been *stressed* by messy, high-friction implementation. Reframed at the M4 retro: after three
  clean holds, the "waiting for the first high-friction milestone" framing is strained — a warm
  harness may simply keep producing low-friction milestones, so the load-test may never arrive
  as a discrete event. Treat this as a **standing known-limitation** (proven-for-low-friction,
  untested-under-load), not an active watch-item awaiting an imminent test.
- **Reproducing the environment across machines (Mac→PC).** Pre-friction — observe and log
  toolchain drift in the migration log before deciding anything.
- **`new-issue.sh` omits the template's `## Dependencies` section.** Still **held** pending
  hand-pass n=2. Did **not** recur in M3 (single-issue milestone, no dependency edge); the gap
  is milestone-shape-dependent.
- **Estimator swap beyond MediaPipe** — deferred until a second estimator is actually needed.
  The seam is isolated behind one function; no plugin system exists and none is justified yet.

---

## Planning Rules

Keep this document concise: strategic direction, current priorities, engineering
recommendations, active risks, open questions. It is not a TODO list, changelog, or
implementation tracker — those belong in GitHub Issues, PRs, and commit history. Update it
only on a material change to objective, milestone, strategy, risk, or open decision.
