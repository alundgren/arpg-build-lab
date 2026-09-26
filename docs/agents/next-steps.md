# Continue the project

The repository has a runnable LETools importer, a versioned `BuildSnapshot`,
offline tests, and Linux/macOS CI. Setup and command use are in `development.md`.

The full remaining handoff lives in
[epic #1: Explore and optimize Last Epoch builds while learning traditional ML](https://github.com/alundgren/arpg-build-lab/issues/1).
It is deliberately unrefined. Consult it when planning future scope; everyday
component work should use the relevant local instructions and contracts.

## Next useful outcome

The import path is implemented under `src/arpg_build_lab/importers/`; the
snapshot contract is under `src/arpg_build_lab/domain/`. The next task should
come from the epic after this importer is reviewed and merged. The current
snapshot has source IDs and unresolved translations, so calculator work must
check compatibility before treating it as an evaluation input.

Use synthetic or permission-checked fixtures for automated checks. Live network
access must not be required for the default tests. Leave build evaluator
integration, data generation, ML, search, and UI in the epic for later work.
