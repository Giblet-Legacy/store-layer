# SPEC_V2 — store-layer (P8 Store v2)

SPEC_V2.md — the layer specification for P8 Store v2.

Function:
    Authoritative specification for store_v2.py. v2 is added beside
    v1 under the Immutable Rule; store.py v1 is never edited. v2 makes
    P4 Ledger v2 the sole authority on chain, hash, signature and
    record form. P8 holds rows and indexes; P4 judges them.

Layer:     P8 — Store
Depends:   P1 Envelope v2, P4 Ledger v2 (public API only)
Consumed:  P9 Substrate, SC-OS, The Cockpit
Version:   SPEC 2.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 0. Why v2 (gaps found in v1 audit, 2026-11-12)
- v1 reimplements the chain rules instead of consuming P4 (drift risk).
- v1 appends onto a store that does not verify. P4 refuses.
- v1 accepts records P4 rejects (non-dict, NaN, tuples, non-str keys).
- v1 verify_store returns True on an empty store. P4 returns False.
- v1 verify_store raises on a file with no ledger table.
- v1 get_entry/append_entry create an empty file on a bad path.
- v1 import paths resolve from the working directory, not the file.
- v1 has no lookup by hash or signer, and no indexes for them.
- v1 stores records key-sorted; P4 keeps insertion order, so exports
  are not byte-identical to P4 ledgers.

## 1. The Store Rule (v2)
P8 v2 contains no hashing, signing or chain logic. Every append and
every verify passes through P4 v2's public API (append_entry,
verify_ledger) over the store's .jsonl image (§3). A store is valid
if and only if its .jsonl image verifies under P4 v2.

No private P4 function (leading underscore) is imported.

## 2. Database Schema
Table unchanged from v1, so v1 databases are readable by v2.

    CREATE TABLE IF NOT EXISTS ledger (
        seq INTEGER PRIMARY KEY,
        prev TEXT NOT NULL,
        record TEXT NOT NULL,
        signer TEXT NOT NULL,
        hash TEXT NOT NULL,
        signature TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ledger_hash ON ledger(hash);
    CREATE INDEX IF NOT EXISTS ledger_signer ON ledger(signer);

`record` is stored as compact JSON (separators ",", ":"), ASCII,
keys in insertion order, exactly as it appears in a P4 v2 line.

## 3. The .jsonl image
For each row in seq order, one line:
    json.dumps({"seq", "prev", "record", "signer", "hash",
                "signature"} in that key order,
               separators=(",", ":")).encode("ascii") + b"\n"
where record is json.loads of the stored text (order preserved).
An empty store's image is b"".

## 4. Function Contracts

All functions except init_db and verify_store raise
FileNotFoundError if db_path does not exist, and never create a file.

### 4.1 init_db(db_path: str) -> None
- Creates the table and both indexes if absent. Idempotent.
- Safe to run on a v1 database (adds indexes only).
- Failure: sqlite3.OperationalError if the path is not writable.

### 4.2 export_jsonl(db_path: str) -> bytes
- Returns the store's .jsonl image (§3).
- FileNotFoundError if db_path does not exist. Never creates a file.

### 4.3 append_entry(db_path: str, record: dict, private_key) -> dict
- FileNotFoundError if db_path does not exist. Never creates a file.
- Takes a write lock (BEGIN IMMEDIATE) for the whole operation.
- Writes the image to a private temp file and calls
  ledger_v2.append_entry on it. All P4 errors pass through unchanged:
  TypeError (key type, record type, non-plain JSON) and ValueError
  (store does not verify under this key).
- Inserts the entry P4 returned, commits, returns that entry.
- On any error the store is unchanged.

### 4.4 get_entry(db_path: str, seq: int) -> dict | None
- Entry dict (six keys, §3 order) or None. Never creates a file.

### 4.5 get_by_hash(db_path: str, hash: str) -> dict | None
- Entry with that hash, or None. Uses the hash index.

### 4.6 get_by_signer(db_path: str, signer: str) -> list[dict]
- All entries by that signer in seq order; [] if none.

### 4.7 verify_store(db_path: str, public_key) -> bool
- TypeError if public_key is not Ed25519PublicKey (from P4).
- False if: file missing, no ledger table, store empty, or the image
  fails ledger_v2.verify_ledger. Otherwise True.
- Never raises for database content.

## 5. Invariants (each is a test)
- I1: For the same records and key, export_jsonl of a v2 store is
  byte-identical to the file ledger_v2.append_entry produces.
- I2: A database built by store.py v1 verifies under v2.
- I3: store_v2.py imports nothing from P4 beginning with "_".
- I4: store.py v1 is byte-unchanged.

## 6. Imports
Sibling layer paths resolve from os.path.dirname(__file__), never
from the working directory.

## 7. Known costs
- append_entry is O(n): it verifies the whole store first. P4 v2 has
  the same cost. Acceptable until a store reaches a size that hurts.
- The whole store is written to a temp file on every append/verify.
