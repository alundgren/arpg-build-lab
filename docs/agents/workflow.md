# GitHub work

Use the `github-use` skill when available. Use `gh` for GitHub reads and writes,
including issues, labels, pull requests, and checks. Keep repository targets
explicit outside the checkout. For multiline issue or PR text, pass a file with
`--body-file`.

## Commits and PR titles

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
for commit messages and PR titles: `<type>[optional scope]: <description>`.
Choose the type that describes the change, such as `feat`, `fix`, `docs`,
`test`, `perf`, `refactor`, `build`, or `ci`. Use `!` or a `BREAKING CHANGE:`
footer when the change breaks compatibility, and explain the consequence.

For example, `feat(import): save builds for repeatable experiments` describes
an outcome; `docs: define PR review and testing guidance` describes this policy.

## PR descriptions

Use [the PR template](../../.github/pull_request_template.md). Keep the body in
two parts:

1. **Summary** stays visible. Explain the intended outcome and why a human
   should care. Describe the problem solved or what someone can now do. Keep
   material limitations visible and link the requested work, using `Closes #N`
   when appropriate. A shorter inventory of changed files or functions does
   not explain the value.
2. **Evidence** contains the agent's supporting work inside
   `<details><summary>Evidence</summary> ... </details>`. Omit the `open`
   attribute so it is collapsed by default. Leave blank lines around Markdown
   inside the block. Keep review records and agent attribution here too.

Make the evidence specific enough for a reviewer to check:

- Connect the requested outcome and acceptance criteria to observed results.
  Include relevant failure cases and limitations of the evidence.
- Explain how the change follows the applicable architectural guidance. Point
  to relevant modules, dependencies, data contracts, and source locations. State
  any justified exceptions. A claim that "architecture was followed" is not
  evidence.
- Follow [testing guidance](development.md#testing-and-validation). Name the
  behavior checked, the test level, commands or tools, and actual results. Link
  tests, CI runs, or other inspectable artifacts. Distinguish automated tests
  from one-off checks and checks performed from checks still planned. Explain
  any relevant checks that could not be completed.

Use evidence suited to the task. Prefer ASCII diagrams for algorithms,
processes, and data flow. For visual changes, screenshots or recordings can
show the result. Benchmarks, test output, and observed user journeys can answer
other review questions. Include only material that helps assess the outcome.

To keep an image inside the folded section, place a reference such as
`![Imported build summary](./evidence.png)` there in the body file, then upload
the same file with `gh pr create --attach` or `gh pr edit --attach`. For example:

```bash
gh pr edit NUMBER --repo alundgren/arpg-build-lab \
  --body-file /tmp/pr-body.md --attach ./evidence.png
```

The CLI replaces the file reference with the uploaded asset URL. Without a
reference in the body, it appends the attachment instead. Inspect the published
body to confirm the evidence appears inside the collapsed section. GitHub's
[collapsed-section guide](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections)
describes the markup.

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

Use native GitHub sub-issues and dependencies when planning work that needs
them. Implement changes through PRs using the guidance above.
