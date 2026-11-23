import unittest
from pathlib import Path

from validate_mistakes import validate_mistakes_markdown

REPO_ROOT = Path(__file__).resolve().parent.parent


class ValidateMistakesTests(unittest.TestCase):
    def test_accepts_repo_template(self) -> None:
        template = (REPO_ROOT / "MISTAKES.md.template").read_text(encoding="utf-8")
        result = validate_mistakes_markdown(template, "MISTAKES.md.template")
        self.assertTrue(result["valid"])
        self.assertEqual(result["style"], "empty")
        self.assertEqual(result["entry_count"], 0)
        self.assertEqual(result["errors"], [])

    def test_accepts_valid_single_line_entries(self) -> None:
        md = """# MISTAKES.md

## Entries

2026-09-15 - Ran DROP TABLE on staging | Thought terminal pointed to SQLite | Lost seed data | Check DATABASE_URL before running any migration
2026-09-15 - Shipped wrong port 3001 | Assumed dev server stayed on 3000 | Health check failed | Verify listening port before updating health config
2026-08-23 - Anchored exit button to right edge | Checked one narrow viewport | Offscreen on wide monitors | Verify escape controls across all viewports
"""
        result = validate_mistakes_markdown(md)
        self.assertTrue(result["valid"])
        self.assertEqual(result["style"], "single-line")
        self.assertEqual(result["entry_count"], 3)

    def test_accepts_valid_sectioned_entries(self) -> None:
        md = """# MISTAKES.md

## Entries

## 2026-09-13 — A validator held a false sentence in place

**What happened:** README asserted one chair alias while the repo ships three.
**Root cause:** The check grepped for an instance instead of the invariant.
**Consequence:** A false claim survived seven review rounds.
**The rule:** Grep the invariant, never a specific instance of it.

## 2026-09-01 — Skipped dry-run on bulk rename

**What happened:** Renamed 40 files in place without previewing matches.
**Root cause:** Ran sed without printing changed paths first.
**Consequence:** Reverted commit and redid edits manually.
**The rule:** Always run a dry-run diff before bulk file renames.

---

## Key Rules

1. Read this file before any risky action.
"""
        result = validate_mistakes_markdown(md)
        self.assertTrue(result["valid"])
        self.assertEqual(result["style"], "sectioned")
        self.assertEqual(result["entry_count"], 2)

    def test_rejects_single_line_missing_fields(self) -> None:
        md = """## Entries
2026-09-15 - Deleted wrong branch | Forgot to check git branch | Lost local commits
"""
        result = validate_mistakes_markdown(md)
        self.assertFalse(result["valid"])
        self.assertIn("4 pipe-separated fields", result["errors"][0]["message"])

    def test_rejects_sectioned_missing_field(self) -> None:
        md = """## Entries

## 2026-09-13 — Missing rule field

**What happened:** Something broke.
**Root cause:** Skipped a check.
**Consequence:** Wasted 30 minutes.
"""
        result = validate_mistakes_markdown(md)
        self.assertFalse(result["valid"])
        self.assertIn('missing required field "**The rule:**"', result["errors"][0]["message"])

    def test_rejects_mixed_styles(self) -> None:
        md = """## Entries

2026-09-15 - What | Cause | Consequence | Rule

## 2026-09-10 — Mixed entry

**What happened:** What.
**Root cause:** Cause.
**Consequence:** Consequence.
**The rule:** Rule.
"""
        result = validate_mistakes_markdown(md)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Mixed entry styles" in e["message"] for e in result["errors"]))

    def test_detects_single_line_entry_after_sectioned_entry(self) -> None:
        md = """## Entries

## 2026-09-10 — Sectioned entry

**What happened:** What happened.
**Root cause:** Root cause.
**Consequence:** Consequence.
**The rule:** The rule.
2026-09-15 - What happened | Root cause | Consequence | The rule
"""
        result = validate_mistakes_markdown(md)
        self.assertFalse(result["valid"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["style"], "mixed")
        self.assertTrue(any("Mixed entry styles" in e["message"] for e in result["errors"]))
        self.assertTrue(any("Out-of-order entry" in e["message"] for e in result["errors"]))

    def test_rejects_malformed_date_in_both_entry_styles(self) -> None:
        examples = {
            "single-line": "2026-9-15 - What | Cause | Consequence | Rule",
            "sectioned": "## 2026-9-15 — Malformed date\n\n**What happened:** What.",
        }
        for style, entry in examples.items():
            with self.subTest(style=style):
                result = validate_mistakes_markdown(f"## Entries\n{entry}\n")
                self.assertFalse(result["valid"])
                self.assertEqual(result["entry_count"], 1)
                self.assertTrue(any('Invalid calendar date "2026-9-15"' in e["message"] for e in result["errors"]))

    def test_rejects_out_of_order_dates(self) -> None:
        md = """## Entries
2026-08-01 - Older | Cause | Consequence | Rule
2026-09-15 - Newer | Cause | Consequence | Rule
"""
        result = validate_mistakes_markdown(md)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Out-of-order entry" in e["message"] for e in result["errors"]))

    def test_rejects_invalid_calendar_date(self) -> None:
        md = """## Entries
2026-02-30 - Impossible date | Typo | Invalid ledger | Use YYYY-MM-DD calendar dates
"""
        result = validate_mistakes_markdown(md)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid calendar date" in e["message"] for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
