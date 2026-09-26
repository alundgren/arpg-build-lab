# Development checks

Own repository validation commands and their output. Use Python's standard
library and the locked project tools. Keep these scripts outside the application
package and portable across Linux and macOS.

Successful checks should produce a brief result. Preserve failure diagnostics
and failed exit codes. Complexity advisories remain visible without failing the
run. Validate output and exit behavior with successful and failing commands.
