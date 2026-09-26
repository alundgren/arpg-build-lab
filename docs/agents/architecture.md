# Architecture direction

The LETools importer produces a versioned `BuildSnapshot`. Evaluators, datasets,
and models remain future work.

## Two goals

Build a useful Last Epoch build explorer while learning traditional ML through
measured experiments. Favor changes that serve both goals. Last Epoch is the
only supported game planned for now; there is no cross-game abstraction.

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

The LETools importer in `importers/letools.py` adapts external data to the
canonical model. It uses module functions; there is no separate adapter class
or package. Saved files can be inspected directly, and `load()` validates the
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
| `src/arpg_build_lab/domain/` | Canonical build snapshot | No adapter or ML dependencies |
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
evaluation adapters, build manipulation, search, ML, orchestration, and any
future UI. Introduce another language only when a concrete problem in our
application justifies it. Record the problem and the reason for that choice
when it arises.

External tools and libraries may use any language or runtime, such as a Lua
calculator. Keep external tool integrations behind adapters and choose the
simplest supported integration that meets our needs.

Reuse canonical domain types and validity rules across Python modules. Keep ML
dependencies out of the domain and importer code. Use versioned files for build
snapshots, datasets, and reproducible experiment artifacts; file exchange is
not required between Python modules. Agree on and validate each persisted or
external exchange format when its first consumer exists. Add processes or
services only for a demonstrated need.

## Learning and reuse

Begin with a narrow target and compare useful simple baselines before increasing
model complexity. Generated data and real imported builds serve different
purposes. The former supplies controlled examples; the latter helps seed and
validate realistic behavior. Keep the experiment's split and scope visible.

Optimization can find predictions the surrogate gets badly wrong. Preserve
those candidates for investigation, reference verification, and possible active
learning rather than hiding their errors.
