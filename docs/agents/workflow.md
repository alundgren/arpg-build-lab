# GitHub work

Use the `github-use` skill when available. Use `gh` for GitHub reads and writes,
including issues, labels, pull requests, and checks. Keep repository targets
explicit outside the checkout. For multiline issue or PR text, pass a file with
`--body-file`.

## Labels

| Label | Meaning |
| --- | --- |
| `epic` | Non-executable root organizing a larger outcome |
| `needs-refinement` | Non-executable work whose unknowns need planning |
| `ready-for-agent` | Executable work an agent can start without a human |
| `ready-for-human` | Executable work requiring focused human action |
| `claimed` | An implementation agent has taken ownership of eligible work |

Use one planning classification per issue: `epic`, `needs-refinement`,
`ready-for-agent`, or `ready-for-human`. `claimed` is separate execution state;
create the label during repository setup but apply it only during implementation.
Re-read eligibility and existing claims before claiming, then verify the label.
Never remove another worker's claim or treat the label alone as proof of your
own ownership.

The initial project epic preserves the unrefined handoff. Its `epic` label keeps
it out of direct implementation selection. Its body states that it has not been
refined; do not also add `needs-refinement` or a readiness label.

When later planning is requested, use native GitHub sub-issues and dependencies
where appropriate. The scaffold creates no implementation leaves or dependency
links. The initial commit goes directly to `main`; future work follows the
workflow requested for that task.
