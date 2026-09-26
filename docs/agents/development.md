# Development and artifacts

## Current setup

This scaffold contains documentation and ownership directories. There are no
runtime dependencies, package manifests, executable commands, tests, or CI yet.
Introduce those with the first runnable importer. Do not add placeholder code
just to give a check something to run.

Introduce Python tooling with the first runnable importer. Select the supported
Python version and dependency manager then, and pin dependencies with a
lockfile. Add ML dependencies with the first experiment; ordinary domain and
importer development must not require them.

Keep application code in Python until a concrete problem justifies another
language. External tools and libraries may use other runtimes. Document any
runtime needed by an integration when it is introduced.

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
versions, source build identity and provenance, generator and evaluator
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
redistributed examples. Prefer permissive dependencies and external adapters.

## Documentation and search

Agent documents are task-specific references. Human documents live under
`docs/humans/`, which `.ignore` excludes from default ripgrep discovery/search.
For a task explicitly involving those documents, use a targeted command such as
`rg --no-ignore 'validation' docs/humans`. The search rule does not restrict file
access or change what Git tracks.

Keep the root README to its image and short project introduction. Setup
instructions belong here. Learning reports belong in the human documentation.
