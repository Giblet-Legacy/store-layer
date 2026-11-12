# Forge Stack Context — P8 Store

CLAUDE.md — Context briefing for AI assistants working in this repository.

## The Immutable Rule
Never rewrite a primitive. Add a layer.

## Dual-Device Workflow
We build on an S24 (Termux) and a laptop (VS Code). State is confirmed, never assumed. Always use LF line endings. Commit messages must be clear. We use the Good/Bad/Ugly CHANGELOG format (latest at top).

## Header Discipline
Every file MUST have a top header paragraph explaining its function.
Every function MUST have a numbered header.

## P8 Architecture Specifics
- Current layer is `store_v2.py` (SPEC_V2.md). `store.py` v1 is frozen.
- v2 depends on `ledger_v2` (P4) public API only. Never import a name
  starting with `_` from P4. Never hash or sign in P8.
- P4 v2 is the sole judge of chain, hash, signature and record form.
- Uses standard library `sqlite3`. No external ORMs.
- Sibling layers are resolved from `__file__`, never the CWD.
- `V1.sha256` pins v1 files. Do not regenerate it.
