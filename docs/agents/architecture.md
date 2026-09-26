# Architecture direction

The LETools importer produces a versioned `BuildSnapshot`. Evaluators, datasets,
and models remain future work.

## Two goals

Build a useful Last Epoch build explorer while learning traditional ML through
measured experiments. Favor changes that serve both goals. Last Epoch is the
only supported game planned for now; there is no cross-game abstraction.

## Names and responsibilities

Humans and agents should recognize the same system in issues, PRs, docs,
diagrams, the folder tree, and code. Use the same terms, ownership, and behavior
in each. A reader should be able to follow a named component to its code and
back without translating between architectural vocabularies.

Organize code by the data and work it owns: build data, importing, evaluation,
and ML experiments. The `domain/` directory owns build data and validity rules;
its name does not require a DDD layer structure.

| Term | Meaning | Current definition or owner |
| --- | --- | --- |
| Build snapshot | Our recorded build data, versions, provenance, and unresolved information; it does not establish game validity. | `BuildSnapshot` in `domain/snapshot.py` and its [format contract](../../src/arpg_build_lab/domain/README.md) |
| Raw response | The original LETools response bytes retained for later interpretation. | `raw.json`, saved by `importers/cli.py` |
| Import run | One import's output directory containing raw response, snapshot, and provenance files. | `importers/cli.py:save` |
| LETools importer | Code that retrieves a requested LETools response and translates it into a build snapshot. | `importers/letools.py` |
| Evaluator | Planned code that runs a calculator for a build snapshot and normalizes the results into `BuildEvaluation`. | Reserved `evaluators/` directory; no implementation yet |

Paths in this document are relative to `src/arpg_build_lab/` unless stated
otherwise. Keep narrow terminology beside the owning module in its README or
docstring. Python types and their persisted contracts define fields and allowed
values; do not duplicate them in a separate naming or ontology registry.

Use these rules when adding or changing code:

- Reuse an existing term when the meaning matches. When two things differ,
  explain the difference and choose distinct names. External API names stay
  intact at the import or evaluation boundary and in retained source data.
- Name folders and modules for their responsibility or source, such as
  `importers/letools.py`. Use domain nouns for data types and clear verbs for
  operations. Let the namespace supply context: `letools.fetch()` is enough.
  `BuildSnapshot` and "build snapshot" are the same term in Python and prose;
  normal casing, plurals, and context do not require repetitive identifiers.
- Use the existing importer and evaluator names. Do not create alternate
  `adapters`, `ports`, `use_cases`, `interactors`, `repositories`, or `services`
  layers simply to apply DDD, hexagonal, or Clean Architecture conventions.
  A proposed abstraction must solve a concrete problem, have a responsibility
  describable in plain language, and fit the documented dependencies. Record a
  changed architecture here before propagating its terminology.
- If a function or module needs several unrelated names to explain its work,
  inspect its responsibilities. A glossary alias cannot fix unclear ownership.
- Rename code, callers, tests, current documentation, and diagrams together.
  Update affected active issues and PRs. Treat names in saved data, public
  commands, and external APIs as compatibility contracts; plan migration when
  they change.

Current import operations have distinct meanings:

```text
fetch      requested URL -> raw response
normalize  raw response  -> BuildSnapshot
save       raw response + BuildSnapshot -> import run
load       import run -> validated BuildSnapshot
```

`fetch` and `normalize` live in `importers/letools.py`; `save` and `load` live in
`importers/cli.py`. Re-importing a saved raw response runs `normalize` and `save`;
it is different from loading an existing snapshot. Helpers may use short names
within their module; the architecture document is not a catalog of every symbol.

This policy takes two practices from Codex: [explicit naming conventions](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/AGENTS.md#L269)
and [terminology beside the owning code](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/codex-rs/tui/src/bottom_pane/footer.rs#L15).
The vocabulary and ownership above are this project's decisions.

## Current import flow

Paths below are relative to `src/arpg_build_lab/`. The `arpg-import` command
in `importers/cli.py:main` selects the input, calls the importer, saves the
result, and prints a summary.

```text
Planner URL -> importers/letools.py:fetch --+
                                            |
Saved raw JSON -----------------------------+
                                            v
                             importers/letools.py:normalize
                                            |
                                            v
                             domain/snapshot.py:BuildSnapshot
                                            |
                                            v
                                  importers/cli.py:save
                                            |
                                            v
                         raw.json + snapshot.json + provenance.json
                                            |
                                     later Python reload
                                            v
                                  importers/cli.py:load
```

The LETools importer in `importers/letools.py` translates external data into
`BuildSnapshot`. Saved files can be inspected directly, and `load()` validates the
snapshot and raw-response hash. Replaying a raw response through the command
runs normalization again and writes a new saved build.

## Future evaluation and ML

The following responsibilities remain planned. These labels describe intended
work, not additional implemented modules.

```text
Training:
BuildSnapshot -> reference evaluator -> labels ---+
       |                                         +-> train surrogate
       +------> feature preparation -> features -+

Search:
candidate builds -> features -> surrogate scores -> candidate selection
                                                         |
                                                         v
                                                reference verification
                                                         |
                          +------------------------------+-------+
                          v                                      v
             tradeoffs + prediction errors            new labelled examples
                                                      for later training
```

Generated or mutated builds will also use `BuildSnapshot`. Keep diagrams of
implemented components tied to code names or module paths. Check arrows against
the actual calls, dependencies, or data flow described by the diagram.

## Ownership

| Directory | Responsibility | Dependencies |
| --- | --- | --- |
| `src/arpg_build_lab/domain/` | Build data and validity rules | No importer, evaluator, command, or ML dependencies |
| `src/arpg_build_lab/importers/` | Recognize and normalize external builds | Domain |
| `src/arpg_build_lab/evaluators/` | Future calculator integration | Domain and chosen calculator integration |
| `ml/` | Future feature preparation, training, and error measurement | Domain and versioned datasets |

The current command, persistence, reload, and summary functions live in
`importers/cli.py`. Add generation, mutation, search, and further orchestration
when that work begins. Modules expose the contracts their callers need and keep
internal representations local.

## Data that we own

`BuildSnapshot` schema 1 retains character, passives, skills, equipment, idols,
blessings, game-version evidence, source provenance, and diagnostics. The
imported raw response sits beside each snapshot and is checked by SHA-256 on
reload. Domain types are independent of the importer package.

Keep schema version, game version, source version, and evaluator version
separate. Use stable game IDs when available. Never silently combine game
versions or infer an exact version without evidence. Unknown version handling
is an explicit importer decision before evaluation or dataset use.

`BuildEvaluation` should normalize only metrics the integration supports, with
units and missing-value meaning defined. Retain raw results outside Git for
investigation. External calculators provide reference labels and can disagree.
They do not define our canonical model.

## Application language and integration

Write all application code we own in Python, including domain rules, importers,
evaluators, build manipulation, search, ML, orchestration, and any
future UI. Introduce another language only when a concrete problem in our
application justifies it. Record the problem and the reason for that choice
when it arises.

External tools and libraries may use any language or runtime, such as a Lua
calculator. For build sources and calculators, keep API details in the importer
or evaluator that uses them. Choose the simplest supported integration that
meets our needs.

Reuse canonical domain types and validity rules across Python modules. Keep ML
dependencies out of the domain and importer code. Use versioned files for build
snapshots, datasets, and reproducible experiment artifacts; file exchange is
not required between Python modules. Agree on and validate each persisted or
external exchange format when its first consumer exists. Add processes or
services only for a demonstrated need.

When another tool first needs a generated schema or API description, derive it
from the owning types and check that it stays in sync. Codex's [protocol fixture
checks](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/codex-rs/app-server-protocol/src/schema_fixtures_tests.rs#L19)
are an example of this practice. Such checks verify a contract; reviewers still
need to check that names mean the same thing in code and documentation.

## Learning and reuse

Begin with a narrow target and compare useful simple baselines before increasing
model complexity. Generated data and real imported builds serve different
purposes. The former supplies controlled examples; the latter helps seed and
validate realistic behavior. Keep the experiment's split and scope visible.

Optimization can find predictions the surrogate gets badly wrong. Preserve
those candidates for investigation, reference verification, and possible active
learning rather than hiding their errors.
