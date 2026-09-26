# What one import gives us

The saved level-100 Necromancer example contains 21 selected passive nodes
with 113 points and five skill trees. LETools calls its class `3` and mastery
`1`. These are source facts. The importer keeps those values and the complete
raw response so we can check a later interpretation against the original.
The user-requested source was
`https://www.lastepochtools.com/planner/AL0rXWDz`, fetched on 2026-09-26.
Its ignored local raw response has SHA-256
`559d73954c0338388a5ffff27cef784424a7cb4108e5ae1275f84fe9d1cc086a`.
The planner may change; these observations refer to that saved response.

`BuildSnapshot` is our shared build representation. It groups the character,
allocations, items, idols, and blessings under schema version 1. It retains
LETools IDs where we cannot yet identify a stable game ID. Three item IDs in
this example have no match in the pinned lookup table. Their translation is
null, rather than a guessed item. An absent affix roll is also null; it does
not mean a roll of zero.

For ML, we could later turn a snapshot into **features**: inputs such as passive
point counts or item affix tiers. A **build evaluator** would run a calculator
to supply a **regression target**, such as damage. An **ML model** would learn
from paired features and targets, then make **predictions** for other builds.
For example, if the calculator reports 1,000 damage and the model predicts 900,
the target is 1,000 and the prediction is 900. **Model evaluation** would measure
errors like this on held-out examples; calculator results are references that
can themselves be wrong.

These ML steps remain future work. Keeping the source response, game version,
and missing values lets us inspect mistakes before training on them.
