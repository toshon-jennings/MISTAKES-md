# MISTAKES.md

> **A memory of failure, for AI agents and their humans.**  
> Agents read it before acting. Humans update it when they err.

---

## Why This Exists

AI coding agents have no persistent memory. Every session starts fresh -- same tools, same confidence, same blind spots. A mistake made on Monday gets remade on Thursday, by a different agent, in a different repo, for the same reason.

MISTAKES.md is the answer. It's a machine-readable, human-maintainable ledger of every mistake worth remembering. Agents check it before risky actions. Humans append to it when something goes wrong.

---

## How It Works

1. You create a MISTAKES.md in your agent rules directory (or repo root).
2. You configure your agents to read it at session start.
3. Every time a mistake happens, you log four things: what happened, the root cause, the consequence, and the rule that prevents a repeat.
4. Agents consult it before `rm -rf`, schema migrations, auth changes, deploys, bulk refactors, etc.

No vector DB. No memory plugin. Just a Markdown file that agents already know how to read.

---

## Agent Integration

### Hermes / Claude Code / Codex CLI / OpenClaw

Add this to your global agent rules (`~/.config/agent-rules/GLOBAL.md` or equivalent):

```markdown
## Mistake Tracking

- **MISTAKES.md:** Before any risky action (delete, migrate, deploy, refactor),
  read `MISTAKES.md` in the active project root (or `~/.config/agent-rules/MISTAKES.md`
  as fallback). Check for past failures in this area. Append a new entry when you
  make a mistake, using the format: What happened | Root cause | Consequence | The rule.
```

### Cursor Rules

Add to `.cursorrules`:

```
Before any risky action, check MISTAKES.md for past failures in this area.
Append a new entry when you make a mistake.
```

### Windsurf / Copilot / Other

Same idea -- reference MISTAKES.md in whatever rules/config mechanism your agent uses.

---

## Quick Start

```bash
# Copy the template to your agent rules directory
cp MISTAKES.md.template ~/.config/agent-rules/MISTAKES.md

# Or drop it in a specific project
cp MISTAKES.md.template ~/my-project/MISTAKES.md
```

Then log your first mistake. Format:

```
2026-09-15 - What happened | Root cause | Consequence | The rule that prevents repeat
```

Newest entries go first.

---

## File Format

MISTAKES.md has one repeating unit -- the entry -- with four fields:

| Field | Purpose |
|-------|---------|
| **What happened** | Concrete description of the error. Name files, commands, ports. No euphemism. |
| **Root cause** | Why it happened. The assumption, the skipped check, the misread output. |
| **Consequence** | What it cost. Data loss, wasted time, shipped falsehood, user correction. |
| **The rule** | The check that prevents a repeat. Stated as an instruction, not a wish. |

Two styles are both valid -- pick one per file and stay consistent:

- **Single-line:** `DATE - What | Cause | Consequence | Rule` (compact, greppable)
- **Sectioned:** `## DATE — Title` with four bolded paragraphs (for failures worth a postmortem)

See the template for the full annotated version.

---

## Validation & Agent Skill

### Zero-Dependency Validator

Verify that your `MISTAKES.md` follows the format (valid dates, all four fields, consistent style, newest-first order) locally or in CI:

```bash
python3 scripts/validate_mistakes.py MISTAKES.md

# Machine-readable JSON output for hooks/CI
python3 scripts/validate_mistakes.py MISTAKES.md --json
```

### Portable Agent Skill

If your agent supports `SKILL.md` (Antigravity, Claude Code, Codex CLI, etc.), copy `skills/mistakes-md/SKILL.md` into your skills directory so agents automatically read `MISTAKES.md` before risky actions and validate new entries.

---

## License

CC0 -- use it, fork it, ship it with your agent rules. No attribution required.
