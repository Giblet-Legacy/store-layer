"""
test_store.py — P8 Store test suite

Function:
    Executable expression of SPEC.md. Written before store.py per
    build discipline.

Layer:    P8 — Store
Spec:     SPEC.md v1.0.0
Licence:  MSL-1.0
"""

import os
import sys
import json
import sqlite3
import tempfile
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, os.path.abspath('../envelope-layer'))
sys.path.insert(0, os.path.abspath('../ledger-layer'))

import store

@pytest.fixture
def key():
    return Ed25519PrivateKey.generate()

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_init_db(temp_db):
    store.init_db(temp_db)
    assert os.path.exists(temp_db)
    conn = sqlite3.connect(temp_db)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ledger'")
    assert cur.fetchone() is not None
    conn.close()

def test_append_genesis(temp_db, key):
    store.init_db(temp_db)
    entry = store.append_entry(temp_db, {"data": "genesis"}, key)
    assert entry["seq"] == 0
    assert entry["prev"] == "0" * 64

def test_append_multiple(temp_db, key):
    store.init_db(temp_db)
    e1 = store.append_entry(temp_db, {"data": "one"}, key)
    e2 = store.append_entry(temp_db, {"data": "two"}, key)
    e3 = store.append_entry(temp_db, {"data": "three"}, key)

    assert e2["seq"] == 1
    assert e2["prev"] == e1["hash"]
    assert e3["seq"] == 2
    assert e3["prev"] == e2["hash"]

def test_get_entry(temp_db, key):
    store.init_db(temp_db)
    store.append_entry(temp_db, {"data": "one"}, key)
    store.append_entry(temp_db, {"data": "two"}, key)

    got = store.get_entry(temp_db, 1)
    assert got["seq"] == 1
    assert got["record"] == {"data": "two"}

    assert store.get_entry(temp_db, 99) is None

def test_verify_store_valid(temp_db, key):
    store.init_db(temp_db)
    store.append_entry(temp_db, {"data": "one"}, key)
    store.append_entry(temp_db, {"data": "two"}, key)
    store.append_entry(temp_db, {"data": "three"}, key)
    assert store.verify_store(temp_db, key.public_key()) is True

def test_verify_store_tampered(temp_db, key):
    store.init_db(temp_db)
    store.append_entry(temp_db, {"data": "one"}, key)
    store.append_entry(temp_db, {"data": "two"}, key)

    conn = sqlite3.connect(temp_db)
    conn.execute("UPDATE ledger SET record = ? WHERE seq = ?",
                 ('{"data":"tampered"}', 0))
    conn.commit()
    conn.close()

    assert store.verify_store(temp_db, key.public_key()) is False

def test_verify_store_broken_chain(temp_db, key):
    store.init_db(temp_db)
    store.append_entry(temp_db, {"data": "one"}, key)
    store.append_entry(temp_db, {"data": "two"}, key)

    conn = sqlite3.connect(temp_db)
    conn.execute("UPDATE ledger SET prev = ? WHERE seq = ?",
                 ("badhash" * 8, 1))
    conn.commit()
    conn.close()

    assert store.verify_store(temp_db, key.public_key()) is False
