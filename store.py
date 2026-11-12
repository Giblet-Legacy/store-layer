"""
store.py — P8 Store primitive layer

Function:
    SQLite-backed ledger mirroring P4's .jsonl format. Provides fast
    querying by seq while enforcing the same hash-chain and signature
    rules as P4. Consumes envelope_v2 (P1) and ledger_v2 (P4).

Public API:
    1. init_db         — Create the ledger table if it doesn't exist.
    2. append_entry    — Build, sign, and insert a new entry.
    3. get_entry       — Fetch a single entry by sequence number.
    4. verify_store    — Verify the entire chain.

Layer:    P8 — Store
Depends:  P1 Envelope v2, P4 Ledger v2
Consumed: P9 Substrate, SC-OS, The Cockpit
Version:  1.0.0 (on freeze; 0.0.0-dev until then)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import json
import sqlite3

# Import P1
sys.path.insert(0, os.path.abspath('../envelope-layer'))
import envelope_v2 as envelope

GENESIS_PREV = "0" * 64

# ---------------------------------------------------------------------------
# 1. init_db
#    Creates the ledger table if it doesn't already exist.
# ---------------------------------------------------------------------------
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            seq INTEGER PRIMARY KEY,
            prev TEXT NOT NULL,
            record TEXT NOT NULL,
            signer TEXT NOT NULL,
            hash TEXT NOT NULL,
            signature TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# 2. append_entry
#    Reads the last row for seq/prev, builds, signs, and inserts.
# ---------------------------------------------------------------------------
def append_entry(db_path, record, private_key):
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT seq, hash FROM ledger ORDER BY seq DESC LIMIT 1")
    row = cur.fetchone()

    if row is None:
        seq = 0
        prev = GENESIS_PREV
    else:
        seq = row[0] + 1
        prev = row[1]

    did_key = envelope.did_key_encode(private_key.public_key())
    unsigned = {
        "seq": seq,
        "prev": prev,
        "record": record,
        "signer": did_key,
    }

    canonical_bytes = envelope.canonical_bytes(unsigned)
    entry_hash = envelope.sha256_hex(canonical_bytes)
    entry_digest = envelope.sha256_digest(canonical_bytes)
    sig_bytes = envelope.sign_bytes(entry_digest, private_key)

    conn.execute(
        "INSERT INTO ledger (seq, prev, record, signer, hash, signature) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            seq,
            prev,
            json.dumps(record, sort_keys=True, separators=(",", ":")),
            did_key,
            entry_hash,
            sig_bytes.hex(),
        ),
    )
    conn.commit()
    conn.close()

    return {
        "seq": seq,
        "prev": prev,
        "record": record,
        "signer": did_key,
        "hash": entry_hash,
        "signature": sig_bytes.hex(),
    }

# ---------------------------------------------------------------------------
# 3. get_entry
#    Fetches a single entry by seq. Returns None if not found.
# ---------------------------------------------------------------------------
def get_entry(db_path, seq):
    conn = sqlite3.connect(db_path)
    cur = conn.execute(
        "SELECT seq, prev, record, signer, hash, signature FROM ledger WHERE seq = ?",
        (seq,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "seq": row[0],
        "prev": row[1],
        "record": json.loads(row[2]),
        "signer": row[3],
        "hash": row[4],
        "signature": row[5],
    }

# ---------------------------------------------------------------------------
# 4. verify_store
#    Reads all rows in seq order and verifies chain and signatures.
# ---------------------------------------------------------------------------
def verify_store(db_path, public_key):
    if not os.path.exists(db_path):
        return False

    expected_did = envelope.did_key_encode(public_key)
    expected_seq = 0
    expected_prev = GENESIS_PREV

    conn = sqlite3.connect(db_path)
    cur = conn.execute(
        "SELECT seq, prev, record, signer, hash, signature FROM ledger ORDER BY seq ASC"
    )

    for row in cur:
        seq, prev, record_json, signer, claimed_hash, sig_hex = row

        if seq != expected_seq:
            conn.close()
            return False
        if prev != expected_prev:
            conn.close()
            return False
        if signer != expected_did:
            conn.close()
            return False

        try:
            record = json.loads(record_json)
            sig_bytes = bytes.fromhex(sig_hex)
        except (json.JSONDecodeError, ValueError):
            conn.close()
            return False

        unsigned = {
            "seq": seq,
            "prev": prev,
            "record": record,
            "signer": signer,
        }
        canonical_bytes = envelope.canonical_bytes(unsigned)
        actual_hash = envelope.sha256_hex(canonical_bytes)
        actual_digest = envelope.sha256_digest(canonical_bytes)

        if actual_hash != claimed_hash:
            conn.close()
            return False

        if not envelope.verify_bytes(actual_digest, sig_bytes, public_key):
            conn.close()
            return False

        expected_seq += 1
        expected_prev = claimed_hash

    conn.close()
    return True
