"""
store_v2_1.py — P8 Store v2.1, gap-closing layer over store_v2

Function:
    The layer new code imports instead of store_v2.py. It passes the
    store_v2 2.0.0 API through unchanged and closes two audit gaps
    (SPEC_V2_1.md §0): verify_store no longer raises on deeply nested
    stored JSON, and get_by_hash takes the parameter name the spec
    gives (`hash`). store_v2.py is not edited (Immutable Rule). No
    hashing, signing, chain or SQL logic lives here.

Public API:
    1. get_by_hash    — SPEC_V2 §4.5 with the `hash` parameter name
    2. verify_store   — SPEC_V2 §4.7, never raises for content
    Passed through from store_v2: init_db, export_jsonl,
    append_entry, get_entry, get_by_signer.

Layer:    P8 — Store, v2.1
Depends:  P8 store_v2 2.0.0 (public API only); P4 Ledger v2 via v2
Consumed: P9 Substrate, SC-OS, The Cockpit
Spec:     SPEC_V2_1.md 2.1.0 (over SPEC_V2.md 2.0.0)
Version:  2.1.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import tempfile

# Resolve store_v2 from this file's location, not the CWD (SPEC_V2_1 §4).
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import store_v2  # noqa: E402

init_db = store_v2.init_db
export_jsonl = store_v2.export_jsonl
append_entry = store_v2.append_entry
get_entry = store_v2.get_entry
get_by_signer = store_v2.get_by_signer


# ---------------------------------------------------------------------------
# 1. get_by_hash
#    SPEC_V2_1 §2.1. store_v2.get_by_hash with the parameter named
#    `hash` as SPEC_V2 §4.5 gives it, so keyword calls work.
# ---------------------------------------------------------------------------
def get_by_hash(db_path, hash):  # noqa: A002 (name fixed by spec)
    return store_v2.get_by_hash(db_path, hash)


# ---------------------------------------------------------------------------
# 2. verify_store
#    SPEC_V2_1 §2.2. store_v2.verify_store, except that a store too
#    deeply nested to decode is judged as unreadable: P4 v2 verifies an
#    empty image (via v2 on an absent path), so a wrong key type still
#    raises TypeError and otherwise the answer is False.
# ---------------------------------------------------------------------------
def verify_store(db_path, public_key):
    try:
        return store_v2.verify_store(db_path, public_key)
    except RecursionError:
        with tempfile.TemporaryDirectory() as tmp:
            return store_v2.verify_store(os.path.join(tmp, "absent.db"), public_key)
