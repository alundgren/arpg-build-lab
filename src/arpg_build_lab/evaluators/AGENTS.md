# Build evaluators

Own conversion from `BuildSnapshot` to a calculator's input, execution of
that calculator, and recording its results in `BuildEvaluation`. Domain types
stay independent of calculator-specific concepts.

Before choosing an integration, check the upstream license, supported game
versions, and headless execution path. Keep the integration in a build evaluator
module and prefer calling the external tool over copying its implementation.
Last Epoch Building and The Forge are candidates, not current dependencies.

Record build evaluator identity/version and game version with results. Retain raw
output in ignored artifacts for investigation. Expose unsupported calculations
and missing metrics explicitly; do not equate them with zero. Treat agreement
with a calculator as a check against that implementation, not proof of in-game
accuracy.
