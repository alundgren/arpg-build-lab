# Development and artifacts

## Current setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
`uv python install` and `uv sync --locked` from the repository root.
The committed `.python-version` selects Python 3.14 for development and CI;
`requires-python` sets 3.14 as the minimum supported version.
Run routine validation through the same check runner as CI:

```bash
python3 scripts/check.py
```

The runner synchronizes the locked environment, then runs lint, formatting,
complexity advisories, tests, and the package build. It prints one `OK` summary
when required checks pass. Complexity findings remain visible as concise
advisories. Other command output appears only on failure, with the failing
check's exit code preserved. Tests buffer output until a failure, formatting
failures show the required diff, and build failures include backend diagnostics.

Use this runner by default so successful command logs do not fill agent context.
To investigate an individual check, run its command directly:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check --diff .
uv run --locked python -m unittest discover -s src/arpg_build_lab/importers/tests --buffer
uv build
```

[Ruff](https://docs.astral.sh/ruff/) provides linting, import sorting, and Python
formatting. It comes from Astral, which also maintains uv, and supports Python
3.14. It is a development dependency pinned by `uv.lock`. Use the formatter's
defaults and the lint rules selected in `pyproject.toml`. Apply safe lint fixes
with `uv run --quiet --locked ruff check --fix --quiet .`, then run
`uv run --quiet --locked ruff format --quiet .`.
Review the changes and rerun the checks. Formatting choices belong to Ruff.
The code-comment ban and rules against work-item references and task-completion
narratives are review rules; Ruff does not enforce those repository policies.

Run complexity advisories separately:

```bash
uv run --quiet --locked ruff check --select C901,PLR0912,PLR0915 --exit-zero --quiet --output-format concise .
```

Ruff reports functions exceeding its defaults of 10 for cyclomatic complexity,
12 branches, or 50 statements. These findings prompt review and do not fail CI.
Keep the concise findings visible even when required checks pass.
They measure control flow and statements, not physical file length. Review long
files and functions for responsibilities that would be clearer apart. Simplify
when it improves understanding; keep related code together when splitting it
would add indirection. Do not split code just to lower a count or hide findings
with suppressions. Explain material retained complexity in the PR's Evidence
section. Keep these advisories separate from required lint and formatting checks.

The runtime uses the Python standard library; `uv.lock` records the project
environment. `uv build` creates the source distribution and wheel using
[`uv_build`](https://docs.astral.sh/uv/concepts/build-backend/), which fits our
pure Python package and standard `src/` layout. The build requirement includes
an upper version bound following uv's guidance. Python 3.14 was the stable
series when selected on 2026-09-26; no current dependency requires support for
an older interpreter. Both distributions include our license, third-party
notices, and the lookup data's original license.

Request one identified LETools planner build with
`uv run --locked arpg-import https://www.lastepochtools.com/planner/<id>`.
To replay a previously saved response without network access, add
`--raw-file artifacts/<version>/imports/<run-id>/raw.json` to that command.
Each import writes `raw.json`, `snapshot.json`, and `provenance.json` to a new
run directory under `artifacts/<version>/imports/`. The command prints the path.
An unknown or conflicting game version goes under `artifacts/unknown/`.

For the supported 1.4.7 Sentinel subset, install the optional calculator runtime
with `uv sync --locked --extra calculator`. Supply a local checkout of Last Epoch
Building at revision `a97d388aca0da00907afb9d5a945c8f254a67b18` to
`arpg-evaluate artifacts/1.4.7/imports/<run-id> --leb-checkout <checkout>`.
On Apple Silicon macOS, install Homebrew `luajit` and `pkg-config`, then run
`LUPA_NO_BUNDLE=true uv sync --locked --extra calculator --no-binary-package lupa --reinstall-package lupa`
to build Lupa against LuaJIT 2.1; the prebuilt ARM64 wheel omits LuaJIT.
See `src/arpg_build_lab/evaluators/README.md` for supported input and synthetic
examples. `python3 scripts/check.py` remains offline. The explicit engine check
is `uv run --locked --extra calculator python scripts/check_real_engine.py --leb-checkout <checkout>`;
CI runs it on Linux and macOS.

Keep application code in Python until a concrete problem justifies another
language. External tools and libraries may use other runtimes. Document any
runtime needed by an integration when it is introduced.

## Testing and validation

Prefer tests in this order:

```text
End-to-end tests
  |  Exercise a user journey through the actual application entry point.
  v
Integration or component tests
  |  Check collaborating parts and focused failure cases.
  v
Pure unit tests
     Check isolated logic when that is the useful place to verify it.
```

Start with the complete outcome a user needs. Add smaller tests where they
provide useful evidence or diagnose important failures. This preference does
not require duplicating every assertion at every level.

Derive expected results from requirements and domain facts. Test desired,
observable behavior. Avoid assertions that merely preserve today's output,
private helper calls, incidental ordering, or implementation details. Exact
values and regression tests are useful when they protect an intended contract.
For example, a missing affix roll must remain unknown rather than becoming
zero; that matters more than which helper parsed it.

Use real collaborating components where practical. Isolate external services
when needed for repeatable checks. An end-to-end importer test can run the
installed command against a saved or synthetic response and verify that the
saved build reloads without losing required information. Tests must respect
the LETools direct-request policy; default checks make no live requests.

Judge validation by what it establishes about correctness, performance,
usability, reliability, and the task's other requirements. Coverage percentages
and test counts are not goals. Choose evidence for the actual risks, such as a
benchmark for a performance claim or an observed user journey for usability.
Record what ran, its result, and what it cannot establish in the PR's Evidence
section. Do not add application tests for prose or template-only edits; inspect
the changed text, links, and formatting instead.

## Platform agreement

Development and small CPU checks must work on a Linux VM and an Apple Silicon
Mac. Add meaningful Linux/macOS checks with the first runnable code. Avoid
absolute paths, macOS-only shell utilities, and mandatory GPU imports in normal
development commands.

Larger training runs may require the Mac GPU. Native Apple GPU acceleration uses
Metal, for example [PyTorch MPS](https://docs.pytorch.org/docs/stable/notes/mps.html).
CUDA requires supported NVIDIA hardware and is not the native Mac training path.
See [NVIDIA's platform requirements](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/).
The ML framework remains undecided. CPU runs provide a portable baseline;
record the device/backend with experiment results.

## Artifact storage

Use `artifacts/<game-version>/<kind>/<run-id>/` once real data exists. Kinds may
include imports, datasets, models, and runs. The contents are ignored by Git.
Use an explicit `unknown` bucket while investigating an import whose game
version is unavailable; do not treat it as version-qualified training data.

Record enough metadata to reproduce a dataset or experiment: game/schema
versions, source build identity and provenance, generator and build evaluator
versions, seed, feature definition, split, configuration, relevant dependency
versions, device, and code revision. Add content hashes where they are needed
to identify exact inputs. A declared seed alone does not prove reproducibility.

Commit small synthetic or permission-checked fixtures near their owning tests.
Commit selected charts and measured summaries in human experiment reports.
Keep personal saves, raw imports, bulk datasets, model weights, and checkpoints
out of Git. These rules also apply to documentation examples.

Check the license before copying upstream code or substantial data. MIT covers
our repository work; it does not relicense Last Epoch assets or third-party
material. Record source, permission/license, and any required attribution for
redistributed examples. Prefer permissive dependencies and keep calculator
integration in the build evaluator that uses it.

## Documentation and search

Agent documents are task-specific references. Human documents live under
`docs/humans/`, which `.ignore` excludes from default ripgrep discovery/search.
For a task explicitly involving those documents, use a targeted command such as
`rg --no-ignore 'validation' docs/humans`. The search rule does not restrict file
access or change what Git tracks.

Keep the root README to its image and short project introduction. Setup
instructions belong here. Learning reports belong in the human documentation.
