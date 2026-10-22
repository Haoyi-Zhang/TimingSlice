#!/usr/bin/env python3
"""Check citation closure and metadata fields without verifying primary sources."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


class BibliographyAuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BibliographyAuditError(message)


def entries(text: str) -> list[tuple[str, str, str]]:
    starts = list(re.finditer(r"(?m)^@(\w+)\s*\{\s*([^,\s]+)\s*,", text))
    result = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        if match.group(1).lower() == "ieeetranbstctl":
            continue
        result.append((match.group(1).lower(), match.group(2), text[match.start():end]))
    return result


def field(body: str, name: str) -> str:
    match = re.search(rf"(?mis)^\s*{re.escape(name)}\s*=\s*\{{(.*?)\}}\s*,?\s*$", body)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    match = re.search(rf'(?mis)^\s*{re.escape(name)}\s*=\s*"(.*?)"\s*,?\s*$', body)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def clean_title(value: str) -> str:
    return re.sub(r"[{}]", "", value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex", type=Path, required=True)
    parser.add_argument("--bib", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    try:
        tex = re.sub(r"(?<!\\)((?:\\\\)*)%[^\n]*", r"\1", args.tex.read_text(encoding="utf-8"))
        bib = args.bib.read_text(encoding="utf-8")
        parsed = entries(bib)
        keys = [key for _, key, _ in parsed]
        require(len(keys) == len(set(keys)), "duplicate BibTeX key")
        cited: set[str] = set()
        for match in re.finditer(r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}", tex):
            cited |= {part.strip() for part in match.group(1).split(",") if part.strip()}
        require(cited <= set(keys), f"missing BibTeX entries: {sorted(cited - set(keys))}")
        require(set(keys) <= cited, f"uncited BibTeX entries: {sorted(set(keys) - cited)}")

        with args.calibration.open(newline="", encoding="utf-8") as handle:
            calibrated = {row["bibkey"] for row in csv.DictReader(handle)}
        authoritative = {
            "zeng2024timing", "zeng2022architecture", "zeng2021state",
            "vaneijk1998sequential",
        }
        rows = []
        for kind, key, body in parsed:
            author = field(body, "author")
            title = field(body, "title")
            year = field(body, "year")
            venue = (field(body, "journal") or field(body, "booktitle") or
                     field(body, "publisher") or field(body, "howpublished"))
            require(author and title and year and venue, f"required metadata missing for {key}")
            doi = field(body, "doi")
            url = field(body, "url")
            howpublished = field(body, "howpublished")
            locator = f"https://doi.org/{doi}" if doi else (url or howpublished)
            if key in calibrated:
                basis = "retained_calibration_row_presence_only"
                status = "CALIBRATION_RECORD_PRESENT"
            elif key in authoritative:
                basis = "preconfigured_metadata_category_not_reverified"
                status = "PRECONFIGURED_METADATA_CATEGORY"
            else:
                basis = "syntax_and_required_fields_only_no_primary_source_check"
                status = "METADATA_FIELDS_PRESENT"
            rows.append({
                "bibkey": key,
                "entry_type": kind,
                "author": re.sub(r"[{}]", "", author),
                "title": clean_title(title),
                "year": year,
                "venue_or_type": clean_title(venue),
                "stable_locator": locator,
                "cited_in_manuscript": "yes",
                "required_fields_complete": "yes",
                "verification_status": status,
                "verification_basis": basis,
                "access_date": "",
            })
        require(bool(rows), "bibliography has no scholarly entries")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        summary = {
            "status": "PASS",
            "entries": len(rows),
            "cited_entries": len(cited),
            "missing_entries": 0,
            "uncited_entries": 0,
            "retained_calibration_records": sum(r["verification_status"] == "CALIBRATION_RECORD_PRESENT" for r in rows),
            "preconfigured_metadata_categories": sum(r["verification_status"] == "PRECONFIGURED_METADATA_CATEGORY" for r in rows),
            "other_metadata_field_records": sum(r["verification_status"] == "METADATA_FIELDS_PRESENT" for r in rows),
            "scope": "Static citation closure and metadata fields only; retained row presence and preconfigured categories are not source access or original reading. No primary sources are verified by this command.",
        }
    except (OSError, BibliographyAuditError, csv.Error) as error:
        summary = {"status": "FAIL", "reason": str(error)}
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
