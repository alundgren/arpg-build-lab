# BuildSnapshot schema 1

`snapshot.json` is a UTF-8 JSON object with `schema_version: 1`. It records the
character's class and mastery IDs and level, passive and skill selections,
equipment, positioned idols, blessings, provenance, and import diagnostics.
Unknown values use JSON null. A selected node with zero points stays zero.
This record describes the imported build; it does not assert game validity or
calculate stats.

`game_version` is the version established by the importer, or null when it
cannot establish one. `version_evidence` retains the source's version fields
and their original text. The importer decides which fields establish a version;
the domain validates their string or null values without requiring source field names.
`importer_version` tracks parser behavior. `lookup_revision` identifies the
table used for translated item and affix IDs. A translation is not proof that
the item or affix has the same meaning in this game version.

The importer stores source IDs with a LETools namespace and stores unrecognized
item, affix, and blessing IDs in `unresolved`. Translated items and blessings
expose `base_type_id`, `sub_type_id`, and `unique_id`; lookup-only metadata
stays in `lookup_extra`. Item `source_fields` retain source-specific properties,
including optional rolls and item metadata. `unsupported_sections` lists data
sections that the importer has not normalized. The full original response is
always available at the relative `raw_path`, guarded by `raw_sha256`.

`BuildSnapshot.from_dict` accepts only schema 1 and validates nested record types.
`load()` also verifies the colocated raw response hash. A future schema change
must define how existing records are read or migrated before changing this
format.
