# NOTES — store-layer (P8 Store)

NOTES.md — open questions, divergences and decisions for P8 Store.

## Open questions
- get_by_signer and the signer index: P4 refuses foreign keys, so one
  store has one signer. Keep only if P9 Substrate will merge stores.
  Otherwise cut in v2.1.
- O(n) append: at what store size does it hurt on the S24? Measure
  before optimising.
- Consumers (P9, SC-OS, The Cockpit) should move to store_v2_1.
- P4 ledger_v2.verify_ledger raises RecursionError on a deeply nested
  .jsonl line, breaking its own "never raises for file content". Fix
  belongs in a P4 layer (ledger-layer), not here.
- append_entry on a deeply nested store raises RecursionError, not
  ValueError. Convert in a later layer? Needs care: a deeply nested
  *new* record is an input error (TypeError-like), not a bad store.

## Divergences from SPEC.md v1.0.0 (made in SPEC_V2.md 2.0.0)
- verify_store: empty store is now False (was True).
- verify_store: never raises for content (v1 raised with no table).
- All functions except init_db/verify_store raise FileNotFoundError on
  a missing path instead of creating an empty file.
- init_db failure is sqlite3.OperationalError (v1 spec said IOError).
- Records stored in insertion order (v1 sorted keys).

## Decisions
- v1: record stored as a JSON string to preserve the exact payload.
- v1: signature covers the raw 32-byte SHA-256 digest, matching P4.
- v2: P8 holds rows; P4 v2 judges them. No private P4 imports.
- v2: verify_store always calls P4, even on an unreadable store (empty
  image), so P4 alone raises on a wrong key type.
- v2: database opened with mode=rw via Path.as_uri() so SQLite can
  never create a file and the path works on Windows.
- v2.1: gaps in frozen v2 closed by a layer over store_v2's public
  API, not by editing it. v2 pinned by V2.sha256.
- v2.1: on RecursionError, verify_store asks v2 (and so P4) to verify
  an absent path, so P4 alone still decides wrong-key TypeError.
- v2: test headers are one-line numbered comments to keep 36 items
  readable; code files keep the block header.
