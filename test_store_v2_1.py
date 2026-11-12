"""
test_store_v2_1.py — P8 Store v2.1 test suite

Function:
    Executable expression of SPEC_V2_1.md. Every gap in §0, contract in
    §2 and invariant in §3 has at least one test. test_store.py and
    test_store_v2.py are untouched and still run.

Layer:    P8 — Store, v2.1
Spec:     SPEC_V2_1.md 2.1.0
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
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import store_v2  # noqa: E402
import store_v2_1  # noqa: E402

DEEP = "[" * 100000 + "]" * 100000


# 1. key — fresh Ed25519 private key
@pytest.fixture
def key():
    return Ed25519PrivateKey.generate()


# 2. db — an initialised v2.1 store holding two entries
@pytest.fixture
def db(tmp_path, key):
    path = str(tmp_path / "store.db")
    store_v2_1.init_db(path)
    store_v2_1.append_entry(path, {"data": "one"}, key)
    store_v2_1.append_entry(path, {"data": "two"}, key)
    return path


# 3. _deepen — overwrite seq 0's record with deeply nested JSON
def _deepen(path):
    conn = sqlite3.connect(path)
    try:
        conn.execute("UPDATE ledger SET record = ? WHERE seq = 0", (DEEP,))
        conn.commit()
    finally:
        conn.close()


# 4. §0 G1 baseline: v2 itself raises on a deeply nested record
def test_g1_v2_raises(db, key):
    _deepen(db)
    with pytest.raises(RecursionError):
        store_v2.verify_store(db, key.public_key())


# 5. §2.2 v2.1 returns False on a deeply nested record
def test_verify_deep_false(db, key):
    _deepen(db)
    assert store_v2_1.verify_store(db, key.public_key()) is False


# 6. §2.2 a wrong key type still raises TypeError on a deep store
def test_verify_deep_wrong_key_type(db, key):
    _deepen(db)
    with pytest.raises(TypeError):
        store_v2_1.verify_store(db, key)


# 7. §2.2 otherwise identical to v2: valid True, empty False, bad key
def test_verify_matches_v2(db, key, tmp_path):
    assert store_v2_1.verify_store(db, key.public_key()) is True
    empty = str(tmp_path / "empty.db")
    store_v2_1.init_db(empty)
    assert store_v2_1.verify_store(empty, key.public_key()) is False
    with pytest.raises(TypeError):
        store_v2_1.verify_store(db, key)


# 8. §0 G2 / §2.1 get_by_hash works by keyword `hash` and positionally
def test_get_by_hash_keyword(db):
    e = store_v2_1.get_entry(db, 1)
    assert store_v2_1.get_by_hash(db, hash=e["hash"]) == e
    assert store_v2_1.get_by_hash(db, e["hash"]) == e
    assert store_v2_1.get_by_hash(db, hash="f" * 64) is None


# 9. §2 pass-through names are the store_v2 objects themselves
@pytest.mark.parametrize("name", [
    "init_db", "export_jsonl", "append_entry", "get_entry", "get_by_signer",
])
def test_pass_through(name):
    assert getattr(store_v2_1, name) is getattr(store_v2, name)


# 10. §3 I5 no private store_v2/ledger_v2 names, no own crypto
def test_i5_no_private_names_no_crypto():
    with open(os.path.join(_HERE, "store_v2_1.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    guarded = {"store_v2", "ledger_v2"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module)
            if node.module in guarded:
                assert not any(a.name.startswith("_") for a in node.names)
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in guarded):
            assert not node.attr.startswith("_"), node.attr
    assert not imported & {"hashlib", "cryptography", "ledger", "envelope",
                           "envelope_v2", "sqlite3"}


# 11. §3 I6 v2 files are byte-unchanged since V2.sha256 was pinned
def test_i6_v2_unchanged():
    with open(os.path.join(_HERE, "V2.sha256")) as f:
        pins = [line.split() for line in f if line.strip()]
    assert pins
    for digest, name in pins:
        with open(os.path.join(_HERE, name), "rb") as g:
            assert hashlib.sha256(g.read()).hexdigest() == digest, name


# 12. §4 store_v2_1 imports from any working directory
def test_imports_from_any_cwd(tmp_path):
    code = f"import sys; sys.path.insert(0, {_HERE!r}); import store_v2_1"
    r = subprocess.run([sys.executable, "-c", code], cwd=str(tmp_path),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
