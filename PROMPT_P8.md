# P8 Store — Laptop Audit Prompt

P8 store-layer is frozen at v1.0.0 on the phone with 7/7 tests passing.

## Your Task

1. Pull `Giblet-Legacy/store-layer`.
2. Audit against SPEC.md and CHANGELOG.md (Good/Bad/Ugly, latest at top).
3. Run `pytest -q` — expect 7 passed.
4. Per the Immutable Rule, if you find gaps in `store.py` v1, create `store_v2.py` with `SPEC_V2.md` and `test_store_v2.py`. Do not edit v1.
5. Suggested V2 hardening: enforce LF-only SQLite content, reject empty store on verify, add index on hash and signer columns.
6. Push when green so the phone can verify.
