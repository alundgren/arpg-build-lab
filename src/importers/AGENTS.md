# Build importers

Own input recognition, external payload validation, and translation into the
canonical domain model. External field names and source quirks stay here.

LETools planner URLs are the first source. Work only with user-supplied URLs or
a small explicitly selected validation corpus. Verify current endpoint behavior
and usage expectations before implementation. Do not crawl bulk content or
bypass authentication, paywalls, anti-bot measures, or other restrictions.
Maxroll is outside current scope.

Keep raw responses in ignored `artifacts/` output for diagnosis. Commit only
small synthetic or permission-checked fixtures, with provenance. Keep automated
checks independent of live services. Validate malformed payloads and missing
game-version information as well as a successful import.
