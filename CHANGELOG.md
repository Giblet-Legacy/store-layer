# CHANGELOG — store-layer (P8 Store)

CHANGELOG.md — build history for P8 Store, latest entry at top.

## [v2.0.0] — 2026-11-12

### Good
- `store_v2.py` added beside v1 to SPEC_V2.md 2.0.0. v1 untouched.
- P4 Ledger v2 is now the sole authority: every append and verify runs
  through `ledger_v2.append_entry` / `verify_ledger` over the store's
  .jsonl image. No hashing or signing code in P8.
- I1 holds: a v2 store's export is byte-identical to the P4 v2 ledger
  of the same appends.
- I2 holds: v1 databases verify under v2 and v2 can extend them. This
  confirms v1's hashing always matched P4.
- New: `export_jsonl`, `get_by_hash`, `get_by_signer`, hash and signer
  indexes, write lock on append, rollback on any error.
- Imports resolve from `__file__`; v2 works from any directory.
- `V1.sha256` pins store.py, test_store.py and SPEC.md (I4).
- 42/42 v2 tests pass; v1 still 7/7.

### Bad
- v1 audit gaps (fixed in v2, not in v1): reimplemented P4's chain
  rules; appended onto unverifiable stores; accepted records P4
  rejects; verified an empty store as True; raised on a file with no
  table; created empty files on bad paths; CWD-relative imports.
- README showed 0.0.0-dev after the v1 freeze. Corrected.

### Ugly
- append_entry is O(n): P4 re-verifies the whole store on each append.
- Every append/verify writes the full store to a temp file.
- get_by_signer is all-or-nothing: P4 refuses foreign keys, so a store
  only ever has one signer. Kept pending a P9 decision (see NOTES).
- verify_store returns a bare bool, so it cannot say what broke.

## [v1.0.0] — 2026-11-12

### Good
- `store.py` implemented to SPEC v1.0.0.
- 7/7 pytest tests pass.
- SQLite-backed ledger mirroring P4's .jsonl format.
- Enforces the same hash chain and signature rules as P4.

### Bad
- (none)

### Ugly
- (none)

## [scaffold]

### Good
- Repository scaffolded: `Giblet-Legacy/store-layer` created for P8.
- Depends on P1 Envelope v2.0.0 and P4 Ledger v2.0.0.

### Bad
- (none)

### Ugly
- (none)
