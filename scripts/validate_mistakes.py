#!/usr/bin/env python3
"""Zero-dependency validator for MISTAKES.md ledgers.

Checks invariants defined in MISTAKES.md.template and README.md:
  1. Valid ISO calendar dates (YYYY-MM-DD)
  2. All four required fields present and non-empty
     (What happened, Root cause, Consequence, The rule)
  3. Single consistent style per file (single-line OR sectioned)
  4. Newest-first chronological ordering (same-day entries allowed)
  5. Empty-ledger placeholder support (e.g. MISTAKES.md.template)

Usage:
  python3 scripts/validate_mistakes.py [path/to/MISTAKES.md] [--json]
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTION_FIELDS = [
    ("what_happened", "What happened", re.compile(r"^\*\*What happened:?\*\*:?\s*(.*)$", re.IGNORECASE)),
    ("root_cause", "Root cause", re.compile(r"^\*\*Root cause:?\*\*:?\s*(.*)$", re.IGNORECASE)),
    ("consequence", "Consequence", re.compile(r"^\*\*Consequence:?\*\*:?\s*(.*)$", re.IGNORECASE)),
    ("the_rule", "The rule", re.compile(r"^\*\*The rule:?\*\*:?\s*(.*)$", re.IGNORECASE)),
]

SINGLE_LINE_FIELDS = ["What happened", "Root cause", "Consequence", "The rule"]

HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
ENTRIES_HEADING_RE = re.compile(r"^##\s+Entries\s*$", re.IGNORECASE)
ANY_H2_RE = re.compile(r"^##\s+")
DATE_LIKE = r"\d{4}-\d{1,2}-\d{1,2}"
DATE_H2_PREFIX_RE = re.compile(rf"^##\s+{DATE_LIKE}\b")
PLACEHOLDER_RE = re.compile(r"^\*?\(?\s*No mistakes logged yet\s*\)?\*?$", re.IGNORECASE)
SECTION_ENTRY_RE = re.compile(rf"^##\s+({DATE_LIKE})(?:\s+(?:—|--|-|–)\s+(.*)|\s+(.*))?$")
SINGLE_LINE_ENTRY_RE = re.compile(rf"^(?:-\s+)?({DATE_LIKE})\s+(?:—|--|-|–)\s+(.+)$")
DATE_LINE_PREFIX_RE = re.compile(rf"^(?:-\s+)?{DATE_LIKE}\b")


def strip_html_comments_preserve_lines(markdown: str) -> str:
    """Strip HTML comments while keeping newline counts intact for accurate line numbers."""
    return HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), markdown)


def is_valid_iso_date(date_str: str) -> bool:
    """Return True if date_str is a valid YYYY-MM-DD calendar date."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        return False
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def extract_entries_region(lines: list[str]) -> tuple[int, int]:
    """Return (start_idx, end_idx) for the entries section."""
    start_idx = 0
    for idx, line in enumerate(lines):
        if ENTRIES_HEADING_RE.match(line.strip()):
            start_idx = idx + 1
            break

    end_idx = len(lines)
    for idx in range(start_idx, len(lines)):
        trimmed = lines[idx].strip()
        if ANY_H2_RE.match(trimmed) and not DATE_H2_PREFIX_RE.match(trimmed):
            end_idx = idx
            break

    return start_idx, end_idx


def validate_mistakes_markdown(raw_content: str, file_path: str = "MISTAKES.md") -> dict:
    """Validate a MISTAKES.md string and return a structured result dict."""
    errors: list[dict] = []
    warnings: list[dict] = []
    entries: list[dict] = []

    cleaned = strip_html_comments_preserve_lines(raw_content)
    lines = cleaned.splitlines()
    start_idx, end_idx = extract_entries_region(lines)

    has_placeholder = False
    i = start_idx

    while i < end_idx:
        line_num = i + 1
        trimmed = lines[i].strip()

        if not trimmed or re.fullmatch(r"-{3,}", trimmed) or re.match(r"^#\s+", trimmed):
            i += 1
            continue

        if PLACEHOLDER_RE.match(trimmed):
            has_placeholder = True
            i += 1
            continue

        # Style B: Sectioned entry (`## YYYY-MM-DD — Short title`)
        sec_match = SECTION_ENTRY_RE.match(trimmed)
        if sec_match:
            date = sec_match.group(1)
            title = (sec_match.group(2) or sec_match.group(3) or "").strip()

            if not is_valid_iso_date(date):
                errors.append({"line": line_num, "message": f'Invalid calendar date "{date}".'})
            if not title:
                errors.append({"line": line_num, "message": f"Sectioned entry for {date} is missing a short title."})

            found_fields: dict[str, str] = {}
            active_field: str | None = None
            j = i + 1

            while j < end_idx:
                next_trimmed = lines[j].strip()
                if (
                    ANY_H2_RE.match(next_trimmed)
                    or DATE_LINE_PREFIX_RE.match(next_trimmed)
                    or re.fullmatch(r"-{3,}", next_trimmed)
                ):
                    break

                matched_field = False
                for key, _label, pattern in REQUIRED_SECTION_FIELDS:
                    m = pattern.match(next_trimmed)
                    if m:
                        active_field = key
                        found_fields[key] = m.group(1).strip()
                        matched_field = True
                        break

                if not matched_field and active_field and next_trimmed:
                    prev = found_fields.get(active_field, "")
                    found_fields[active_field] = f"{prev} {next_trimmed}".strip() if prev else next_trimmed

                j += 1

            for key, label, _pattern in REQUIRED_SECTION_FIELDS:
                if key not in found_fields:
                    errors.append({
                        "line": line_num,
                        "message": f'Sectioned entry ({date}) is missing required field "**{label}:**".',
                    })
                elif not found_fields[key]:
                    errors.append({
                        "line": line_num,
                        "message": f'Sectioned entry ({date}) has an empty "**{label}:**" field.',
                    })

            entries.append({"style": "sectioned", "date": date, "line": line_num})
            i = j
            continue

        # Style A: Single-line entry (`YYYY-MM-DD - What | Cause | Consequence | Rule`)
        single_match = SINGLE_LINE_ENTRY_RE.match(trimmed)
        if single_match:
            date = single_match.group(1)
            rest = single_match.group(2)

            if not is_valid_iso_date(date):
                errors.append({"line": line_num, "message": f'Invalid calendar date "{date}".'})

            parts = [p.strip() for p in rest.split("|")]
            if len(parts) != 4:
                errors.append({
                    "line": line_num,
                    "message": (
                        f"Single-line entry ({date}) must have 4 pipe-separated fields "
                        f"(What happened | Root cause | Consequence | The rule); found {len(parts)}."
                    ),
                })
            else:
                for idx, value in enumerate(parts):
                    if not value:
                        errors.append({
                            "line": line_num,
                            "message": f'Single-line entry ({date}) has an empty "{SINGLE_LINE_FIELDS[idx]}" field.',
                        })

            entries.append({"style": "single-line", "date": date, "line": line_num})
            i += 1
            continue

        # Malformed line beginning with a date
        if DATE_LINE_PREFIX_RE.match(trimmed):
            errors.append({
                "line": line_num,
                "message": (
                    'Unrecognized entry format. Expected '
                    '"YYYY-MM-DD - What | Cause | Consequence | Rule" or "## YYYY-MM-DD — Title".'
                ),
            })

        i += 1

    # Invariant: single consistent style per file
    styles = sorted({e["style"] for e in entries})
    if len(styles) > 1:
        errors.append({
            "line": entries[0]["line"],
            "message": f"Mixed entry styles ({' and '.join(styles)}). Pick one style per file and stay consistent.",
        })

    # Invariant: newest-first chronological ordering
    for idx in range(1, len(entries)):
        prev = entries[idx - 1]
        curr = entries[idx]
        if is_valid_iso_date(prev["date"]) and is_valid_iso_date(curr["date"]) and curr["date"] > prev["date"]:
            errors.append({
                "line": curr["line"],
                "message": (
                    f'Out-of-order entry: {curr["date"]} appears after older entry '
                    f'{prev["date"]} (line {prev["line"]}). Newest entries go first.'
                ),
            })

    if has_placeholder and entries:
        warnings.append({
            "line": start_idx + 1,
            "message": f'Placeholder "(No mistakes logged yet)" is still present alongside {len(entries)} logged entries.',
        })

    if not has_placeholder and not entries and not errors:
        warnings.append({
            "line": start_idx + 1,
            "message": 'No entries or "(No mistakes logged yet)" placeholder found.',
        })

    style = styles[0] if len(styles) == 1 else ("mixed" if len(styles) > 1 else "empty")
    return {
        "file": file_path,
        "valid": len(errors) == 0,
        "style": style,
        "entry_count": len(entries),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    as_json = "--json" in args
    positional = [a for a in args if not a.startswith("-")]
    target_arg = positional[0] if positional else "MISTAKES.md"
    target_path = Path(target_arg)

    try:
        content = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f'Cannot read "{target_arg}": {exc}'
        if as_json:
            print(json.dumps({"file": target_arg, "valid": False, "errors": [{"line": 0, "message": msg}], "warnings": []}, indent=2))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    result = validate_mistakes_markdown(content, target_arg)

    if as_json:
        print(json.dumps(result, indent=2))
    elif result["valid"]:
        noun = "entry" if result["entry_count"] == 1 else "entries"
        print(f'OK: {result["file"]} ({result["entry_count"]} {noun}, style: {result["style"]})')
        for w in result["warnings"]:
            print(f'  WARN  line {w["line"]}: {w["message"]}', file=sys.stderr)
    else:
        noun = "error" if len(result["errors"]) == 1 else "errors"
        print(f'FAIL: {result["file"]} ({len(result["errors"])} {noun})', file=sys.stderr)
        for e in result["errors"]:
            print(f'  ERROR line {e["line"]}: {e["message"]}', file=sys.stderr)
        for w in result["warnings"]:
            print(f'  WARN  line {w["line"]}: {w["message"]}', file=sys.stderr)

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
