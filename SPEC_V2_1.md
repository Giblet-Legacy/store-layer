# SPEC_V2_1 — store-layer (P8 Store v2.1)

SPEC_V2_1.md — the layer specification for P8 Store v2.1.

Function:
    Authoritative specification for store_v2_1.py. v2.1 is added over
    store_v2.py under the Immutable Rule; store_v2.py, SPEC_V2.md and
    test_store_v2.py are frozen at 2.0.0 and never edited. v2.1 closes
    two gaps found in the laptop audit of v2.0.0. Everything not named
    here behaves exactly as SPEC_V2.md 2.0.0.

Layer:     P8 — Store
Depends:   P8 store_v2 2.0.0 (public API only); P4 Ledger v2 via v2
Consumed:  P9 Substrate, SC-OS, The Cockpit
Version:   SPEC 2.1.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 0. Why v2.1 (gaps found in v2 laptop audit, 2026-11-12)
- G1: v2 verify_store raises RecursionError when a stored record is
  deeply nested JSON (e.g. 100000 nested lists). SPEC_V2 §4.7 says it
  never raises for database content. P4 v2 verify_ledger has the same
  fault on a .jsonl file (reported in NOTES; P4 is not edited here).
- G2: SPEC_V2 §4.5 names the parameter `hash`; v2 names it `hash_hex`,
  so get_by_hash(db, hash=h) raises TypeError.

## 1. The Store Rule (unchanged)
v2.1 contains no hashing, signing, chain or SQL logic. It calls only
public names of store_v2. P4 v2 remains the sole judge.

## 2. Function Contracts
Passed through unchanged from store_v2 (same objects):
init_db, export_jsonl, append_entry, get_entry, get_by_signer.

### 2.1 get_by_hash(db_path: str, hash: str) -> dict | None
- As SPEC_V2 §4.5. The second parameter is named `hash`, so both
  positional and keyword calls work.

### 2.2 verify_store(db_path: str, public_key) -> bool
- As SPEC_V2 §4.7, plus: if the store's content cannot be decoded
  because it is nested too deeply (RecursionError), the store is
  judged as unreadable: P4 v2 is asked to verify an empty image, so a
  wrong key type still raises TypeError and otherwise the result is
  False.
- Never raises for database content.

## 3. Invariants (each is a test)
- I5: store_v2_1.py imports no name beginning with "_" from store_v2
  or ledger_v2, and no hashing or crypto module.
- I6: store_v2.py, test_store_v2.py and SPEC_V2.md are byte-unchanged
  since V2.sha256 was pinned.
- I1–I4 of SPEC_V2 still hold (their tests still run).

## 4. Imports
store_v2 resolves from os.path.dirname(__file__), never the CWD.

## 5. Known gaps carried forward
- append_entry on a deeply nested store raises RecursionError (store
  unchanged). Not converted to ValueError in 2.1; see NOTES.
