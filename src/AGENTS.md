# Application components

The `arpg_build_lab/` package contains the application and its ownership areas.

Keep dependencies directed toward `arpg_build_lab/domain/`. Domain code does not
import importers, build evaluators, ML code, or commands. Importers and build
evaluators exchange domain types and keep source- or calculator-specific
details local.
Use the component names and operation names in
`../docs/agents/architecture.md` for paths, public functions, and documentation.

Do not add code comments. Docstrings may explain behavior and contracts, never
work-item references or task-completion history. Put design explanations in the
owning module's README. Run the Ruff checks in the development guide.
Review its complexity advisories and long files or functions. Prefer a clearer
implementation over a lower count; advisories do not require splitting related
code.

Co-locate tests and small fixtures with the component they exercise. Add the
command entry point when there is behavior to run. Add a new work area only
when a concrete feature gives it a responsibility.
