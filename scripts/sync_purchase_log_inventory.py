#!/usr/bin/env python3
"""Sync imported purchase-log rows into structured inventory history for insights."""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4


IMPORT_NOTE_PREFIXES = (
    "Imported Blinkit CSV batch=",
    "Imported purchase CSV batch=",
)
SYNC_NOTE_PREFIX = "purchase_log_sync"


DEFAULT_INVENTORY_CATEGORIES = [
    {"name": "Fruits", "shelf_life_days": 5},
    {"name": "Vegetables", "shelf_life_days": 6},
    {"name": "Dal / Pulses", "shelf_life_days": 180},
    {"name": "Grains / Rice / Atta", "shelf_life_days": 150},
    {"name": "Oil / Ghee", "shelf_life_days": 240},
    {"name": "Masale / Spices", "shelf_life_days": 210},
    {"name": "Dry Fruits / Seeds", "shelf_life_days": 90},
    {"name": "Snacks / Makhana", "shelf_life_days": 60},
    {"name": "Pickles / Papad / Chutney", "shelf_life_days": 120},
    {"name": "Dairy / Eggs", "shelf_life_days": 7},
    {"name": "Protein / Health", "shelf_life_days": 120},
    {"name": "Frozen / Stored", "shelf_life_days": 120},
    {"name": "Beverages", "shelf_life_days": 45},
    {"name": "Cleaning", "shelf_life_days": 90},
    {"name": "Laundry", "shelf_life_days": 120},
    {"name": "Paper / Disposables", "shelf_life_days": 180},
    {"name": "Personal Care", "shelf_life_days": 180},
    {"name": "Utilities", "shelf_life_days": 240},
    {"name": "Maintenance", "shelf_life_days": 240},
    {"name": "Bathroom", "shelf_life_days": 120},
    {"name": "Kitchen Non-Food", "shelf_life_days": 120},
    {"name": "Other Supplies", "shelf_life_days": 120},
    {"name": "Home Supplies", "shelf_life_days": 90},
    {"name": "Other Kitchen", "shelf_life_days": 60},
]


def normalize_user_id(raw_value: str) -> str:
    value = re.sub(r"[^a-z0-9_-]+", "-", str(raw_value).strip().lower()).strip("-_")
    return value[:40]


def slugify_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\ufeff", "").split()).strip()


def try_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_store(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"User store not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"User store is not valid JSON: {path}") from exc


def save_store_atomic(path: Path, payload: dict[str, Any]) -> None:
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


def parse_purchase_timestamp(value: str) -> tuple[str, str]:
    text = clean_text(value)
    if not text:
        raise ValueError("missing purchase date/time")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt == "%Y-%m-%d":
            parsed = parsed.replace(hour=12, minute=0)
        return parsed.date().isoformat(), parsed.isoformat(timespec="seconds")
    raise ValueError(f"unsupported purchase date/time {value!r}")


def parse_quantity_text(text: str) -> tuple[float, str]:
    value = clean_text(text)
    match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*([A-Za-z].*)?$", value)
    if not match:
        raise ValueError(f"invalid quantity {text!r}")
    quantity = float(match.group(1))
    unit = clean_text(match.group(2) or "") or "unit"
    return quantity, unit


def category_id_for_name(profile: dict[str, Any], category_name: str) -> str:
    target = clean_text(category_name)
    alias_map = {
        "Dairy": "Dairy / Eggs",
        "Dry Fruits": "Dry Fruits / Seeds",
    }
    target = alias_map.get(target, target)
    for category in profile.get("inventory_categories", []):
        if clean_text(category.get("name", "")).casefold() == target.casefold():
            return category["id"]
    fallback = slugify_name(target or "Other Kitchen")
    known = {slugify_name(item["name"]): item["name"] for item in DEFAULT_INVENTORY_CATEGORIES}
    return slugify_name(known.get(fallback, "Other Kitchen"))


def imported_purchase_rows(profile: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in profile.get("purchase_log_rows", []):
        note = str(row.get("note", ""))
        if any(note.startswith(prefix) for prefix in IMPORT_NOTE_PREFIXES):
            rows.append(row)
    return rows


def sync_marker(row_id: str, batch_id: str) -> str:
    return f"{SYNC_NOTE_PREFIX}; batch={batch_id}; purchase_log_row_id={row_id}"


def synced_row_ids(profile: dict[str, Any]) -> set[str]:
    found = set()
    for entry in profile.get("inventory_transactions", []):
        note = str(entry.get("notes", ""))
        match = re.search(r"purchase_log_row_id=([a-f0-9]+)", note)
        if entry.get("source") == "purchase_log_sync" and match:
            found.add(match.group(1))
    return found


def inventory_item_lookup(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean_text(item.get("name", "")).casefold(): item for item in profile.get("inventory", [])}


def make_item(profile: dict[str, Any], item_name: str, category_id: str, unit: str, vendor: str, quantity: float, purchase_date: str) -> dict[str, Any]:
    return {
        "id": uuid4().hex,
        "name": item_name,
        "archived": False,
        "category_id": category_id,
        "unit": unit or "unit",
        "approx_status": "",
        "refill_level": None,
        "storage_capacity": None,
        "shelf_life_days": 0,
        "purchase_date": purchase_date,
        "opened_date": "",
        "expiry_date": "",
        "location_id": "",
        "preferred_vendor": vendor,
        "preferred_brand": "",
        "preferred_purchase_quantity": quantity,
        "preferred_purchase_unit": unit or "unit",
        "aliases": [],
        "notes": "",
        "lots": [],
    }


def make_lot(row: dict[str, Any], batch_id: str, quantity: float, unit: str, purchase_date: str) -> dict[str, Any]:
    return {
        "id": uuid4().hex,
        "quantity": quantity,
        "unit": unit or "unit",
        "status": "finished",
        "purchase_date": purchase_date,
        "opened_date": "",
        "expiry_date": "",
        "location_id": "",
        "vendor": clean_text(row.get("vendor", "")),
        "brand": "",
        "price": try_float(row.get("price")),
        "notes": sync_marker(row["id"], batch_id),
    }


def make_transaction(item: dict[str, Any], row: dict[str, Any], batch_id: str, quantity: float, unit: str, created_at: str) -> dict[str, Any]:
    return {
        "id": uuid4().hex,
        "created_at": created_at,
        "item_id": item["id"],
        "item_name": item["name"],
        "change_value": quantity,
        "unit": unit or "unit",
        "action": "Add",
        "reason": "purchase",
        "notes": sync_marker(row["id"], batch_id),
        "source": "purchase_log_sync",
    }


def prune_empty_items(profile: dict[str, Any]) -> None:
    kept = []
    for item in profile.get("inventory", []):
        if item.get("lots"):
            kept.append(item)
    profile["inventory"] = kept


def run_sync(store_path: Path, user_id: str, apply: bool, batch_id: str) -> int:
    store = load_store(store_path)
    profile = active_profile(store)
    imported_rows = imported_purchase_rows(profile)
    already_synced = synced_row_ids(profile)
    candidate_rows = []
    invalid_rows = []
    for row in imported_rows:
        if row.get("id") in already_synced:
            continue
        try:
            quantity, unit = parse_quantity_text(row.get("quantity", ""))
            purchase_date, created_at = parse_purchase_timestamp(row.get("date_time", ""))
        except ValueError as exc:
            invalid_rows.append(f"{row.get('id', '')}: {exc}")
            continue
        candidate_rows.append(
            {
                "row": row,
                "quantity": quantity,
                "unit": unit,
                "purchase_date": purchase_date,
                "created_at": created_at,
                "category_id": category_id_for_name(profile, row.get("category", "")),
            }
        )

    print(f"User ID: {user_id}")
    print(f"Store path: {store_path}")
    print(f"Active profile: {profile.get('name', '')} ({profile.get('id', '')})")
    print(f"Batch ID: {batch_id}")
    print("Dry-run summary:")
    print(f"  imported purchase-log rows found: {len(imported_rows)}")
    print(f"  already synced rows: {len(already_synced)}")
    print(f"  invalid rows: {len(invalid_rows)}")
    print(f"  rows to sync: {len(candidate_rows)}")
    if invalid_rows:
        print("Invalid rows:")
        for entry in invalid_rows:
            print(f"  - {entry}")

    if not apply:
        return 0

    item_map = inventory_item_lookup(profile)
    new_items = 0
    updated_items = 0
    for entry in candidate_rows:
        row = entry["row"]
        key = clean_text(row.get("item", "")).casefold()
        item = item_map.get(key)
        if not item:
            item = make_item(
                profile,
                clean_text(row.get("item", "")),
                entry["category_id"],
                entry["unit"],
                clean_text(row.get("vendor", "")),
                entry["quantity"],
                entry["purchase_date"],
            )
            profile.setdefault("inventory", []).append(item)
            item_map[key] = item
            new_items += 1
        else:
            if not item.get("preferred_vendor"):
                item["preferred_vendor"] = clean_text(row.get("vendor", ""))
            if not item.get("preferred_purchase_quantity"):
                item["preferred_purchase_quantity"] = entry["quantity"]
            if not item.get("preferred_purchase_unit"):
                item["preferred_purchase_unit"] = entry["unit"]
            updated_items += 1
        item.setdefault("lots", []).insert(
            0,
            make_lot(row, batch_id, entry["quantity"], entry["unit"], entry["purchase_date"]),
        )
        profile.setdefault("inventory_transactions", []).insert(
            0,
            make_transaction(item, row, batch_id, entry["quantity"], entry["unit"], entry["created_at"]),
        )

    save_store_atomic(store_path, store)

    reloaded = load_store(store_path)
    reloaded_profile = active_profile(reloaded)
    synced = [
        entry
        for entry in reloaded_profile.get("inventory_transactions", [])
        if entry.get("source") == "purchase_log_sync" and f"batch={batch_id}" in str(entry.get("notes", ""))
    ]
    print("Apply summary:")
    print(f"  synced transactions written: {len(synced)}")
    print(f"  new inventory items created: {new_items}")
    print(f"  existing inventory items updated: {updated_items}")
    print(f"  inventory count after sync: {len(reloaded_profile.get('inventory', []))}")
    print(f"  inventory transaction count after sync: {len(reloaded_profile.get('inventory_transactions', []))}")
    return len(synced)


def rollback_batch(store_path: Path, batch_id: str) -> None:
    store = load_store(store_path)
    profile = active_profile(store)
    before_tx = len(profile.get("inventory_transactions", []))
    profile["inventory_transactions"] = [
        entry
        for entry in profile.get("inventory_transactions", [])
        if not (entry.get("source") == "purchase_log_sync" and f"batch={batch_id}" in str(entry.get("notes", "")))
    ]
    removed_tx = before_tx - len(profile["inventory_transactions"])
    removed_lots = 0
    for item in profile.get("inventory", []):
        before_lots = len(item.get("lots", []))
        item["lots"] = [
            lot
            for lot in item.get("lots", [])
            if f"batch={batch_id}" not in str(lot.get("notes", ""))
        ]
        removed_lots += before_lots - len(item["lots"])
    prune_empty_items(profile)
    save_store_atomic(store_path, store)
    print(f"Rollback batch={batch_id}: removed {removed_tx} transactions and {removed_lots} lots.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--rollback-batch", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    user_id = normalize_user_id(args.user_id)
    if user_id != "shreya":
        raise SystemExit(f"Refusing sync for user {args.user_id!r}; only 'shreya' is allowed for this one-off.")
    store_path = Path("data") / user_id / "profiles_data.json"
    if not store_path.exists():
        raise SystemExit(f"User 'shreya' does not exist at {store_path}.")
    if args.rollback_batch:
        rollback_batch(store_path, args.rollback_batch)
        return 0
    batch_id = args.batch_id or datetime.now().strftime("purchase-log-sync-%Y%m%d-%H%M%S")
    synced = run_sync(store_path, user_id, args.apply, batch_id)
    if args.apply:
        print(
            "Rollback command:\n"
            f"  ./.venv/bin/python scripts/sync_purchase_log_inventory.py --user-id shreya --rollback-batch {batch_id}"
        )
        print(f"Synced rows: {synced}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
