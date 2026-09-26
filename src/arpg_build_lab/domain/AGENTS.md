# Canonical Last Epoch data

Own the versioned `BuildSnapshot`, build validity rules, and normalized
`BuildEvaluation` contract as they are implemented. Read
`../../../docs/agents/architecture.md` before defining persisted formats.

Prefer stable game IDs to display names. Distinguish schema version from game
version. Preserve unknown or unsupported information explicitly instead of
inventing values. Define missing metrics separately from a measured zero.

Keep this code independent of network access, LETools payloads, calculator
internals, and ML libraries. A schema change needs a compatibility decision and
validation of representative serialized records.
