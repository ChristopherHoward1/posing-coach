# Hand-pass Portability Ledger

This repository is the **first hand-instantiation of `agentic-coding-template` onto a
non-bash (Python) project**. This ledger is the empirical record of how the ported
harness meets a Python project: where it fights, and — just as important — where it
ports cleanly.

**What this ledger is and is not.** It records **observations and hypotheses**, not a
mandate to change the template. One hand-pass can show that something is coupled *in this
instance*; it cannot distinguish "coupled in general" from "coupled to Python
specifically" — that needs a second hand-pass to confirm recurrence. Template changes stay
friction-justified (recurrence across hand-passes, `n >= 2`, or measured cost), exactly
like any other earned automation. A row here is evidence, not a spec. The
`template hypothesis` column holds hypotheses, never requirements.

**Axis vocabulary** (why did the artifact fight?):

- `bash-coupling` — needs a per-language rewrite. Expected, routine porting cost.
- `template-design-flaw` — an assumption wrong even for a generic project (e.g. an
  operating doc naming a specific implementation artifact). More valuable to catch: it
  would bite any project, not just Python.
- `machine` — the host lacks something (tool absent, wrong version).
- `shell-env` — environment/layout mismatch (PATH, venv layout, quoting).
- `other` — anything else (note it inline).

Keep `bash-coupling` and `template-design-flaw` distinct: the first is expected porting
cost; the second is a latent template bug.

---

## Part A — Artifact inventory (the denominator)

One row per inherited scaffolding artifact. Clean ports are logged too: an artifact that
needed zero changes is the strongest evidence it belongs in a future template verbatim.

| inherited artifact | verdict | if not clean: what fought + axis | cost & recurrence | template hypothesis (NOT spec) |
| --- | --- | --- | --- | --- |
| `CLAUDE.md` | adapted | Review section hard-references `scripts/review-context.sh` (a bash gate helper that was not ported) → dangling pointer; gate prose is in bash terms. Axis: bash-coupling, with a `template-design-flaw` edge (an operating doc naming a specific script path inherits a dangling reference on any partial port). | one-time, cheap (doc edit in the planning PR) | An operating doc might describe the review gate by *command/role* ("run the repo's lint + test gate") rather than a hard-coded script path, so a port cannot inherit a dangling reference. Hypothesis, n=1. |
| `AGENTS.md` | clean-verbatim | — | none | Language-agnostic role/contract ("tests, lint, typecheck, build" phrased generically). Strong candidate for verbatim template inclusion. |
| `.github/ISSUE_TEMPLATE/implementation.md` | clean-verbatim | — | none | Language-agnostic; already carries `## Dependencies`. Verbatim candidate. Watch: `new-issue.sh` may not render `## Dependencies` (inherited divergence) — confirm when exercised. |
| `.github/PULL_REQUEST_TEMPLATE.md` | clean-verbatim | — | none | Language-agnostic. Verbatim candidate. |
| `scripts/new-issue.sh` | not-yet-exercised | (pending: will run to create M1 issues) | — | Bash + `gh`. Watch: known inherited omission of `## Dependencies` in `render_body`. |
| `scripts/new-handoff.sh` | not-yet-exercised | (pending: will run to create the gate branch) | — | Bash + `gh` + `git`. Watch: `[[ -d .git ]]` repo-root check (worktree-incompatible; not triggered in a full clone). |
| `scripts/trigger-agent.sh` | not-yet-exercised | (pending: may run to dispatch Codex) | — | Bash + `codex`. Same `[[ -d .git ]]` note; rejects a dirty tree (see `.gitignore` row). |
| `PLAN.md` ("skeleton") | discarded+replaced | It was **not** a skeleton — it carried the donor's entire Milestone 1–12 history (all about the harness itself), so a fresh reader would learn nothing about *this* product. Rewritten to posing-coach M1. Axis: `template-design-flaw` (instantiation did not skeletonize PLAN). | one-time, moderate (full rewrite in the planning PR) | A template should ship `PLAN.md` as a blank skeleton (product vision + empty milestone slots), not the donor's history. Hypothesis, n=1. Pairs with the `CLAUDE.md`/`AGENTS.md` clean ports: agnostic operating docs travel; product-specific `PLAN.md` does not. |
| gate — lint: shellcheck → `ruff check` | discarded+replaced (planned, Issue A) | The bash gate lints via a `lint.sh` that globs `scripts/*.sh`; Python replaces it with `ruff check`, which does its own discovery — **no custom script needed**. Axis: bash-coupling. | one-time | `lint.sh` may be bash-ecosystem scaffolding (bash has no native linter/runner), not a universal template need. Hypothesis, n=1. |
| gate — tests: bash harness → `pytest` | discarded+replaced (planned, Issue A) | Bash needs a hand-rolled test runner + discovery loop; `pytest` does discovery natively. Axis: bash-coupling. | one-time | Same as above: the template's test-runner scaffolding may be a bash workaround, not a universal need. Hypothesis, n=1. |
| gate — orchestration: `review-context.sh` lint+test run → `scripts/gate.py` | adapted+replaced (planned, Issue A) | The bash gate bundled lint+test into one read-only pass; the Python equivalent (`scripts/gate.py`) is ~15 lines calling `ruff`/`pytest` because the ecosystem already provides discovery/runners. `review-context.sh`'s **richer** gathering (PR metadata, linked issue, diff) is deliberately **not** ported — that is not the lint+test job. Axis: bash-coupling. | one-time | The orchestration script may be near-vacuous in a real language ecosystem (`ruff && pytest` is nearly as good). Whether a wrapper earns its place is itself the hypothesis; needs a 2nd hand-pass. n=1. |
| gate — `pyproject.toml` | new (planned, Issue A) | No bash analog; Python needs its own project/config file (ruff + pytest config). Axis: bash-coupling. | one-time | Every Python port needs a `pyproject.toml`; a Python-flavored template would ship a minimal one. Hypothesis, n=1. |
| `.gitignore` | adapted (planned, Issue A) | Inherited `.gitignore` ignores only `.venv/`. Python runs create `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, which dirty the tree — and `new-handoff.sh`/`trigger-agent.sh` **reject a dirty tree**. So the Python gate couples to the workflow scripts' clean-tree check. Axis: bash-coupling / other (language artifacts). | one-time, cheap | A Python template ships a Python `.gitignore`; the clean-tree coupling is real and language-independent in *shape* (every language has build/cache artifacts). Hypothesis, n=1. |
| `requirements.txt` | pre-supplied (not template scaffolding) | Product deps (mediapipe, opencv, numpy, …) + dev tools (ruff, pytest) were committed by the Product Owner, not inherited from the template. | — | Out of template scope; noted for completeness. |

---

## Part B — Event log (chronological)

Append the moment friction occurs, so nothing is lost between orientation and review.
Findings fold back into Part A.

| when (milestone/step) | what happened | axis | resolution |
| --- | --- | --- | --- |
| M1 / Step 1 orient | `scripts/` ships only the three workflow scripts; `lint.sh` and `review-context.sh` were not ported, yet `CLAUDE.md`'s Review section still instructs running `scripts/review-context.sh` → dangling reference. | bash-coupling + template-design-flaw | Recarve the gate to Python (Issue A); fix the `CLAUDE.md` Review prose in the planning PR. |
| M1 / Step 1 orient | `PLAN.md` contained the donor template's full Milestone 1–12 history, not a posing-coach skeleton. | template-design-flaw | Gutted and rewritten to M1 in the planning PR. |
| M1 / Step 1 orient | ruff/pytest/python are not on the global PATH; they live in `.venv/Scripts/*.exe` (Windows venv layout, not POSIX `.venv/bin`). | shell-env / machine | Gate and all verification run with the venv active; recorded as a key constraint in the gate handoff. |
| M1 / Step 1 orient | `mediapipe 0.10.35` imports cleanly (with `cv2`) in the venv → M1 is feasible offline **iff** the bundled `mediapipe.solutions.pose` API is used (the Tasks API needs a downloaded `.task` model). | other (product-dep) | Constrain Issue B to the legacy `solutions.pose` API for hermeticity. |
| M1 / Step 3 plan | `pytest` exits 5 on "no tests collected", so a gate treating non-zero as failure would fail on the empty bootstrap tree (the gate PR precedes the first test). This parallels the donor's bash empty-array/`nullglob` fights (Milestones 5, 9) — same *bootstrap-empty-suite* category, different mechanism. | bash-coupling | `gate.py` treats pytest exit 5 as non-failing; pinned in Issue A acceptance. |
