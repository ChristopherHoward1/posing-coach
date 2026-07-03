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

**Milestone 1 is complete** (shipped via PR #7 — the Python gate — and PR #8 — the product
slice; gate green on `main`). **No milestone is currently active.** Milestone 2 is not yet
scoped; scoping it is a separate Product Owner decision and is deliberately *not* opened
here. This plan currently holds the **M1 retrospective** and the open decisions it surfaced.

---

## Milestone 1 — Single image → pose keypoints (JSON) — ✅ SHIPPED

**Why it existed (kept for cold-read).** A posing coach cannot score a pose, compare it to a
reference, or give feedback until it can *reliably turn an image of a person into structured
pose data*. Keypoint extraction is the foundational dependency of the entire product; every
later capability sits on top of it. The narrowest slice that yields a real, verifiable
artifact is therefore **one image → keypoints JSON**. Doing it first de-risked the core
dependency (MediaPipe) and stood up the Python lint/test gate **before** any judgment logic
existed to be judged. M1 was also the vehicle for this repo's hand-pass role: it is where the
inherited bash gate was recarved to Python and the first portability friction was logged.

**What shipped.**
- **Gate (Issue #2 / PR #7).** `scripts/gate.py` runs `ruff check` + `pytest` through the
  venv; `pyproject.toml` (ruff + pytest config); Python `.gitignore` entries. Empty-suite
  `pytest` exit 5 is treated as pass. Functional parity with the bash gate — no enhancement.
- **Product (Issue #3 / PR #8).** `pose_estimation.py`: `estimate_pose()` returns the first
  detected pose's **33 landmarks** `{name, x, y, z, visibility}`, plus a thin argparse CLI
  (`--image`, `--output`). `tests/test_pose_estimation.py` asserts the structure. Gate green
  on `main` with the product test passing.
- **Approach change from the original plan.** M1 was specified around the legacy
  `mediapipe.solutions.pose` API. The installed `mediapipe==0.10.35` proved to be a
  **Tasks-API-only** build (no `solutions` module at all), so the slice shipped on the
  MediaPipe **Tasks API** (`PoseLandmarker`) against a **committed** model asset
  (`models/pose_landmarker_lite.task`, ~5.8 MB, like the fixture image) for offline
  hermeticity. No dependency change; milestone shape and acceptance criteria unchanged. See
  ledger "M1 / product orient" and "M1 / product pivot".

### Retrospective

**Per-artifact verdicts** (inherited scaffolding; detail in ledger Part A). The clean ports
matter as much as the frictions — they are the evidence for what a template keeps untouched:
- **Clean-verbatim:** `AGENTS.md`, `.github/ISSUE_TEMPLATE/implementation.md`,
  `.github/PULL_REQUEST_TEMPLATE.md`. `new-issue.sh` also *ran* unmodified (but see its gap).
  These are language-agnostic operating docs/contracts — they travel.
- **Adapted:** `CLAUDE.md` (Review gate de-bashed to a command/role, not a script path);
  `new-handoff.sh` + `trigger-agent.sh` (portable repo-root check, PR #6 — since dogfooded
  clean on Windows during M1).
- **Discarded+replaced:** the bash gate (`lint.sh` / test-harness / `review-context.sh`
  orchestration) → `scripts/gate.py` + `pyproject.toml`; the `PLAN.md` "skeleton" that was
  actually the donor's Milestone 1–12 history → this product plan.
- **Not-yet-exercised:** none outstanding for M1.

**Held hypotheses (n=1 — recorded, NOT acted on).** This is hand-pass **n=1**, so *by
construction* almost nothing meets the friction-justification bar (recurrence across ≥2
hand-passes, OR a measured non-trivial cost). Each of these is evidence awaiting a second
hand-pass to confirm recurrence — none is promoted to a template spec or build item:
- Operating docs should name the review gate by command/role, not a hard-coded script path
  (the `CLAUDE.md` → `review-context.sh` dangling reference).
- A template should ship `PLAN.md` as a blank skeleton, not donor history.
- Template scripts should use a portable repo-root check. Already fixed in this instance
  (PR #6) with a strictly-better fix that blocked Windows work until landed — a strong
  candidate, but still one hand-pass.
- `pyproject.toml` / Python `.gitignore` / the very shape of the gate — these feed the gate
  **open design question** below rather than a standalone change.

**Closest to earning a change (still held):** `new-issue.sh` renders no `## Dependencies`
section, so `Depends on #2` had to be added to Issue #3 by hand. It has independent evidence
in two contexts (the donor's own Milestone-12 note + this hand-pass). It is the first thing to
confirm on hand-pass n=2 — but it stays a **hypothesis**, not a build item.

**Named-but-held temptations (this system's Imagine→Automate failure mode).** Explicitly
*not* acting on these tidy piles of n=1 annoyances:
- "Fork a Python-flavored template now" from the pyproject / Python-`.gitignore` / `gate.py`
  observations. n=1. **Held.**
- "Adopt the portable repo-root check into the template." Low-risk and correct, but n=1, and
  already fixed in this instance — no urgency. **Held.**
- "Switch codex to `danger-full-access` so the agent does its own git," to erase the
  edit-only-sandbox friction. n=1 machine finding that trades away sandbox safety. **Held**
  (and routed to the migration log, below).

**Routed elsewhere — NOT template evidence.** Machine / shell-env findings belong in the
PC-migration observe log, not this template ledger, because they say nothing about a generic
template: venv-local toolchain (`.venv/Scripts`), codex auth (401 → `codex login`), the
Windows **edit-only sandbox** (the agent cannot commit/push/run bash/reach network — the SE
does all git for it), CRLF checkout. They shaped *how* M1 was executed but earn no template
case.

**What went right (worth keeping).** Role separation survived the port to real product code
(see Open Decisions). The gate recarve executed with zero new friction beyond what was logged
at plan time. "Artifacts over memory" paid off concretely: PR #7 was reported merged but was
still open — the GitHub state, not the recollection, drove the next step.

---

## Open Decisions

- **Gate architecture — per-language copies vs a shared language-agnostic runner (OPEN
  DESIGN QUESTION, do not resolve).** The bash gate read as discarded+replaced with an
  obvious "the gate must be per-language" reading. The Portability Brief deliberately left
  open whether a future template ships **per-language gate copies** or a **shared
  language-agnostic runner** that calls per-language linters (`ruff`, `shellcheck`, …). This
  is held as an open design question, **not** a decision; hand-pass n=2 (a third language)
  is what would inform it.
- **Did the living-ledger convention actually work? Partially — strengthen before M2.**
  Planning-phase friction (orientation → decomposition) *was* captured live. But the
  implementation-phase events (gate landing, the mediapipe falsification, the dispatch-#1
  revert, the Tasks-API pivot) were **reconstructed at the retrospective**, not logged the
  moment they occurred — because the ledger lives on protected `main` while implementation
  happens on feature branches, making mid-branch appends awkward. Candidate fix (hypothesis,
  not mandate): let each feature PR carry its own Part B append, or keep a scratch event log
  during implementation that folds into the ledger at PR time. Decide before M2.
- **Role separation survived the Python port — keep the model as-is.** Codex implemented real
  **product** code (not just harness plumbing); author (Codex) / reviewer (SE) / merger (PO)
  held throughout; and the boundary passed a *stress test* — the first product dispatch hit a
  constraint conflict (forbidden Tasks API) and **escalated it back to the SE instead of
  violating scope or fabricating**. The only blur is mechanical: the Windows edit-only
  sandbox forces the SE to do the agent's commit/push/PR — a machine artifact (migration
  log), not a flaw in the role model. No change to the role model is warranted.
- **Verify feasibility claims by executing them (process).** Orientation logged
  `mediapipe.solutions.pose` as feasible without ever running it; it was false and survived
  to implementation. Before a future milestone depends on a library capability, exercise the
  **exact** API in the venv — not just the top-level `import`.
- **Reproducing the environment across machines (Mac→PC).** Python is venv-local here; a
  future machine may differ. Pre-friction — observe and log toolchain drift in the migration
  log before deciding anything. No environment-reproduction work is justified yet.
- **`new-issue.sh` omits the template's `## Dependencies` section.** Recurred on Issue #3
  (edge added by hand). Still **held** pending hand-pass n=2; the narrow fix (render the
  section + a `--depends-on` flag) is not yet justified.
- **Estimator swap beyond MediaPipe** — deferred until a second estimator is actually needed
  (e.g. for a later scoring milestone). M1 shipped on the Tasks-API `PoseLandmarker` behind a
  single-function seam; the seam is isolated, but no plugin system exists and none is
  justified yet.

---

## Risks

- **Over-engineering (standing risk).** The pull to convert M1's pile of n=1 template
  observations into a "Python template" fork is the current concrete instance. Mitigation:
  the friction gate governs every harness/template addition — ledger rows are observations,
  not build orders; promote only on recurrence (≥2 hand-passes) or measured cost.
- **Toolchain is venv-local, not on PATH (standing).** ruff/pytest/python resolve only inside
  `.venv/Scripts` (Windows layout). The gate and every verification step must run with the
  venv active. Ties into the Mac→PC migration open decision.
- **MediaPipe hermeticity — RESOLVED for M1.** Shipped on the Tasks API against a committed
  `.task` model, so inference is offline and deterministic with no test-time network. Kept as
  a note because a future model/tier change would revisit the committed-asset choice.
- **Empty-suite bootstrap — RESOLVED.** `gate.py` treats `pytest` exit 5 as non-failing; the
  M1 product test now makes the suite pass for the right reason.

---

## Planning Rules

Keep this document concise: strategic direction, current priorities, engineering
recommendations, active risks, open questions. It is not a TODO list, changelog, or
implementation tracker — those belong in GitHub Issues, PRs, and commit history. Update it
only on a material change to objective, milestone, strategy, risk, or open decision.
