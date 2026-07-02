# AI Engineering Operating Plan

## Project Vision

Build an AI-native engineering operating system that enables a solo builder to work with AI agents as if managing a disciplined, high-performing software engineering team.

The focus is on improving engineering process, maintainability, review quality, and learning—not maximizing automation.

This document is jointly maintained by the Product Owner and the Staff Engineer and should evolve throughout the project.

---

## Current Objective

Milestones 1–12 are complete: the planning/handoff/review tooling is shipped and validated, and **parallel dependency-graph decomposition** is adopted and validated under real parallelism (Milestone 12). The roadmap is at a **rest state** — there is no active milestone. The next build, if any, is an open Product Owner decision (see Active Milestone and Acceleration Roadmap).

Increment 1 (auto-open the PR after the agent pushes) has been **dropped**: Milestone 12 measured the friction it targeted — manual PR filing — as below the automation bar at current scale, so its premise failed empirically. Dropping it does not re-open the friction gate, which still governs everything outside any named acceleration roadmap; the gate was always a bounded Product Owner override, not removed.

---

## Completed Milestones

### Milestone 1: Foundation — Complete

Core repository artifacts shipped: CLAUDE.md, PLAN.md, AGENTS.md, README.md, issue and PR templates, `scripts/new-issue.sh`. The Staff Engineer / Product Owner collaboration model is established and the planning process is repeatable across sessions.

### Milestone 2: External Agent Validation — Complete

The manual handoff process was validated across two implementation cycles. External agents completed scoped issues without clarification requests. Git ownership boundaries, scope discipline, and handoff quality all held. The implementation handoff has emerged as a first-class workflow artifact.

### Milestone 3: Targeted Automation of Issue/Branch/Handoff Creation — Complete

The handoff format was formalized in CLAUDE.md (Issues #21/#25, PRs #22/#24). `scripts/new-handoff.sh` (Issue #25, PR #26) now creates and pushes the feature branch and renders the canonical handoff from issue metadata, composing with the existing `scripts/new-issue.sh`. The review cycle caught and corrected a non-hermetic test before merge.

### Milestone 4: Validate the Automation Through Use — Complete

The issue/branch/handoff automation was validated across two real cycles: ShellCheck linting (Issue #28, PR #29) and the dirty-tree fix (Issue #31, PR #32). In both, the external agent implemented the scoped issue with no clarification requests and the resulting PR matched the handoff. The cycle also surfaced and resolved a self-referential friction: `.claude/settings.local.json` was git-tracked and rewritten by the Claude Code harness on every permission grant, dirtying the tree and blocking `new-handoff.sh`; it is now untracked and gitignored (PR #32). The metadata/file-list duplication and verification-prerequisite frictions noted after cycle 1 did not recur. One friction did recur without being resolved — driving the interactive scripts requires hand-built piped stdin — and is carried forward as the next increment.

### Milestone 5: Non-Interactive Input for the Handoff Scripts — Complete

Non-interactive flag mode shipped on both scripts — `new-handoff.sh` (Issue #34, PR #35) and `new-issue.sh` (Issue #36, PR #37) — removing the hand-built piped-stdin friction that recurred across both Milestone 4 cycles. Real use of the flag mode immediately exposed a latent robustness bug: rendering an issue or handoff with empty in-scope/out-of-scope lists aborted under `set -u` on bash 3.2 (`IN_SCOPE[@]: unbound variable`). It was fixed narrowly by guarding the empty-array render loops (Issue #39, PR #40); `new-handoff.sh` was confirmed already safe because validation requires its lists non-empty before the renderer is reached. Both scripts' flag modes were validated in a real cycle: Issue #39 was created through `new-issue.sh`'s flags and its handoff through `new-handoff.sh`'s flags.

### Milestone 6: Read-Only Review-Preparation Helper — Complete

`scripts/review-context.sh` shipped (Issue #41, PR #43): a read-only helper that assembles PR review context in one command — PR metadata/body, the linked issue and its acceptance criteria (resolved from a Closes/Fixes/Resolves reference), the changed-file list, the diff (or a stat summary above a size threshold), and the results of the repository's lint and test checks — without making or recording any review decision. The read-only boundary is enforced by a test that fails on any write-capable `gh` subcommand. The cycle dogfooded both Milestone 5 scripts (Issue #41 via `new-issue.sh`'s flags, the branch and handoff via `new-handoff.sh`'s flags) with no friction. Review was APPROVE: all acceptance criteria met, all four verification commands green under bash 3.2. Non-blocking observations were carried forward to the validation phase below.

### Milestone 7: Validate the Review-Preparation Helper Through Use — Complete

`scripts/review-context.sh` was exercised on a real review — PR #48's initial review and re-review. It materially reduced review-prep effort: one command assembled the PR metadata/body, the linked issue and its acceptance criteria, the changed-file list, the diff, and lint/test results, replacing the manual multi-step gather. The same cycle exposed a real limitation: the helper's test runner uses a hardcoded script list, so it silently never ran the PR's new `tests/test-trigger-agent.sh` while still reporting "All tests passed" — false confidence on exactly the new code under review. The reviewer caught it only by running the test manually. The identical hardcoded-list pattern in `lint.sh` had already forced PR #48 to be hand-patched to honor AC #6. Both are the same root cause, now promoted to Milestone 9.

### Milestone 8: Manually Trigger the External Agent (Narrowest Slice) — Complete

`scripts/trigger-agent.sh` shipped (Issue #46, PR #48): it takes an existing handoff path plus a `--dry-run` flag, runs preflight (path given, file non-empty, run from repo root, codex installed, clean working tree), and invokes `codex exec --sandbox workspace-write - < "$handoff"` exactly once, exiting with Codex's status without parsing its output. Hermetic tests (stubbed codex, bash 3.2) cover stdin delivery, dry-run, each preflight failure, and status propagation. Review was REQUEST CHANGES then APPROVE: the first pass found AC #6 hollow because `lint.sh` excluded the new script and test; the revision wired both in via a commit scoped to `lint.sh` only. The previously-owed live validation is now discharged: the trigger drove the Milestone 9 implementation as a real `codex exec` run (Codex v0.139.0, clean stdin delivery, exit 0), confirming end-to-end behavior against a real binary rather than a stub. One known property surfaced: Codex's sandbox could not reach `api.github.com`, so the agent implemented/committed/pushed but could not open its own PR; the Staff Engineer filed it.

Observations carried forward from Milestone 6 (recorded only): ~~unused `contains()` helper~~ (removed in Issue #60 / PR #61 as a workflow-exercise dogfood, not an earned increment); untested zero-arg path; above-threshold diffs still fetch the full diff before `--stat`, with `gh pr diff` running up to three times; write-capable `gh` detection is a denylist. Three observations remain recorded-only.

### Milestone 9: Replace Hardcoded File Lists with Discovery — Complete

`scripts/lint.sh` and `scripts/review-context.sh` now derive their file lists from the filesystem (Issue #50, PR #51, reviewed APPROVE): `lint.sh` globs `scripts/*.sh` and `tests/test-*.sh`; `review-context.sh`'s verification keeps `run_check "lint"` and loops over discovered `tests/test-*.sh`. Both use `shopt -s nullglob` plus a guarded array-count check before expansion, avoiding the Milestone 5 `set -u`/empty-array regression on bash 3.2. The test runner matches `tests/test-*.sh` (not `tests/*.sh`), verified by a stub asserting non-test helpers are excluded; discovery is independent in each script (no shared helper). The fix validated itself in review — `review-context.sh` on PR #51 executed all four tests, including the two the old hardcoded list silently skipped — closing the root cause behind both PR #48 failures.

### Milestone 10: Clean `new-handoff.sh` Output — Complete

`scripts/new-handoff.sh` now writes its git operations (fetch/checkout/pull/push), dry-run notice, separators, and interactive prompts to stderr, so stdout carries only the rendered handoff (Issue #54, PR #55). This removes the manual-cleanup friction that recurred across the Milestone 8 and 9 trigger cycles, making the handoff cleanly pipeable into `trigger-agent.sh`; a test captures stdout and stderr separately to prove the split. The same cycle confirmed the second occurrence of the PR-ownership gap — the Codex agent implemented and pushed but its sandbox could not reach `api.github.com` — which subsequently justified codifying the manual fallback in CLAUDE.md (PR #56).

### Milestone 11: Adopt Parallel Dependency-Graph Decomposition — Complete

The parallel-decomposition convention shipped (Issue #65, PR #66, reviewed APPROVE): CLAUDE.md's Planning Expectations now documents recording dependency edges via native GitHub issue references, per-issue file-footprint declaration, a pre-dispatch pairwise disjointness check, the two-part parallel-eligibility rule (disjoint footprint AND no interface dependency, else serialize via an edge), and reading live run-state from `gh issue list`/`gh pr list` with the graph recorded in a milestone tracking issue, not PLAN.md. The issue template gained an optional `## Dependencies` section. It is a convention, not infrastructure — no new script — and the discovery-based lint/test runners stayed green. The cycle dogfooded the full lifecycle end to end (planning PR → `new-issue.sh`/`new-handoff.sh` flag modes → live `trigger-agent.sh` run → `review-context.sh` review → merge); the agent held scope exactly and the review was a clean first-pass APPROVE.

### Milestone 12: Validate Decomposition Under Real Parallelism — Complete

The decomposition convention was exercised on its first genuinely parallel batch (tracking issue #70): two file-disjoint issues — #68 (README.md, PR #71) and #69 (AGENTS.md, PR #72) — were dispatched to two `codex` agents running **concurrently in isolated clones**, then both merged to `main`. The convention's core claim held: each agent stayed within its declared footprint under true concurrency (neither touched the other's file, aided by listing the concurrent issue's file under `Files Not to Modify`), and the two disjoint branches merged with no conflict (#72 was `MERGEABLE CLEAN` against the post-#71 `main`). This discharges Milestone 11's owed validation. **Measured-N:** the manual PR filings were trivial (~seconds each), so the parallel amplification of PR-filing cost is real but small per occurrence — which collapsed Increment 1's premise (now dropped; see Acceleration Roadmap). Two infrastructure findings surfaced: `trigger-agent.sh` is worktree-incompatible (now attached to Increment 2's roadmap edge) and `new-issue.sh`'s renderer omits the issue template's `## Dependencies` section (under Open Decisions).

---

## Active Milestone

**None — the roadmap is at a rest state.** Milestones 1–12 are complete and Increment 1 has been dropped (see Acceleration Roadmap). Whether to take up a next build is an open Product Owner decision; leaving the active slot empty is a deliberate, legitimate outcome, not a gap to fill. Increment 2 is **not** auto-promoted into this slot — its activation, if it ever happens, is a fresh Product Owner decision (see Acceleration Roadmap and Open Decisions).

---

## Acceleration Roadmap (Dogfooded as a Dependency Graph)

The Product Owner chose to accelerate toward autonomous implementation ahead of pure friction-evidence. The path was decomposed using the Milestone 11 technique. Each increment is an isolated roadmap node; the increments below are **gated** acceleration overrides — none is friction-justified, and sequence order is not a justification tier.

- **Foundation — Parallel decomposition (Milestone 11).** Complete and validated under real parallelism (Milestone 12). Depended on nothing new.
- **Increment 1 — Auto-open the PR after the agent pushes. DROPPED.** Its premise failed empirically: Milestone 12 measured the friction it targeted — manual PR filing — as below the automation bar at current scale, so the prospective justification (parallel batches multiplying that cost) did not materialize. This is a drop, not a deferral, and it leaves **no "revisit Increment 1" hook**: if unattended/looped runs ever make PR-filing cost real (no human present to file at all), that is a **new** decision under a **new** rationale, not a resumption of Increment 1. Increment 1 was an isolated node, so its removal triggers no downstream re-derivation.
- **Increment 2 — Label-triggered agent runs.** Depends only on the existing `trigger-agent.sh` (never on Increment 1); applying a GitHub label would fire `trigger-agent.sh` in place of a manual command. Gated acceleration override; **not auto-promoted** into the active slot — taking it up is a fresh Product Owner decision. **Precondition attached to this edge:** the `[[ -d .git ]]` repo-root check is worktree-incompatible — inside a git worktree `.git` is a file, not a directory, so the check fails. This same check exists identically in **two** scripts: `trigger-agent.sh` (line 36) and `lint.sh` (line 10); the incompatibility is therefore not confined to the trigger (n=1 observation, found in Milestone 12, which therefore needed separate full clones for isolation). Because Increment 2 fires `trigger-agent.sh` via label and is the increment most likely to drive concurrent runs, this incompatibility is a precondition to confront if and when Increment 2 is taken up; the narrow fix — accept a `.git` file as well as a directory — must be applied to **both** scripts, not just the trigger.
- **Increment 3 — Agent-to-agent review/revise loop.** With Increment 1 dropped, its precondition reduces from "Increments 1 **and** 2 plus validated throughput" to **"Increment 2 plus validated throughput"** — the largest leap. Carries the correlated-validator risk (see Risks), so **the final merge stays human or independent** even if the loop is autonomous. Gated acceleration override.

The roadmap is at a rest state. No increment is active; opening any of the above is an open Product Owner decision.

---

## Staff Engineer Recommendations

### Current Recommendation

The Product Owner has decided to accelerate toward automation and, eventually, productizing this framework for other projects. This replaces the prior blanket "no automation" stance — but the gating logic stays: automate only what has been demonstrated through repeated manual use, starting with the narrowest, most mechanical step first. The gate now also runs forward: shipped automation must demonstrate value in real use before the next layer (triggering, productization) is opened.

Milestones 6 through 10 are complete and Milestone 8's owed live-run validation is discharged. The bounded gate-override worked as intended end to end: the narrowest-slice trigger shipped, reviewing its PR with `review-context.sh` produced Milestone 7's validation, that review found the hardcoded-list defect (fixed in Milestone 9), and the Milestone 9 implementation was itself driven by the first live `trigger-agent.sh` run — discharging Milestone 8's validation as a byproduct. Each step continued to surface its own next increment from real use.

Recommended next step:

1. **Hold at the rest state; take up no new build by default.** Milestones 1–12 are complete and validated, and Increment 1 has been dropped (its premise failed empirically — see Acceleration Roadmap). With the active slot deliberately empty, the disciplined default is to stop and let the next build be a fresh Product Owner decision rather than auto-promoting Increment 2. Increments 2 and 3 remain gated acceleration overrides; do not build them absent a Product Owner decision to take them up.

The friction gate still governs everything outside any named Acceleration Roadmap. Dropping Increment 1 does not loosen the gate; productization remains gated until separately justified.

The prior dirty-tree friction in the handoff flow has been resolved: `.claude/settings.local.json` is now untracked and gitignored (Issue #31, PR #32), so routine permission grants no longer dirty the tree or block `new-handoff.sh`.

Do not build, until each is separately justified by its own repeated manual pattern:

- Agent orchestration
- Multi-agent communication infrastructure
- Automatic triggering of the external agent
- Skills or GitHub integrations beyond the Milestone 3 target

### Reasoning

The operating model should emerge from experience rather than speculation, even on an accelerated timeline. Compressing the validation phase is acceptable; skipping it is not — automation targets must still be chosen from patterns that have actually repeated, not from what seems generically useful.

Premature infrastructure increases maintenance burden without validating that it solves a real problem.

---

## Open Decisions

Items requiring future discussion:

- **What the next build should be, if any — OPEN.** With Milestones 1–12 complete and Increment 1 dropped, the roadmap is at a rest state and the active slot is deliberately empty. Holding at rest is a legitimate outcome; Increment 2 is sequenced-but-gated, not auto-promoted. Choosing to take up Increment 2 (or anything else) is a fresh Product Owner decision.
- How far to automate triggering the external agent **beyond the narrowest manual slice** — partially mapped into the Acceleration Roadmap: **Increment 2 (label-triggered runs)** is the sequenced-but-gated option in this space, **not** an active or auto-promoted choice. Taking it up is a fresh Product Owner decision; anything past it (status polling, looping over issues) stays deferred until demonstrated repeated need justifies it, except where the Roadmap names it as a prerequisite for a sequenced increment.
- Whether to automate **trigger-side PR creation** — **closed: dropped with Increment 1.** Milestone 12 measured the targeted friction (manual PR filing) as below the automation bar at current scale, so the premise failed empirically. This is closed, not deferred: if unattended/looped runs ever make PR-filing cost real (no human present to file), that is a new decision under a new rationale, not a resumption of Increment 1.
- **Decomposition validated under real parallelism — Resolved (Milestone 12).** The Product Owner chose validate-first; the first genuinely parallel batch ran (tracking issue #70, PRs #71/#72): two file-disjoint agents ran concurrently in isolated clones, each stayed within its declared footprint, and both branches merged with no conflict — discharging Milestone 11's owed validation and confirming the convention's core claim. The same measurement — per-PR filing proved trivial — collapsed Increment 1's premise and led to dropping it (see Acceleration Roadmap).
- What productization requires structurally (e.g., parameterizing CLAUDE.md/AGENTS.md, removing solo-builder-specific framing) — deferred until a reusability need is demonstrated rather than anticipated.
- Whether to unify `new-issue.sh` and `new-handoff.sh` into a single flow — open only if the metadata/file-list seam between them recurs as friction; not yet observed to repeat.
- **Wrapped-title papercut when hand-filing a PR** — filing via `gh pr create` with a multi-line title produced a malformed PR title (n=1, surfaced in the Milestone 11 cycle and fixed post-hoc). This is an **independent** human-filing friction sample, distinct from the PR-ownership gap. If it recurs on the next hand-filed PR, it earns its own narrow fix — set the PR title from the issue at filing time. It stands on its own and is not evidence for any broader trigger-side PR automation (the now-dropped Increment 1 space).
- **The `[[ -d .git ]]` repo-root check is worktree-incompatible — in two scripts** — inside a git worktree `.git` is a file, not a directory, so the check fails. The identical check lives in **both** `trigger-agent.sh` (line 36) and `lint.sh` (line 10), so the eventual narrow fix (accept a `.git` file as well as a directory) must touch both, not just the trigger. Recorded as a precondition attached to **Increment 2's dependency edge** in the Acceleration Roadmap (Increment 2 fires `trigger-agent.sh`), not as a free-standing item. n=1, gated, not yet justified.
- **Reproducing the working environment on a second machine — OPEN, pre-friction, un-justified.** The Product Owner is migrating personal projects from a MacBook to a self-built PC, driven by a real constraint unrelated to this repo: model training is impractical on the Mac. This gives a concrete, named machine to reproduce the environment on where before there was none — but **nothing has broken yet**, so this is pre-friction, not friction-justified. It is a live open question, **not** a build: no environment-reproduction work is justified by this entry on its own. The observe-first move is to run the existing script suite on the PC and **log toolchain drift** — which tools are present, their versions, what breaks, and the effort to fix each — before deciding anything. That log is the evidence any future decision would rest on.
- **Docker-based reproducible environment — ACCELERATION OVERRIDE (learning-motivated), not earned work.** Separately from the pre-friction question above, the Product Owner has elected to build a Docker-based reproducible environment as a future item, motivated by **learning / skill-building** — explicitly **not** by demonstrated friction. It is labeled an **acceleration override** — a deliberate build-ahead-of-evidence choice for a named reason — by the same mechanism the Acceleration Roadmap uses; this label is load-bearing and fences the item so it cannot become false precedent for any other un-earned build. It is **not on the PC-migration critical path**: getting working on the PC uses the quickest sufficient means (likely a short install step), and this Docker build is a separate deliberate exercise that must not block day-one PC work. The toolchain-drift log from the entry above still feeds it — but as an override its role shifts from *gating whether* to build to *specifying what* the Dockerfile must pin.
- **`new-issue.sh` renderer omits the template's `## Dependencies` section** — Milestone 11 added the section to the issue template but not to `new-issue.sh`'s `render_body`, so issues created via flag mode (e.g. #68/#69) lack it; dependencies were recorded in the tracking issue instead. n=1 template/script divergence. The narrow fix is to add the section (and a `--depends-on` flag) to the renderer. Not yet justified.
- When a triggered agent cannot open its own PR — **Resolved (manual fallback codified).** The sandbox-cannot-reach-`api.github.com` gap recurred on the next triggered run, clearing the two-occurrence proven-need bar, so the fallback is now procedure in CLAUDE.md (Implementation Handoff): the Product Owner files the PR from the agent's pushed branch using the agent's PR body, and the Staff Engineer reviews the diff on its merits. The filer is the Product Owner, not the Staff Engineer, preserving the author/reviewer separation. **Still open and gated:** whether this justifies building trigger-side PR automation is tracked as its own decision above; two occurrences justify codifying the manual fallback, not automating it.
- Repository template structure beyond MVP.
- **Introduction of reusable skills** — evaluated 2026-07-01, **verdict: hold, no skill justified yet.** Candidates reviewed against the friction gate: the planning-PR flow (most-repeated, ≥3×, but its mechanical part is ~seconds/PR — below the bar by the same standard that dropped Increment 1, and its content is bespoke judgment a skill can't write); issue-based review (already a tested script + CLAUDE.md procedure, and overlaps Claude Code's built-in `/review`); cold-start orientation (already covered by CLAUDE.md's always-loaded Session Startup); the dispatch pipeline (scripts already compose, and a run-the-whole-thing skill would blur the handoff boundary). The repo's earned-automation mechanism is a *tested shell script*, not a `SKILL.md`; that stays the default even when something clears the gate. What would flip it: a judgment-heavy, multi-step, on-demand workflow that recurs and is awkward as a single script — most likely in the label-triggered/unattended direction (a fresh decision under its own rationale, not pre-built now).
- Additional persistent documentation.
- Cross-agent orchestration.

These should remain deferred until supported by practical experience.

---

## Risks

### Over-engineering

The largest risk is building infrastructure before validating process. This risk increases under the Product Owner's decision to accelerate toward automation and productization.

Mitigation:

Gate every automation step on a pattern that has actually repeated in manual use — not on convenience or speculation. Revisit this gate explicitly at the start of each new milestone.

### Correlated Validators (Increment 3)

An agent-to-agent review/revise loop pairs two LLM agents that share training blind spots, so the loop can converge on confident-but-wrong output that neither flags. Mitigation: the final merge decision stays human or independent even when the loop is autonomous, and Increment 3 is gated until decomposition and Increments 1–2 have proven the throughput justifies the orchestration cost.

### Documentation Sprawl

Excess markdown files create maintenance overhead and competing sources of truth.

Mitigation:

Prefer updating existing artifacts and using GitHub Issues and Pull Requests for transient information.

### Vendor Lock-in

Avoid coupling organizational concepts to specific AI providers.

Mitigation:

Describe responsibilities in terms of roles (e.g., Staff Engineer, Software Engineer) rather than model names whenever practical.

---

## Planning Rules

This document should remain concise and actionable.

It should capture:

- Strategic direction
- Current priorities
- Engineering recommendations
- Active risks
- Major open questions

It should not duplicate:

- GitHub Issues
- Pull Request descriptions
- Implementation details
- Change logs
- Long task lists

When priorities change, update this document rather than creating a new planning artifact.