# Build evaluators

Own conversion from `BuildSnapshot` to a calculator's input, execution of
that calculator, and recording its results in `BuildEvaluation`. Domain types
stay independent of calculator-specific concepts.

The current integration calls a pinned Last Epoch Building checkout for a
limited 1.4.7 Sentinel subset. Keep its source and game data outside the
package and its Lupa runtime optional for ordinary importing. Read the local
README for supported inputs, execution, and retained output. Check upstream
license, game version, and headless entry point before expanding support or
adding another calculator.

Record build evaluator identity/version and game version with results. Retain raw
output in ignored artifacts for investigation. Expose unsupported calculations
and missing metrics explicitly; do not equate them with zero. Treat agreement
with a calculator as a check against that implementation, not proof of in-game
accuracy.
