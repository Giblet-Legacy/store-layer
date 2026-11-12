# SPEC — store-layer (P8 Store)

SPEC.md — the complete layer specification for P8 Store.

Function:
    This document is the authoritative specification for primitive
    layer P8 of the Forge Stack. It defines the SQLite-backed ledger.

Layer:     P8 — Store
Depends:   P1 Envelope v2, P4 Ledger v2
Consumed:  P9 Substrate, SC-OS, The Cockpit
Version:   SPEC 1.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 1. The Store Rule

P8 mirrors the .jsonl ledger into a SQLite database. It enforces
the same hash-chain and signature rules as P4, but allows fast
queries by seq, hash, or signer.

## 2. Database Schema

CREATE TABLE IF NOT EXISTS ledger (
    seq INTEGER PRIMARY KEY,
    prev TEXT NOT NULL,
    record TEXT NOT NULL,
    signer TEXT NOT NULL,
    hash TEXT NOT NULL,
    signature TEXT NOT NULL
);

## 3. Function Contracts

### 3.1 init_db(db_path: str) -> None
- Creates the ledger table if it doesn't exist.
- Failure: IOError if path is not writable.

### 3.2 append_entry(db_path: str, record: dict, private_key) -> dict
- Reads the last seq and hash (genesis defaults if empty).
- Builds the unsigned entry, hashes it, signs the digest, inserts.
- Returns the inserted entry.

### 3.3 get_entry(db_path: str, seq: int) -> dict
- Returns the entry as a dict, or None if not found.

### 3.4 verify_store(db_path: str, public_key) -> bool
- Reads all rows ordered by seq.
- Verifies hash chain, recalculates hashes, verifies signatures.
- Returns True if valid, False otherwise.
