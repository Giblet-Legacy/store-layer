"""
store_v2.py — P8 Store v2, SQLite store judged by P4 Ledger v2

Function:
    The layer new code imports instead of store.py. It holds ledger
    entries as SQLite rows, indexed by hash and signer, and hands every
    chain, hash, signature and record-form decision to P4 Ledger v2's
    public API over the store's .jsonl image (SPEC_V2.md §1, §3).
    It contains no hashing or signing of its own. store.py v1 is not
    edited (Immutable Rule); this file is the "add a layer" half.

Public API:
    1. init_db        — create table and indexes (idempotent, v1-safe)
    2. export_jsonl   — the store as P4 v2 .jsonl bytes
    3. append_entry   — P4 v2 builds and checks the entry; P8 inserts it
    4. get_entry      — one entry by seq
    5. get_by_hash    — one entry by hash
    6. get_by_signer  — all entries by signer, in seq order
    7. verify_store   — P4 v2 verify over the .jsonl image

Internal helpers (not exported):
    8.  _connect      — open an existing db read/write; never create
    9.  _row_entry    — SQLite row to entry dict, P4 key order
    10. _image        — all rows to .jsonl bytes (SPEC_V2 §3)
    11. _ledger_file  — bytes written to a private temp ledger file

Layer:    P8 — Store, v2
Depends:  P4 Ledger v2 (public API only), via ledger-layer/
Consumed: P9 Substrate, SC-OS, The Cockpit
Spec:     SPEC_V2.md 2.0.0 (over SPEC.md v1.0.0)
Version:  2.0.0 (on freeze; draft until then)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import pathlib
import sqlite3
import sys
import tempfile
from contextlib import contextmanager

# Resolve P4 v2 from this file's location, not the CWD (SPEC_V2 §6).
_HERE = os.path.dirname(os.path.abspath(__file__))
_LEDGER = os.path.join(os.path.dirname(_HERE), "ledger-layer")
if _LEDGER not in sys.path:
    sys.path.insert(0, _LEDGER)

import ledger_v2  # noqa: E402

_COLUMNS = ", ".join(ledger_v2.KEYS)
_SCHEMA = """
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
"""


# ---------------------------------------------------------------------------
# 8. _connect
#    Opens an existing database read/write in autocommit mode, so
#    transactions are explicit. FileNotFoundError if absent; mode=rw
#    means SQLite itself can never create the file either.
# ---------------------------------------------------------------------------
def _connect(db_path):
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)
    uri = pathlib.Path(os.path.abspath(db_path)).as_uri() + "?mode=rw"
    return sqlite3.connect(uri, uri=True, isolation_level=None)


# ---------------------------------------------------------------------------
# 9. _row_entry
#    One SQLite row to an entry dict with keys in P4 order. The record
#    text is parsed back to a dict, insertion order preserved.
# ---------------------------------------------------------------------------
def _row_entry(row):
    entry = dict(zip(ledger_v2.KEYS, row))
    entry["record"] = json.loads(entry["record"])
    return entry


# ---------------------------------------------------------------------------
# 10. _image
#     All rows in seq order as P4 v2 .jsonl bytes (SPEC_V2 §3).
#     Raises ValueError/TypeError if a stored record is not JSON text.
# ---------------------------------------------------------------------------
def _image(conn):
    rows = conn.execute(f"SELECT {_COLUMNS} FROM ledger ORDER BY seq").fetchall()
    return b"".join(
        json.dumps(_row_entry(r), separators=(",", ":")).encode("ascii") + b"\n"
        for r in rows
    )


# ---------------------------------------------------------------------------
# 11. _ledger_file
#     Writes bytes to ledger.jsonl in a private temp directory and yields
#     its path. The directory is removed on exit, error or not.
# ---------------------------------------------------------------------------
@contextmanager
def _ledger_file(data):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "ledger.jsonl")
        with open(path, "wb") as f:
            f.write(data)
        yield path


# ---------------------------------------------------------------------------
# 1. init_db
#    SPEC_V2 §4.1. Creates the table and both indexes if absent.
#    Idempotent; on a v1 database it adds the indexes only.
# ---------------------------------------------------------------------------
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_SCHEMA)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 2. export_jsonl
#    SPEC_V2 §4.2. The store's .jsonl image. Never creates a file.
# ---------------------------------------------------------------------------
def export_jsonl(db_path):
    conn = _connect(db_path)
    try:
        return _image(conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 3. append_entry
#    SPEC_V2 §4.3. Under a write lock: image to temp file, P4 v2
#    append_entry builds and checks the entry (all P4 errors pass
#    through), P8 inserts it. On any error the store is rolled back.
# ---------------------------------------------------------------------------
def append_entry(db_path, record, private_key):
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            with _ledger_file(_image(conn)) as path:
                entry = ledger_v2.append_entry(path, record, private_key)
            conn.execute(
                f"INSERT INTO ledger ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    entry["seq"],
                    entry["prev"],
                    json.dumps(entry["record"], separators=(",", ":")),
                    entry["signer"],
                    entry["hash"],
                    entry["signature"],
                ),
            )
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return entry
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 4. get_entry
#    SPEC_V2 §4.4. Entry with this seq, or None.
# ---------------------------------------------------------------------------
def get_entry(db_path, seq):
    conn = _connect(db_path)
    try:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM ledger WHERE seq = ?", (seq,)
        ).fetchone()
    finally:
        conn.close()
    return None if row is None else _row_entry(row)


# ---------------------------------------------------------------------------
# 5. get_by_hash
#    SPEC_V2 §4.5. Entry with this hash, or None. Uses ledger_hash.
# ---------------------------------------------------------------------------
def get_by_hash(db_path, hash_hex):
    conn = _connect(db_path)
    try:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM ledger WHERE hash = ? ORDER BY seq LIMIT 1",
            (hash_hex,),
        ).fetchone()
    finally:
        conn.close()
    return None if row is None else _row_entry(row)


# ---------------------------------------------------------------------------
# 6. get_by_signer
#    SPEC_V2 §4.6. All entries by this signer in seq order, or [].
# ---------------------------------------------------------------------------
def get_by_signer(db_path, signer):
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            f"SELECT {_COLUMNS} FROM ledger WHERE signer = ? ORDER BY seq",
            (signer,),
        ).fetchall()
    finally:
        conn.close()
    return [_row_entry(r) for r in rows]


# ---------------------------------------------------------------------------
# 7. verify_store
#    SPEC_V2 §4.7. Reads the image; if the store cannot be read at all
#    (missing, no table, not SQLite, bad record text) the image is b"".
#    P4 v2 verify_ledger then judges either way: TypeError on a wrong
#    key type, False on an empty image, else its chain verdict.
#    Never raises for database content.
# ---------------------------------------------------------------------------
def verify_store(db_path, public_key):
    try:
        conn = _connect(db_path)
        try:
            data = _image(conn)
        finally:
            conn.close()
    except (FileNotFoundError, sqlite3.DatabaseError, ValueError, TypeError):
        data = b""
    with _ledger_file(data) as path:
        return ledger_v2.verify_ledger(path, public_key)
