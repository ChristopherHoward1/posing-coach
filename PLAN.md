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

**Milestone 1 is active.** Turn a single still image into structured pose keypoints. This
is the narrowest slice that produces something real, testable, and load-bearing for
everything later.

---

## Active Milestone

### Milestone 1 — Single image → pose keypoints (JSON)

**Why this, why now.** A posing coach cannot score a pose, compare it to a reference, or
give feedback until it can *reliably turn an image of a person into structured pose data*.
Keypoint extraction is the foundational dependency of the entire product; every later
capability sits on top of it. The narrowest slice that yields a real, verifiable artifact
is therefore **one image → keypoints JSON**. Doing this first de-risks the core dependency
(MediaPipe) and stands up the Python lint/test gate **before** any judgment logic exists to
be judged. It is also the vehicle for this repo's hand-pass role: M1 is where the inherited
bash gate gets recarved to Python and the portability friction gets logged.

**Shape.**
- **Input:** one still image file (path via CLI arg / config).
- **Process:** pose estimation via MediaPipe Pose / BlazePose — the *starting* estimator,
  isolated behind one function so it stays swappable (do not build a plugin system).
- **Output:** detected keypoints to JSON — per landmark: name, x, y, z, visibility.

**Acceptance.**
- Runs on the committed fixture `tests/fixtures/test_image.jpeg` and produces the JSON.
- A `pytest` test asserts the JSON structure (expected landmark count + fields) for that
  image.
- `ruff check` is clean and `pytest` is green.

**Out of scope for M1** (later milestones — do not let these creep in): video / multi-frame,
any pose scoring or judging, phone / iOS anything, any UI, model comparison.

**Decomposition** (live edges live on the issues, not here):
- **Issue A — gate recarve** (harness): port the bash lint/test gate to Python at
  functional parity — `pyproject.toml`, `scripts/gate.py` (runs `ruff check` + `pytest`),
  Python `.gitignore` entries. No product code.
- **Issue B — product slice** (M1 proper): image → keypoints JSON + the `pytest` structure
  test. **`Depends on` Issue A** — B needs A's pytest/ruff config to be gradable, and the
  two touch disjoint files. Serial, not parallel (interface dependency), so no
  disjointness race to manage.

**Definition of done for M1:** both issues merged via PR, the gate green on the product
test, and the portability ledger updated. Stop there — do not roll into scoring/video.

---

## Staff Engineer Recommendations

**Decompose M1 into the two serial issues above rather than one PR.** Reasoning: the gate
recarve is harness plumbing (config + orchestration) while the product slice is estimation
logic — different concerns, different footprints, independently reviewable. Splitting them
also exercises the `## Dependencies` convention on a real edge, which is part of what this
hand-pass is meant to test. Landing the gate first proves `ruff`/`pytest` actually run
green on this machine *before* product code depends on them. Alternative considered: a
single combined PR — simpler round-trip and it sidesteps the `pytest`-exit-5 empty-suite
edge, but it blurs harness vs product and skips the dependency-edge exercise. Tradeoff
accepted: one extra review cycle in exchange for cleaner scope and a real dependency-graph
test.

**Keep the gate recarve at functional parity, not enhancement.** Reproduce only the bash
gate's lint+test job. Do **not** re-port `review-context.sh`'s richer PR/issue/diff
gathering — that is not the gate's job, and it is not-yet-needed at M1.

---

## Risks

- **Toolchain is venv-local, not on PATH.** ruff/pytest/python resolve only inside
  `.venv/Scripts` (Windows layout). The gate and every verification step must run with the
  venv active. Mitigation: state it as a key constraint in the handoff; the reviewer
  verifies with the venv active. Ties into the Mac→PC migration open decision.
- **MediaPipe hermeticity.** The Tasks API needs a downloaded `.task` model (network). The
  legacy `mediapipe.solutions.pose` API bundles its model. Mitigation: constrain Issue B to
  the legacy API so M1 runs offline and deterministically.
- **Empty-suite bootstrap.** `pytest` exits 5 with no tests collected, which would fail the
  gate on the gate-only PR. Mitigation: `gate.py` treats exit 5 as non-failing; the product
  test then makes it pass for the right reason.
- **Over-engineering (standing risk).** Swappable estimator, gate features, config systems
  invite gold-plating. Mitigation: M1 isolates the estimator behind one function and no
  more; gate features stay at parity. The friction gate governs any harness addition —
  ledger rows are observations, not build orders.

---

## Open Decisions

- **Reproducing the environment across machines (Mac→PC).** Python is venv-local here; a
  future machine may differ. Pre-friction — observe and log toolchain drift in the ledger
  before deciding anything. No environment-reproduction work is justified yet.
- **`new-issue.sh` renderer omits the template's `## Dependencies` section** (inherited from
  the donor). If it bites while creating the M1 issues, record dependencies on the issue
  body manually and log the recurrence; the narrow fix (render the section) is not yet
  justified.
- **Estimator swap beyond MediaPipe** — deferred until a second estimator is actually
  needed (e.g., for the later scoring milestone). M1 only isolates the seam.

---

## Planning Rules

Keep this document concise: strategic direction, current priorities, engineering
recommendations, active risks, open questions. It is not a TODO list, changelog, or
implementation tracker — those belong in GitHub Issues, PRs, and commit history. Update it
only on a material change to objective, milestone, strategy, risk, or open decision.
