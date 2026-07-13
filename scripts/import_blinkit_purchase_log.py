#!/usr/bin/env python3
"""One-off backend importer for purchase CSVs into a user profile store."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4


DEFAULT_TIME = "12:00"
IMPORT_NOTE_PREFIX = "Imported purchase CSV batch="
LEGACY_IMPORT_NOTE_PREFIXES = (
    "Imported Blinkit CSV batch=",
    "Imported purchase CSV batch=",
)
HEADER_ALIASES = {
    "vendor": "vendor",
    "item": "item",
    "product name": "item",
    "product": "item",
    "quantity": "quantity",
    "qty": "quantity",
    "price (inr)": "price",
    "price": "price",
    "total price": "price",
    "date & time": "date_time",
    "date": "date_time",
    "purchase date": "date_time",
    "purchase date/time": "date_time",
    "category": "category",
}
REQUIRED_COLUMNS = {"vendor", "item", "quantity", "price", "date_time"}


@dataclass
class ParsedRow:
    source_file: str
    source_row_number: int
    vendor: str
    item: str
    quantity: str
    price: str
    date_time: str
    category: str
    key: tuple[str, str, str, str, str]


def normalize_user_id(raw_value: str) -> str:
    value = re.sub(r"[^a-z0-9_-]+", "-", str(raw_value).strip().lower()).strip("-_")
    return value[:40]


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\ufeff", "").split()).strip()


def normalize_item_name(value: str) -> str:
    return clean_text(value).casefold()


def normalize_quantity(value: str) -> str:
    return clean_text(value)


def normalize_price(value: str) -> str:
    text = clean_text(value).replace(",", "")
    if text.startswith("₹"):
        text = text[1:].strip()
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid price {value!r}") from exc
    if amount < 0:
        raise ValueError(f"negative price {value!r}")
    return format(amount.quantize(Decimal("0.01")), "f")


def normalize_vendor(value: str) -> str:
    vendor = clean_text(value) or "Blinkit"
    return "Blinkit" if vendor.casefold() == "blinkit" else vendor


def normalize_category(value: str) -> str:
    return clean_text(value)


def normalize_date_time(value: str) -> str:
    text = clean_text(value)
    if not text:
        raise ValueError("missing date/time")
    for fmt in (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %I:%M %p",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt in {"%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"}:
            parsed = parsed.replace(hour=12, minute=0)
        return parsed.strftime("%Y-%m-%d %H:%M")
    raise ValueError(f"unsupported date/time format {value!r}")


def dedupe_key(vendor: str, item: str, quantity: str, price: str, date_time: str) -> tuple[str, str, str, str, str]:
    return (
        clean_text(vendor).casefold(),
        normalize_item_name(item),
        normalize_quantity(quantity).casefold(),
        normalize_price(price),
        normalize_date_time(date_time),
    )


def load_store(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"User store not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"User store is not valid JSON: {path}") from exc


def save_store_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def active_profile(store: dict[str, Any]) -> dict[str, Any]:
    active_id = store.get("active_profile_id")
    for profile in store.get("profiles", []):
        if profile.get("id") == active_id:
            return profile
    raise SystemExit("Active profile not found in user store.")


def existing_duplicate_keys(profile: dict[str, Any]) -> set[tuple[str, str, str, str, str]]:
    keys: set[tuple[str, str, str, str, str]] = set()
    for row in profile.get("purchase_log_rows", []):
        try:
            keys.add(
                dedupe_key(
                    row.get("vendor", ""),
                    row.get("item", ""),
                    row.get("quantity", ""),
                    row.get("price", ""),
                    row.get("date_time", ""),
                )
            )
        except ValueError:
            continue
    return keys


def row_note(batch_id: str, source_file: str, source_row_number: int) -> str:
    return f"{IMPORT_NOTE_PREFIX}{batch_id}; source_file={source_file}; source_row={source_row_number}"


def batch_note_matches(note: str, batch_id: str) -> bool:
    text = str(note or "")
    return any(text.startswith(f"{prefix}{batch_id}") for prefix in LEGACY_IMPORT_NOTE_PREFIXES)


def canonical_fieldnames(fieldnames: list[str] | None) -> dict[str, str]:
    if not fieldnames:
        return {}
    mapped = {}
    for name in fieldnames:
        canonical = HEADER_ALIASES.get(clean_text(name).casefold())
        if canonical:
            mapped[canonical] = name
    return mapped


def parse_csv_rows(csv_path: Path) -> tuple[list[ParsedRow], list[str]]:
    valid_rows: list[ParsedRow] = []
    errors: list[str] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = canonical_fieldnames(reader.fieldnames)
        missing = sorted(REQUIRED_COLUMNS - set(fields))
        if missing:
            errors.append(
                f"{csv_path.name}: invalid header {reader.fieldnames!r}; missing canonical columns {missing!r}"
            )
            return valid_rows, errors
        for source_row_number, raw in enumerate(reader, start=2):
            try:
                item = clean_text(raw.get(fields["item"], ""))
                if not item:
                    raise ValueError("missing item")
                vendor = normalize_vendor(raw.get(fields["vendor"], ""))
                quantity = normalize_quantity(raw.get(fields["quantity"], ""))
                if not quantity:
                    raise ValueError("missing quantity")
                price = normalize_price(raw.get(fields["price"], ""))
                date_time = normalize_date_time(raw.get(fields["date_time"], ""))
                category = normalize_category(raw.get(fields.get("category", ""), "")) if fields.get("category") else ""
                valid_rows.append(
                    ParsedRow(
                        source_file=csv_path.name,
                        source_row_number=source_row_number,
                        vendor=vendor,
                        item=item,
                        quantity=quantity,
                        price=price,
                        date_time=date_time,
                        category=category,
                        key=dedupe_key(vendor, item, quantity, price, date_time),
                    )
                )
            except ValueError as exc:
                errors.append(f"{csv_path.name}:{source_row_number}: {exc}")
    return valid_rows, errors


def import_rows(
    store_path: Path,
    user_id: str,
    csv_paths: list[Path],
    apply: bool,
    batch_id: str,
) -> int:
    store = load_store(store_path)
    profile = active_profile(store)
    current_rows = profile.setdefault("purchase_log_rows", [])
    existing_keys = existing_duplicate_keys(profile)

    total_rows = 0
    invalid_rows: list[str] = []
    valid_rows: list[ParsedRow] = []
    for csv_path in csv_paths:
        parsed_rows, errors = parse_csv_rows(csv_path)
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            total_rows += max(sum(1 for _ in handle) - 1, 0)
        valid_rows.extend(parsed_rows)
        invalid_rows.extend(errors)

    seen_in_batch: set[tuple[str, str, str, str, str]] = set()
    duplicate_rows: list[str] = []
    rows_to_insert: list[ParsedRow] = []
    for row in valid_rows:
        if row.key in existing_keys:
            duplicate_rows.append(
                f"{row.source_file}:{row.source_row_number}: duplicate of existing record"
            )
            continue
        if row.key in seen_in_batch:
            duplicate_rows.append(
                f"{row.source_file}:{row.source_row_number}: duplicate within import batch"
            )
            continue
        seen_in_batch.add(row.key)
        rows_to_insert.append(row)

    print(f"User ID: {user_id}")
    print(f"Store path: {store_path}")
    print(f"Active profile: {profile.get('name', '')} ({profile.get('id', '')})")
    print(f"Batch ID: {batch_id}")
    print("Dry-run summary:")
    print(f"  total CSV rows: {total_rows}")
    print(f"  valid rows: {len(valid_rows)}")
    print(f"  duplicate/skipped rows: {len(duplicate_rows)}")
    print(f"  invalid rows: {len(invalid_rows)}")
    print(f"  rows to be inserted: {len(rows_to_insert)}")

    if duplicate_rows:
        print("Skipped duplicates:")
        for entry in duplicate_rows:
            print(f"  - {entry}")
    if invalid_rows:
        print("Invalid rows:")
        for entry in invalid_rows:
            print(f"  - {entry}")

    if not apply:
        return 0

    for row in rows_to_insert:
        current_rows.insert(
            0,
            {
                "id": uuid4().hex,
                "in_stock": True,
                "date_time": row.date_time,
                "vendor": row.vendor,
                "item": row.item,
                "quantity": row.quantity,
                "price": row.price,
                "note": row_note(batch_id, row.source_file, row.source_row_number),
                "category": row.category,
            },
        )

    save_store_atomic(store_path, store)

    reloaded = load_store(store_path)
    reloaded_profile = active_profile(reloaded)
    imported = [
        row
        for row in reloaded_profile.get("purchase_log_rows", [])
        if batch_note_matches(row.get("note", ""), batch_id)
    ]
    print("Import verification:")
    print(f"  inserted records found for batch: {len(imported)}")
    print(f"  total purchase_log_rows after import: {len(reloaded_profile.get('purchase_log_rows', []))}")
    return len(imported)


def rollback_batch(store_path: Path, batch_id: str) -> int:
    store = load_store(store_path)
    profile = active_profile(store)
    rows = profile.get("purchase_log_rows", [])
    kept = [
        row
        for row in rows
        if not batch_note_matches(row.get("note", ""), batch_id)
    ]
    removed = len(rows) - len(kept)
    profile["purchase_log_rows"] = kept
    if removed:
        save_store_atomic(store_path, store)
    print(f"Rollback batch={batch_id}: removed {removed} records from purchase_log_rows.")
    return removed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", required=True, help="Planner user ID to import into.")
    parser.add_argument("--csv", dest="csv_paths", action="append", default=[], help="CSV path to import. Pass more than once for multiple files.")
    parser.add_argument("--apply", action="store_true", help="Write changes to the store after dry-run validation.")
    parser.add_argument("--batch-id", default="", help="Stable batch ID for apply/rollback runs.")
    parser.add_argument("--rollback-batch", default="", help="Remove only records previously created by the given batch ID.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    normalized_user = normalize_user_id(args.user_id)
    if normalized_user != "shreya":
        raise SystemExit(f"Refusing import: requested user_id={args.user_id!r} normalizes to {normalized_user!r}, not 'shreya'.")
    store_path = Path("data") / normalized_user / "profiles_data.json"
    if not store_path.exists():
        raise SystemExit(f"User 'shreya' does not exist at {store_path}.")
    if args.rollback_batch:
        return 0 if rollback_batch(store_path, args.rollback_batch) >= 0 else 1
    if not args.csv_paths:
        raise SystemExit("Provide at least one --csv path.")
    csv_paths = [Path(path) for path in args.csv_paths]
    missing = [str(path) for path in csv_paths if not path.exists()]
    if missing:
        raise SystemExit(f"Missing CSV file(s): {', '.join(missing)}")
    batch_id = args.batch_id or datetime.now().strftime("blinkit-%Y%m%d-%H%M%S")
    inserted = import_rows(store_path, normalized_user, csv_paths, args.apply, batch_id)
    if args.apply:
        print(
            "Rollback command:\n"
            f"  ./.venv/bin/python scripts/import_blinkit_purchase_log.py --user-id shreya --rollback-batch {batch_id}"
        )
        print(f"Inserted rows: {inserted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
