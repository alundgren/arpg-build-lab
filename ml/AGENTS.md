# ML experiments

Use Python where its ecosystem helps. Frameworks and Python tooling are not yet
selected. Add them with the first experiment. Read
`../docs/agents/architecture.md` when defining dataset exchange and
`../docs/agents/development.md` when adding runtime dependencies or artifacts.

Consume versioned files exported by the TypeScript components. Keep ML packages
out of the domain and importer dependency trees. Small CPU checks must run on
Linux and macOS; larger training may use Metal acceleration on the Mac.

Start with an intentionally narrow prediction target and useful baselines.
Record the dataset, feature definition, split, seed, model, parameter count,
training time, train/validation errors, and worst predictions. When mutations
share a seed build, make the split policy explicit so related builds do not
accidentally make validation look better than it is.

Keep game versions separate unless a named experiment deliberately measures
version shift. Compare optimized candidates with a reference evaluator before
presenting predicted gains as verified gains.

Keep generated datasets, checkpoints, and run output under `artifacts/`.
Write human explanations and failed-experiment reports in
`docs/humans/experiments/` when the task calls for them. Put rules needed by
current code in its contracts or local instructions.
