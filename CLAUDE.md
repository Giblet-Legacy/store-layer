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
- Depends on `envelope_v2` (P1) and `ledger_v2` (P4).
- Implements a SQLite ledger mirroring the `.jsonl` format.
- Uses standard library `sqlite3`. No external ORMs.
- Enforces the same cryptographic chain rules as P4.
