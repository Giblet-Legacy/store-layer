"""
test_store_v2.py — P8 Store v2 test suite

Function:
    Executable expression of SPEC_V2.md. Written before store_v2.py per
    build discipline. Every contract in §4 and invariant in §5 has at
    least one test. v1's test_store.py is untouched and still runs.

Layer:    P8 — Store, v2
Spec:     SPEC_V2.md 2.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import ast
import hashlib
import os
import sqlite3
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

_HERE = os.path.dirname(os.path.abspath(__file__))
_LEDGER = os.path.join(os.path.dirname(_HERE), "ledger-layer")
for _path in (_LEDGER, _HERE):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import ledger_v2  # noqa: E402
import store  # noqa: E402  (v1, for I2)
import store_v2  # noqa: E402

RECORDS = [
    {"data": "one"},
    {"b": 1, "a": 2},
    {"nested": {"z": [1, 2], "y": None}},
]


# 1. key — fresh Ed25519 private key
@pytest.fixture
def key():
    return Ed25519PrivateKey.generate()


# 2. other_key — a second, foreign key
@pytest.fixture
def other_key():
    return Ed25519PrivateKey.generate()


# 3. db_path — a path that does not exist yet
@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "store.db")


# 4. db — an initialised, empty v2 store
@pytest.fixture
def db(db_path):
    store_v2.init_db(db_path)
    return db_path


# 5. _rows — row count, read straight from SQLite
def _rows(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
    finally:
        conn.close()


# 6. _sql — one raw write against SQLite (the tamper tool)
def _sql(path, query, params=()):
    conn = sqlite3.connect(path)
    try:
        conn.execute(query, params)
        conn.commit()
    finally:
        conn.close()


# 7. _fill — append records in order through v2, return the entries
def _fill(path, records, key):
    return [store_v2.append_entry(path, r, key) for r in records]


# 8. §4.1 init_db creates the table and both indexes
def test_init_db_creates_table_and_indexes(db_path):
    store_v2.init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    finally:
        conn.close()
    assert {"ledger", "ledger_hash", "ledger_signer"} <= names


# 9. §4.1 init_db is idempotent and keeps rows
def test_init_db_idempotent(db, key):
    _fill(db, RECORDS[:1], key)
    store_v2.init_db(db)
    assert _rows(db) == 1


# 10. §4.1 init_db on a v1 database keeps its rows
def test_init_db_on_v1_keeps_rows(db_path, key):
    store.init_db(db_path)
    store.append_entry(db_path, {"data": "v1"}, key)
    store_v2.init_db(db_path)
    assert _rows(db_path) == 1


# 11. §4.1 init_db raises OperationalError on an unwritable path
def test_init_db_unwritable(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        store_v2.init_db(str(tmp_path / "no-such-dir" / "store.db"))


# 12. §4 missing db raises FileNotFoundError and is never created
@pytest.mark.parametrize("call", [
    lambda p, k: store_v2.export_jsonl(p),
    lambda p, k: store_v2.append_entry(p, {"data": "x"}, k),
    lambda p, k: store_v2.get_entry(p, 0),
    lambda p, k: store_v2.get_by_hash(p, "0" * 64),
    lambda p, k: store_v2.get_by_signer(p, "did:key:x"),
])
def test_missing_db_raises_and_is_not_created(db_path, key, call):
    with pytest.raises(FileNotFoundError):
        call(db_path, key)
    assert not os.path.exists(db_path)


# 13. §4.2 an empty store exports b""
def test_export_empty(db):
    assert store_v2.export_jsonl(db) == b""


# 14. §5 I1 export is byte-identical to a P4 v2 ledger of the same appends
def test_i1_export_matches_p4(db, key, tmp_path):
    jsonl = str(tmp_path / "ledger.jsonl")
    for r in RECORDS:
        store_v2.append_entry(db, r, key)
        ledger_v2.append_entry(jsonl, r, key)
    with open(jsonl, "rb") as f:
        assert store_v2.export_jsonl(db) == f.read()


# 15. §4.3 genesis: seq 0, zero prev, six keys in P4 order
def test_append_genesis(db, key):
    e = store_v2.append_entry(db, {"data": "genesis"}, key)
    assert list(e) == ledger_v2.KEYS
    assert e["seq"] == 0
    assert e["prev"] == "0" * 64


# 16. §4.3 entries chain by seq and prev
def test_append_chain(db, key):
    e = _fill(db, RECORDS, key)
    for i in (1, 2):
        assert e[i]["seq"] == i
        assert e[i]["prev"] == e[i - 1]["hash"]


# 17. §2 record stored as compact JSON in insertion order
def test_record_stored_in_insertion_order(db, key):
    store_v2.append_entry(db, {"b": 1, "a": 2}, key)
    conn = sqlite3.connect(db)
    try:
        stored = conn.execute("SELECT record FROM ledger").fetchone()[0]
    finally:
        conn.close()
    assert stored == '{"b":1,"a":2}'


# 18. §4.3 a foreign key is refused, store unchanged
def test_append_foreign_key_refused(db, key, other_key):
    _fill(db, RECORDS[:2], key)
    with pytest.raises(ValueError):
        store_v2.append_entry(db, {"data": "intruder"}, other_key)
    assert _rows(db) == 2


# 19. §4.3 append onto a tampered store is refused, store unchanged
def test_append_on_tampered_refused(db, key):
    _fill(db, RECORDS[:2], key)
    _sql(db, "UPDATE ledger SET record = ? WHERE seq = 0",
         ('{"data":"tampered"}',))
    with pytest.raises(ValueError):
        store_v2.append_entry(db, {"data": "three"}, key)
    assert _rows(db) == 2


# 20. §4.3 bad input raises P4's error, store unchanged
@pytest.mark.parametrize("record, good_key, exc", [
    (["not", "a", "dict"], True, TypeError),
    ({"t": (1, 2)}, True, (TypeError, ValueError)),
    ({1: "int key"}, True, (TypeError, ValueError)),
    ({"x": float("nan")}, True, (TypeError, ValueError)),
    ({"data": "ok"}, False, TypeError),
])
def test_append_bad_input(db, key, record, good_key, exc):
    _fill(db, RECORDS[:1], key)
    with pytest.raises(exc):
        store_v2.append_entry(db, record, key if good_key else "not-a-key")
    assert _rows(db) == 1


# 21. §4.4 get_entry returns the entry in P4 key order, or None
def test_get_entry(db, key):
    e = _fill(db, RECORDS, key)
    got = store_v2.get_entry(db, 1)
    assert got == e[1]
    assert list(got) == ledger_v2.KEYS
    assert store_v2.get_entry(db, 99) is None


# 22. §4.5 get_by_hash returns the entry, or None
def test_get_by_hash(db, key):
    e = _fill(db, RECORDS, key)
    assert store_v2.get_by_hash(db, e[2]["hash"]) == e[2]
    assert store_v2.get_by_hash(db, "f" * 64) is None


# 23. §4.6 get_by_signer returns entries in seq order, or []
def test_get_by_signer(db, key):
    e = _fill(db, RECORDS, key)
    assert store_v2.get_by_signer(db, e[0]["signer"]) == e
    assert store_v2.get_by_signer(db, "did:key:nobody") == []


# 24. §4.7 a valid store verifies
def test_verify_valid(db, key):
    _fill(db, RECORDS, key)
    assert store_v2.verify_store(db, key.public_key()) is True


# 25. §4.7 an empty store is False
def test_verify_empty_false(db, key):
    assert store_v2.verify_store(db, key.public_key()) is False


# 26. §4.7 a missing file is False and is not created
def test_verify_missing_false(db_path, key):
    assert store_v2.verify_store(db_path, key.public_key()) is False
    assert not os.path.exists(db_path)


# 27. §4.7 a database with no ledger table is False
def test_verify_no_table_false(db_path, key):
    _sql(db_path, "CREATE TABLE other (x INTEGER)")
    assert store_v2.verify_store(db_path, key.public_key()) is False


# 28. §4.7 a non-SQLite file is False
def test_verify_garbage_file_false(db_path, key):
    with open(db_path, "wb") as f:
        f.write(b"not a database at all")
    assert store_v2.verify_store(db_path, key.public_key()) is False


# 29. §4.7 any tampered column is False
@pytest.mark.parametrize("column, value", [
    ("record", '{"data":"tampered"}'),
    ("record", "not json"),
    ("prev", "f" * 64),
    ("hash", "f" * 64),
    ("signature", "f" * 128),
    ("signer", "did:key:z6Mkforged"),
])
def test_verify_tampered_false(db, key, column, value):
    _fill(db, RECORDS, key)
    _sql(db, f"UPDATE ledger SET {column} = ? WHERE seq = 1", (value,))
    assert store_v2.verify_store(db, key.public_key()) is False


# 30. §4.7 a deleted row (seq gap) is False
def test_verify_gap_false(db, key):
    _fill(db, RECORDS, key)
    _sql(db, "DELETE FROM ledger WHERE seq = 1")
    assert store_v2.verify_store(db, key.public_key()) is False


# 31. §4.7 a wrong key type raises TypeError
def test_verify_wrong_key_type(db, key):
    _fill(db, RECORDS[:1], key)
    with pytest.raises(TypeError):
        store_v2.verify_store(db, key)  # private key, not public


# 32. §4.7 another signer's public key is False
def test_verify_other_key_false(db, key, other_key):
    _fill(db, RECORDS, key)
    assert store_v2.verify_store(db, other_key.public_key()) is False


# 33. §5 I2 a v1-built database verifies under v2, and v2 can extend it
def test_i2_v1_store_verifies_under_v2(db_path, key):
    store.init_db(db_path)
    for r in RECORDS:
        store.append_entry(db_path, r, key)
    assert store_v2.verify_store(db_path, key.public_key()) is True
    store_v2.append_entry(db_path, {"data": "v2 on v1"}, key)
    assert store_v2.verify_store(db_path, key.public_key()) is True


# 34. §1/§5 I3 no private P4 names, no P1 or P4 v1 imports, no own crypto
def test_i3_no_private_p4_and_no_own_crypto():
    with open(os.path.join(_HERE, "store_v2.py"), encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    aliases = {"ledger_v2"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name)
                if a.name == "ledger_v2" and a.asname:
                    aliases.add(a.asname)
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module)
            if node.module == "ledger_v2":
                assert not any(a.name.startswith("_") for a in node.names)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in aliases):
            assert not node.attr.startswith("_"), node.attr
    assert not imported & {"ledger", "envelope", "envelope_v2", "hashlib"}
    for banned in ("sha256", "sign_bytes", "verify_bytes"):
        assert banned not in src, banned


# 35. §5 I4 v1 files are byte-unchanged since V1.sha256 was pinned
def test_i4_v1_unchanged():
    with open(os.path.join(_HERE, "V1.sha256")) as f:
        pins = [line.split() for line in f if line.strip()]
    assert pins
    for digest, name in pins:
        with open(os.path.join(_HERE, name), "rb") as g:
            assert hashlib.sha256(g.read()).hexdigest() == digest, name


# 36. §6 store_v2 imports from any working directory
def test_imports_from_any_cwd(tmp_path):
    code = f"import sys; sys.path.insert(0, {_HERE!r}); import store_v2"
    r = subprocess.run([sys.executable, "-c", code], cwd=str(tmp_path),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
