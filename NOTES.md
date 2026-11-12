# NOTES — store-layer (P8 Store)

NOTES.md — open questions, divergences and decisions for P8 Store.

## Open questions
- (none)

## Divergences from v1.2.1 specification
- (none)

## Decisions
- The record is stored as a JSON string in SQLite to preserve the
  exact payload.
- The signature covers the raw 32-byte SHA-256 digest, matching P4.
- verify_store enforces the same chain logic as P4.
