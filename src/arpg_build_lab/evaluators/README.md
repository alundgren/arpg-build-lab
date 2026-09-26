# Last Epoch Building evaluation

`arpg-evaluate` loads an existing import run, checks its saved response and
provenance, then evaluates canonical `BuildSnapshot` fields through the pinned
Last Epoch Building (LEB) calculator. The command does not contact LETools.

```text
import run -> importers.cli.load -> BuildSnapshot
           -> evaluators.le_building -> fresh LEB process
           -> domain.evaluation.BuildEvaluation + retained files
```

Install the optional Lupa 2.8 runtime with `uv sync --locked --extra calculator`.
On Apple Silicon macOS, the Lupa wheel omits LuaJIT. Install Homebrew's
`luajit` and `pkg-config`, then build the locked Lupa source package against
that runtime:

```bash
brew install luajit pkg-config
LUPA_NO_BUNDLE=true uv sync --locked --extra calculator --no-binary-package lupa --reinstall-package lupa
```

The worker checks that the loaded runtime is LuaJIT 2.1 before loading LEB.
Clone `https://github.com/uta666XYZ/LastEpochBuilding.git` separately and
checkout commit `a97d388aca0da00907afb9d5a945c8f254a67b18`. The checkout
must contain `src/` and `runtime/` and have no source changes. The evaluator
copies those directories to a temporary location for each run because LEB
changes its working directory, writes logs, and holds global state. It calls
the original `HeadlessWrapper.lua` and `loadBuildFromXML`. LEB identifies
itself as application version 0.14.0. LEB and Lupa are MIT licensed; the
calculator code and game data stay outside this repository.

The supported input is a 1.4.7 Sentinel (class ID 2), no mastery (ID 0),
level 1–100, and only Fearless (node 49, at most eight points) and Armour Clad
(node 2, at most five points). Armour Clad needs five Fearless points. Total
points cannot exceed level minus one. No skills, equipment, idols, blessings,
unresolved IDs, or unsupported source sections are accepted. These checks
cover this subset only; they do not establish general game validity.
The calculator target `1_4` is used only for accepted 1.4.7 snapshots.
The output metrics are LEB `Life` as health points and `Armour` as armour rating.
They are calculator reference results, not a claim of in-game accuracy.
LEB initializes five default configuration values for boss, skill, minion,
Falconer, and resource calculations even with an empty `<Config/>`. The
evaluator verifies their exact loaded values and records them in
`evaluation.json`; the supported Sentinel has no skills or equipment to use
those settings. It also verifies that no item, skill, or equipment slot is
loaded.

The author-created fixtures in `tests/fixtures/` can be imported offline:

```bash
uv run --locked arpg-import https://www.lastepochtools.com/planner/ABC12345 --raw-file src/arpg_build_lab/evaluators/tests/fixtures/sentinel-baseline.json
uv run --locked --extra calculator arpg-evaluate artifacts/1.4.7/imports/<run-id> --leb-checkout <checkout>
uv run --locked --extra calculator python scripts/check_real_engine.py --leb-checkout <checkout>
```

The baseline gives health 206 and armour 0. The allocated fixture gives
health 236 and armour 16. The explicit check imports both, repeats the
baseline, and mutates canonical passive allocations while retaining the same
raw response to prove that the evaluator uses the snapshot.

Each success creates a new ignored `artifacts/1.4.7/evaluations/<run-id>/`
directory. `evaluation.json` is `BuildEvaluation` schema 1. It links
`snapshot.json`, `calculator-input.xml`, `calculator-output.json`, and
`diagnostics.json` by SHA-256. `snapshot_sha256` hashes UTF-8 JSON of the
evaluated snapshot with sorted keys, compact separators, no ASCII escaping,
and no NaN. This distinguishes passive changes even when `raw_sha256` stays
the same. `domain.evaluation.load()` validates the result, linked file hashes,
metric units, and source identity. A failed calculation does not publish a
complete result.
