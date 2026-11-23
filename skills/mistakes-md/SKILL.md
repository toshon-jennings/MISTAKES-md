---
name: mistakes-md
description: Read MISTAKES.md before risky actions and append structured failure entries (What happened, Root cause, Consequence, The rule) when errors occur.
---

# MISTAKES.md Skill

Use `MISTAKES.md` as a persistent, append-only ledger of failures so mistakes are not repeated across sessions.

## Before Any Risky Action

Before running destructive commands (`rm -rf`, database resets, schema migrations, auth changes, deploys, or bulk refactors):

1. Check for `MISTAKES.md` in the active project root (falling back to `~/.config/agent-rules/MISTAKES.md` if present).
2. Read the top entries and any entries covering the area you are about to touch.
3. Follow every applicable rule before executing.

## When a Mistake Happens

Append a new entry at the **top** of `## Entries` (newest first). Never edit or delete older entries—correct past rules by appending a superseding entry.

Match the style already used in the file:

- **Single-line:**
  `YYYY-MM-DD - What happened | Root cause | Consequence | The rule`
- **Sectioned:**
  ```markdown
  ## YYYY-MM-DD — Short title

  **What happened:** Concrete description (files, commands, ports).
  **Root cause:** The assumption, skipped check, or misread output.
  **Consequence:** What it cost (data loss, wasted time, correction).
  **The rule:** A checkable instruction that prevents a repeat.
  ```

## Validate Before Finishing

If `scripts/validate_mistakes.py` is available, verify formatting, style consistency, and newest-first ordering:

```bash
python3 scripts/validate_mistakes.py MISTAKES.md
```
