# P8 Store — Laptop Audit Prompt (v2)

PROMPT_P8.md — instructions for auditing P8 v2 on the laptop.

P8 store-layer v2.0.0 is frozen on the phone. v1 7/7, v2 42/42.

## Your Task
1. Pull `Giblet-Legacy/store-layer`, plus `ledger-layer` and
   `envelope-layer` as siblings in the same parent folder.
2. Audit store_v2.py against SPEC_V2.md, NOTES.md and CHANGELOG.md.
3. Run `pytest -q` in store-layer. Expect 49 passed (7 + 42).
4. Check line endings: `git ls-files --eol` shows no crlf.
5. On Windows, confirm test_missing_db_raises_and_is_not_created and
   test_imports_from_any_cwd pass (Path.as_uri and mode=rw).
6. Do not edit store.py, test_store.py or SPEC.md. V1.sha256 will fail
   if you do. Gaps go in a v2.1 layer with its own spec and tests.
7. Push only when green, so the phone can verify.
