# Application components

This directory reserves ownership areas; runnable Python code and tooling
will arrive with the first importer.

Keep dependencies directed toward `domain/`. The domain does not import source
adapters, calculator adapters, ML code, or a future command/UI layer. Sibling
adapters communicate through the canonical representation rather than each
other's internals.

Co-locate tests and small fixtures with the component they exercise. Add the
command entry point when there is behavior to run. Add a new work area only
when a concrete feature gives it a responsibility.
