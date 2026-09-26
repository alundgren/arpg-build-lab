# ML experiments

Select ML frameworks and add their dependencies with the first experiment. Read
`../docs/agents/architecture.md` when defining dataset exchange and
`../docs/agents/development.md` when adding runtime dependencies or artifacts.

Use versioned datasets for reproducible experiments. Reuse canonical domain
types and validity rules directly when needed; Python modules do not require
file exchange. Keep ML packages out of the domain and importer dependency
trees. Small CPU checks must run on Linux and macOS; larger training may use
Metal acceleration on the Mac.

Use established ML vocabulary from the architecture guide: features are inputs,
regression targets are continuous numeric outputs, and predictions are ML model
estimates. A build evaluator runs a calculator; model evaluation measures an
ML model's predictive quality.

Start with an intentionally narrow prediction target and useful baselines.
Record the dataset, feature definition, split, random seed, model, parameter count,
training time, train/validation errors, and worst predictions. When mutations
share a starting snapshot, make the split policy explicit so related builds do not
accidentally make validation look better than it is.

Keep game versions separate unless a named experiment deliberately measures
version shift. Compare optimized candidates with a build evaluator before
presenting predicted gains as verified gains.

Keep generated datasets, checkpoints, and run output under `artifacts/`.
Write human explanations and failed-experiment reports in
`docs/humans/experiments/` when the task calls for them. Put rules needed by
current code in its contracts or local instructions.
