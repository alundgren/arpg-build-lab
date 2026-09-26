# Continue the project

The repository has a runnable LETools importer, versioned `BuildSnapshot` and
`BuildEvaluation` records, a narrow Last Epoch Building evaluator, offline
tests, and Linux/macOS CI. Setup and command use are in `development.md`.

Choose future work from the active GitHub planning documents. Everyday component
work should use the relevant local instructions and contracts. Keep planning
status in GitHub and document current capabilities here.

## Next useful outcome

The importer is under `src/arpg_build_lab/importers/`, the build records are
under `src/arpg_build_lab/domain/`, and the supported 1.4.7 Sentinel evaluator
is under `src/arpg_build_lab/evaluators/`. The next task should come from active
GitHub planning. Other build versions and content need explicit compatibility
checks before evaluation.

Use synthetic or permission-checked fixtures for automated checks. Live network
access is not required for the default tests. Data generation, ML, search, and
UI remain future work.
