# Project intent

ARPG Build Lab has two equally important goals: useful Last Epoch build
exploration and practical understanding of traditional ML. Keep experiments
inspectable and preserve the path to a useful optimizer. Last Epoch is the only
game in scope. Choose the simplest implementation that serves it.

## Work in the smallest area

Read the instructions on the path to the files you will change, including local
`AGENTS.md` files before entering a child area. Start searches in that area and
expand only to the contracts or callers needed for the task. Avoid recursive
instruction or documentation collection.

- `src/domain/` owns our canonical build representation and validity rules.
- `src/importers/` translates external builds into that representation.
- `src/evaluators/` adapts calculators and normalizes their results.
- `ml/` owns feature preparation, training, and measured experiments.

Add a local `AGENTS.md` when a directory has distinct responsibilities or rules.
Write only what differs from its parents: ownership, allowed dependencies,
relevant documents, and meaningful validation. If the boundary is hard to
explain, reconsider the code organization before adding more instructions.

## Read documents on demand

- Changing module boundaries or persisted data: read
  `docs/agents/architecture.md`.
- Setting up tools, portability, or artifact storage: read
  `docs/agents/development.md`.
- Creating, refining, selecting, or claiming GitHub work: read
  `docs/agents/workflow.md`. Use the `github-use` skill when available and the
  `gh` CLI for GitHub operations.
- Continuing the project or choosing its next task: read
  `docs/agents/next-steps.md`.

`docs/humans/` holds learning material. Exclude it from routine discovery and
content searches; `.ignore` does this for ripgrep. Read it only when the task
explicitly involves that material. These are context conventions, not access
controls. Current implementation must not depend on hidden journal knowledge.

## Project principles

Own a small, versioned canonical model. Keep external formats in adapters.
Retain the game version and relevant provenance in every persisted build,
evaluation, and dataset. Represent missing information honestly.

Make ML behavior measurable. Compare useful baselines, inspect failures, and
explain unfamiliar concepts using actual project examples. Evaluator outputs
are reference results that can be wrong.

Keep development and small CPU checks portable across Linux and macOS. Larger
training may use the Mac GPU. Start with files between TypeScript and Python;
add processes or services only for a demonstrated need.

Check licenses before copying code or substantial data. Prefer permissive
licenses; GPL-family dependencies require an explicit project decision. Keep
personal saves and bulk generated artifacts out of Git.
