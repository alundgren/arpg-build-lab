# Continue the project

The repository contains the agreed documentation and folder scaffold. There is
no runnable application, dependency installation, or test suite yet.

The full remaining handoff lives in
[epic #1: Explore and optimize Last Epoch builds while learning traditional ML](https://github.com/alundgren/arpg-build-lab/issues/1).
It is deliberately unrefined. Consult it when planning future scope; everyday
component work should use the relevant local instructions and contracts.

## Next useful outcome

Refine the smallest import task when implementation resumes. Its intended
result is importing
`https://www.lastepochtools.com/planner/AL0rXWDz`, writing a canonical
`BuildSnapshot`, and printing a concise human-readable summary. The command
name in the epic is illustrative until tooling exists.

Start in `src/importers/` to verify the actual endpoint, payload, and usage
expectations. Define the minimum evidence-backed representation in
`src/domain/`, including how missing version information is handled. Introduce
the TypeScript tooling and meaningful Linux/macOS checks with this work.

Use synthetic or permission-checked fixtures for automated checks. Live network
access must not be required for the default tests. Leave evaluator integration,
data generation, ML, search, and UI in the epic for later work.
