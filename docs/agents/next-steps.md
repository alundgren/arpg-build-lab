# Continue the project

The repository has a runnable LETools importer, a versioned `BuildSnapshot`,
offline tests, and Linux/macOS CI. Setup and command use are in `development.md`.

Choose future work from the active GitHub planning documents. Everyday component
work should use the relevant local instructions and contracts. Keep planning
status in GitHub and document current capabilities here.

## Next useful outcome

The import path is implemented under `src/arpg_build_lab/importers/`; the
snapshot contract is under `src/arpg_build_lab/domain/`. The next task should
come from the active planning documents. The current snapshot has source IDs
and unresolved translations, so calculator work must check compatibility before
treating it as an evaluation input.

Use synthetic or permission-checked fixtures for automated checks. Live network
access must not be required for the default tests. Leave build evaluator
integration, data generation, ML, search, and UI for later work.
