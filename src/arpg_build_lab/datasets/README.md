# Sentinel passive point allocation datasets

`arpg-dataset` takes one existing 1.4.7 Sentinel import run and a local pinned
Last Epoch Building checkout. It checks the saved raw response, source content,
starting snapshot validity, and checkout before calculation. It enumerates Fearless node `49`
from 0 through 8 points, then Armour Clad node `2` from 0 through 5 points in
ascending order. Armour Clad needs at least five Fearless points, and the total
cannot exceed character level minus one. Zero-point nodes are omitted from
generated snapshots. The original starting snapshot is retained byte for byte.

```text
validated import run -> candidates(starting_snapshot) -> le_building.evaluate
                                             -> dataset manifest + retained evidence
```

At level 10, the command evaluates 19 passive point allocations. At levels 14
through 100, it evaluates 29. It has no random sampling or random seed. The
generator version and fixed configuration are in `manifest.json`.

With the default root, the run lives under
`artifacts/1.4.7/datasets/<run-id>/`. A shared root can be selected with
`ARPG_BUILD_LAB_ARTIFACTS_ROOT` or overridden with `--output-root`; see the
[development guide](../../../docs/agents/development.md#current-setup).
`starting_snapshot/` contains the original import snapshot, raw response, and
available provenance. Each
`candidates/NNN/` directory contains a generated snapshot, `BuildEvaluation`,
calculator input/output, and diagnostics. `manifest.json` schema 1 lists the
ordered candidate snapshot hashes and evaluation record hashes, exact starting snapshot
identity, game and record schema versions, generator configuration, evaluator
and calculator identity/configuration, and measured total calculation seconds.
The starting snapshot record also hashes retained provenance when the import supplied it.
The starting snapshot hash is a grouping key for later data splits. Each
candidate has its own snapshot hash because its passive point allocation is the
evaluated input. Schema 1 keeps the stable generator identifier
`sentinel_passive_space` independently of the Python module name.

`datasets.manifest.load(run)` checks the retained import against its raw
response, then verifies the complete ordered candidate set, source identity,
evaluation links, calculator identity, and all retained evaluation files. It
uses paths within the dataset run, so the run can be moved or the original
import removed. A failed generation has no accepted manifest. Rerun it in a
fresh directory.

For a repeatable offline example, use the committed synthetic level-10 starting snapshot:
These paths assume the default `./artifacts/` root.

```bash
uv sync --locked --extra calculator
uv run --locked arpg-import https://www.lastepochtools.com/planner/ABC12345 \
  --raw-file src/arpg_build_lab/evaluators/tests/fixtures/sentinel-baseline.json
uv run --locked --extra calculator arpg-dataset artifacts/1.4.7/imports/<run-id> \
  --leb-checkout <pinned-local-LEB-checkout>
```

Supply revision `a97d388aca0da00907afb9d5a945c8f254a67b18` as the local
checkout. The command prints progress, candidate count, health and armour
reference ranges with units, measured calculator time, and dataset path.
When using a shared root, pass the import path printed by `arpg-import` (or its
explicit path under that root) as the positional argument. The output setting
does not find existing imports automatically.
Results are calculator references. Related passive mutations of one synthetic
starting snapshot do not demonstrate generalization to untouched or complete builds.
