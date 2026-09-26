# Architecture direction

The LETools importer produces a versioned `BuildSnapshot`. The Last Epoch
Building evaluator calculates health and armour for a narrow 1.4.7 Sentinel
subset. The dataset command evaluates every supported two-passive allocation
for one saved starting snapshot. ML models remain future work.

## Two goals

Build a useful Last Epoch build explorer while learning traditional ML through
measured experiments. Favor changes that serve both goals. Last Epoch is the
only supported game planned for now; there is no cross-game abstraction.

## Names and responsibilities

Humans and agents should recognize the same system in issues, PRs, docs,
diagrams, the folder tree, and code. Use the same terms, ownership, and behavior
in each. A reader should be able to follow a named component to its code and
back without translating between architectural vocabularies.

Organize code by the data and work it owns: build data, importing, build evaluation,
and ML experiments. The `domain/` directory owns build data and validity rules;
its name does not require a DDD layer structure.

| Term | Meaning | Current definition or owner |
| --- | --- | --- |
| Build snapshot | Our recorded build data, versions, provenance, and unresolved information; it does not establish game validity. | `BuildSnapshot` in `domain/snapshot.py` and its [format contract](../../src/arpg_build_lab/domain/README.md) |
| Raw response | The original LETools response bytes retained for later interpretation. | `raw.json`, saved by `importers/cli.py` |
| Import run | One import's output directory containing raw response, snapshot, and provenance files. | `importers/cli.py:save` |
| LETools importer | Code that retrieves a requested LETools response and translates it into a build snapshot. | `importers/letools.py` |
| Build evaluator | Code that runs a calculator for a supported build snapshot and records its reference results. | `evaluators/le_building.py` and [its limits](../../src/arpg_build_lab/evaluators/README.md) |
| Build evaluation | A versioned record of the evaluated snapshot, calculator provenance, metrics, and retained-file hashes. | `BuildEvaluation` in `domain/evaluation.py` and its [format contract](../../src/arpg_build_lab/domain/README.md) |
| Dataset | One starting snapshot and the ordered, complete set of its supported passive allocations with reference evaluations. | `datasets/` and its [manifest contract](../../src/arpg_build_lab/datasets/README.md) |

Paths in this document are relative to `src/arpg_build_lab/` unless stated
otherwise. Keep narrow terminology beside the owning module in its README or
an appropriate contract docstring. Python types and their persisted contracts
define fields and allowed values; do not duplicate them in a separate naming
or ontology registry.

Use these rules when adding or changing code:

- Reuse an existing term when the meaning matches. When two things differ,
  explain the difference and choose distinct names. External API names stay
  intact at the import or build evaluation boundary and in retained source data.
- Name folders and modules for their responsibility or source, such as
  `importers/letools.py`. Use domain nouns for data types and clear verbs for
  operations. Let the namespace supply context: `letools.fetch()` is enough.
  `BuildSnapshot` and "build snapshot" are the same term in Python and prose;
  normal casing, plurals, and context do not require repetitive identifiers.
- Use the existing importer and build evaluator names. Do not create alternate
  `adapters`, `ports`, `use_cases`, `interactors`, `repositories`, or `services`
  layers simply to apply DDD, hexagonal, or Clean Architecture conventions.
  A proposed abstraction must solve a concrete problem, have a responsibility
  describable in plain language, and fit the documented dependencies. Record a
  changed architecture here before propagating its terminology.
- If a function or module needs several unrelated names to explain its work,
  inspect its responsibilities. A glossary alias cannot fix unclear ownership.
- Rename code, callers, tests, current documentation, and diagrams together.
  Update affected active issues, including open epics, and PRs. Treat names in
  saved data, public commands, and external APIs as compatibility contracts;
  plan migration when they change.

Current import operations have distinct meanings:

```text
fetch        requested URL -> raw response
parse_build  raw response  -> BuildSnapshot
save         raw response + BuildSnapshot -> import run
load         import run -> validated BuildSnapshot
```

`fetch` and `parse_build` live in `importers/letools.py`; `save` and `load` live in
`importers/cli.py`. Re-importing a saved raw response runs `parse_build` and `save`;
it is different from loading an existing snapshot. Helpers may use short names
within their module; the architecture document is not a catalog of every symbol.

This policy takes two practices from Codex: [explicit naming conventions](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/AGENTS.md#L269)
and [terminology beside the owning code](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/codex-rs/tui/src/bottom_pane/footer.rs#L15).
The vocabulary and ownership above are this project's decisions.

## ML vocabulary

Use established ML terms for ML concepts. Qualify overlapping software terms
rather than redefining them. Call application data a build representation or
`BuildSnapshot`; use **ML model** when "model" alone could mean either.

| Term | Meaning in this project |
| --- | --- |
| Features (`X`) | Inputs prepared from build snapshots, such as passive point counts or affix tiers. |
| Regression targets (`y`) | Continuous numeric reference outputs, such as calculator damage, that an ML model learns to predict. |
| Predictions | An ML model's estimates, such as predicted damage; call these surrogate predictions in the search flow. |
| Model evaluation | Measuring predictive quality, such as error on held-out builds. A build evaluator instead runs a calculator. |
| Normalization | Numerical preprocessing, such as scaling a sample to unit norm. Distinguish this from standardization and from parsing source data with `parse_build()`. |

These meanings follow scikit-learn's [glossary](https://scikit-learn.org/stable/glossary.html#term-targets),
[model evaluation guide](https://scikit-learn.org/stable/modules/model_evaluation.html),
and [preprocessing guide](https://scikit-learn.org/stable/modules/preprocessing.html#normalization).
A **surrogate model** is an ML model that approximates a more expensive function,
here a build evaluator. This is established [surrogate modeling terminology](https://botorch.org/docs/overview),
not a commitment to a particular ML algorithm.

## Current import flow

Paths below are relative to `src/arpg_build_lab/`. The `arpg-import` command
in `importers/cli.py:main` selects the input, calls the importer, saves the
result, and prints a summary.

```text
Planner URL -> importers/letools.py:fetch --+
                                            |
Saved raw JSON -----------------------------+
                                            v
                             importers/letools.py:parse_build
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
snapshot, raw-response hash, and retained version evidence. Replaying a raw response through the command
runs `parse_build()` again and writes a new saved build.

## Current evaluation flow

The `arpg-evaluate` command in `cli.py` loads an existing import run and checks
the source content supported by `evaluators/le_building.py`. The evaluator
converts canonical snapshot fields to LEB XML, runs the pinned calculator in a
fresh process, and checks the loaded build before accepting its metrics.

```text
importers/cli.py:load -> domain/snapshot.py:BuildSnapshot
                            |
                            v
                evaluators/le_building.py:evaluate
                            |
                            v
              domain/evaluation.py:BuildEvaluation
                            |
                            v
             evaluation.json + retained inputs/output
```

## Current dataset flow

`arpg-dataset` in `datasets/cli.py` validates an import run, enumerates
allocations through `datasets/passive_space.py`, and asks the existing build
evaluator to calculate each candidate. `datasets/manifest.py:load` checks the
retained starting snapshot raw response and every candidate evaluation after generation or
after moving the dataset run.

```text
importers/cli.py:load -> datasets/passive_space.py:candidates
                              |           |
                              |           v
                              |   evaluators/le_building.py:evaluate
                              |           |
                              +-----------+-> datasets/manifest.py:load
                                                |
                                                v
                                      complete dataset run
```

## Future ML

The following responsibilities remain planned. These labels describe intended
work, not additional implemented modules.

```text
Training:
BuildSnapshot -> build evaluator -> regression targets (y) -+
       |                                                    +-> train surrogate model
       +------> feature preparation -> features (X) --------+

Search:
candidate builds -> features -> surrogate predictions -> candidate selection
                                                               |
                                                               v
                                                        build evaluator
                                                               |
                              +--------------------------------+----+
                              v                                     v
                   tradeoffs + prediction errors        new training examples
```

Generated or mutated builds will also use `BuildSnapshot`. Keep diagrams of
implemented components tied to code names or module paths. Check arrows against
the actual calls, dependencies, or data flow described by the diagram.

## Ownership

| Directory | Responsibility | Dependencies |
| --- | --- | --- |
| `src/arpg_build_lab/domain/` | Build data and validity rules | No importer, build evaluator, command, or ML dependencies |
| `src/arpg_build_lab/importers/` | Parse external builds into `BuildSnapshot` | Domain |
| `src/arpg_build_lab/evaluators/` | Supported LEB conversion, execution, and metric extraction | Domain and optional Lupa runtime |
| `src/arpg_build_lab/datasets/` | Generation from one starting snapshot, evaluation orchestration, and dataset persistence | Domain, importer, and build evaluator |
| `ml/` | Future feature preparation, training, and error measurement | Domain and versioned datasets |
| `scripts/` | Development checks and their output | Python standard library and locked development tools |

Import commands, persistence, reload, and summary live in `importers/cli.py`.
The evaluation command in `cli.py` coordinates the importer loader and build
evaluator without a dependency between their packages. The dataset command
reuses both; the importer and evaluator do not depend on datasets. Search
remains future work.

## Data that we own

`BuildSnapshot` schema 1 retains character, passives, skills, equipment, idols,
blessings, game-version evidence, source provenance, and diagnostics. The
imported raw response sits beside each snapshot and is checked by SHA-256 on
reload. Domain types are independent of the importer package.

Keep schema version, game version, source version, and build evaluator version
separate. Use stable game IDs when available. Never silently combine game
versions or infer an exact version without evidence. Unknown version handling
is an explicit importer decision before build evaluation or dataset use.

`BuildEvaluation` schema 1 records only supported health and armour metrics,
with units and a separate meaning for zero and missing values. It links the
exact evaluated snapshot and retained calculator files by content hash. The
result sits outside Git. Calculator results can disagree; treat them as
references when using them as regression targets. They do not define our build
representation.

## Application language and integration

Write all application code we own in Python, including domain rules, importers,
build evaluators, build manipulation, search, ML, orchestration, and any
future UI. Introduce another language only when a concrete problem in our
application justifies it. Record the problem and the reason for that choice
when it arises.

External tools and libraries may use any language or runtime, such as a Lua
calculator. For build sources and calculators, keep API details in the importer
or build evaluator that uses them. Choose the simplest supported integration that
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
purposes. The former supplies controlled examples; the latter helps initialize and
validate realistic behavior. Keep the experiment's split and scope visible.

Optimization can find predictions the surrogate gets badly wrong. Preserve
those candidates for investigation, reference verification, and possible active
learning rather than hiding their errors.
