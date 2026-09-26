# LETools importer contract

The command accepts exactly one `https://www.lastepochtools.com/planner/<id>`
URL. For a direct import it requests only `/api/public/build_data/<id>`, with a
20-second timeout, a browser-compatible User-Agent, and redirects disabled.
The optional `--raw-file` reads a saved response and makes no HTTP request.
Both paths call `normalize()` and save a new run; they never overwrite an old
one.

The snapshot includes class, mastery, level, passive selections, skill trees,
equipment, idol coordinates, and blessings. Numeric IDs may lack names. Item
and affix IDs absent from the pinned maps remain LETools IDs and appear in the
summary. Blessings use item ID translation and report unresolved blessing IDs
separately. All original item fields, including `ir`, `ur`, and optional affix
roll `r`, stay in `source_fields`. The raw response preserves progression,
weaver trees, combat settings, quests, and any future fields. The importer names
unsupported response and `data` sections in the summary.

Malformed JSON and structural errors fail before an artifact is saved. The game
version is established only when `created_for_build`, `data_version`, and
`data.dataVersion` all exist as version strings and agree. Missing
or conflicting game versions save under `artifacts/unknown/` and show the
original version fields in the summary. An offline replay records its import
time and input path; the original fetch time is not inferred.
