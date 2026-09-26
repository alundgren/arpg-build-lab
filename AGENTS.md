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

- `src/arpg_build_lab/domain/` owns our canonical build representation and validity rules.
- `src/arpg_build_lab/importers/` translates external builds into that representation.
- `src/arpg_build_lab/evaluators/` will adapt calculators and normalize their results.
- `ml/` owns feature preparation, training, and measured experiments.

Add a local `AGENTS.md` when a directory has distinct responsibilities or rules.
Write only what differs from its parents: ownership, allowed dependencies,
relevant documents, and meaningful validation. If the boundary is hard to
explain, reconsider the code organization before adding more instructions.

## Read documents on demand

- Choosing or changing names, module boundaries, or persisted data: read
  `docs/agents/architecture.md`.
- Setting up tools, portability, artifact storage, or testing and validation: read
  `docs/agents/development.md`.
- Creating, refining, selecting, or claiming GitHub work, writing commits, or
  preparing and reviewing PRs: read
  `docs/agents/workflow.md`. Use the `github-use` skill when available and the
  `gh` CLI for GitHub operations.
- Continuing the project or choosing its next task: read
  `docs/agents/next-steps.md`.

`docs/humans/` holds learning material. Exclude it from routine discovery and
content searches; `.ignore` does this for ripgrep. Read it only when the task
explicitly involves that material. These are context conventions, not access
controls. Current implementation must not depend on hidden journal knowledge.

## LETools access

Download individual LETools builds only on direct user request. The user must
identify the build or planner URL. An agent or Python script may make the HTTP
requests for that import, including using a browser-compatible User-Agent.
Fetch only the requested build and the specific metadata needed to import it.

Do not crawl or scrape LETools for collections, enumerate planner IDs, or
bulk-download builds or game data. Cache requested builds locally. Generate ML
training examples through local mutations and evaluation of saved builds.

## Project principles

Prefer ASCII diagrams over prose when explaining algorithms, processes, and
data flow. Add short prose for context and details the diagram cannot show.
Apply this to documentation, PR summaries and evidence, and explanations during
work. Include a diagram when it helps the reader understand or assess the change;
simple changes may need only a sentence. For implemented components, use actual
code names or pair a readable role with its module path. Mark future work clearly.

Make issues, PRs, docs, diagrams, the folder tree, and code describe the same
system for humans and agents. Use one name for each concept and responsibility,
following `docs/agents/architecture.md`. Match ownership and behavior as well as
words. Name code after the Last Epoch concepts it models or the work it does.
New architectural layers need a concrete project problem; do not introduce
them or their terminology merely to follow a named pattern.

Own a small, versioned build model. Importers own external build formats;
evaluators own calculator integration and normalized results.
Retain the game version and relevant provenance in every persisted build,
evaluation, and dataset. Represent missing information honestly.

Make ML behavior measurable. Compare useful baselines, inspect failures, and
explain unfamiliar concepts using actual project examples. Evaluator outputs
are reference results that can be wrong.

Write all application code we own in Python. Introduce another language only
when a concrete problem in our application justifies it. External tools and
libraries may use any language or runtime. Keep code specific to a build source
or calculator in the corresponding importer or evaluator.

Keep development and small CPU checks portable across Linux and macOS. Larger
training may use the Mac GPU. Keep versioned files for reproducible artifacts;
add processes or services only for a demonstrated need.

Check licenses before copying code or substantial data. Prefer permissive
licenses; GPL-family dependencies require an explicit project decision. Keep
personal saves and bulk generated artifacts out of Git.
