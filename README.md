# store-layer — P8 Store

README.md — repository purpose and layer contract for P8 Store.

Function:
    This repository implements primitive layer P8 of the Forge Stack:
    SQLite ledger per node. It consumes P1 Envelope v2 and P4 Ledger v2
    to provide a fast, queryable storage layer that enforces the same
    hash-chain rules as the flat .jsonl ledger.

Layer:    P8 — Store
Depends:  P1 Envelope v2, P4 Ledger v2
Consumed: P9 Substrate, SC-OS, The Cockpit
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   0.0.0-dev (in build, pre-freeze)
