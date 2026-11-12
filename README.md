# store-layer — P8 Store

README.md — repository purpose and layer contract for P8 Store.

Function:
    This repository implements primitive layer P8 of the Forge Stack:
    a SQLite ledger per node. It holds P4 ledger entries as indexed
    rows for fast lookup by seq, hash or signer. From v2, every chain,
    hash and signature decision is made by P4 Ledger v2 itself.

Use:
    New code imports `store_v2`. `store.py` (v1) is frozen and kept
    for existing callers (Immutable Rule).

Files:
    store_v2.py / SPEC_V2.md / test_store_v2.py — v2 (current)
    store.py    / SPEC.md    / test_store.py    — v1 (frozen)
    V1.sha256   — pins v1 files; test_store_v2 fails if they change

Layer:    P8 — Store
Depends:  P4 Ledger v2 (public API); P1 Envelope v2 via P4
Consumed: P9 Substrate, SC-OS, The Cockpit
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   2.0.0 (frozen)
