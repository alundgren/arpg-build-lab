# Calculator adapters

Own conversion from our canonical build to a calculator's input, execution of
that calculator, and normalization into our evaluation contract. Domain types
stay independent of calculator-specific concepts.

Before choosing an integration, check the upstream license, supported game
versions, and headless execution path. Prefer an external executable or adapter
over copying implementation. Last Epoch Building and The Forge are candidates,
not current dependencies.

Record evaluator identity/version and game version with results. Retain raw
output in ignored artifacts for investigation. Expose unsupported calculations
and missing metrics explicitly; do not equate them with zero. Treat agreement
with a calculator as a check against that implementation, not proof of in-game
accuracy.
