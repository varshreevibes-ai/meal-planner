from collections import OrderedDict
from copy import deepcopy
import csv
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from io import StringIO
import json
from pathlib import Path
import re
import random
from uuid import uuid4

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yaml

DATA = yaml.safe_load(Path("meal_data.yaml").read_text())
MEAL_LOG_PATH = Path("meal_log.json")
PROFILE_STORE_PATH = Path("profiles_data.json")
DATA_ROOT = Path("data")
USER_PREFERENCE_PATH = DATA_ROOT / "device_user.json"
MAX_PROFILE_MEMBERS = 5
PROJECT_DEFAULT_MEMBERS = [
    {
        "name": "Shreya",
        "portion_ratio": 1.0,
        "goes_to_gym": "No",
        "walks_regularly": "Yes",
        "intake_items": "Warm water with ghee, soaked dates, soaked almonds, soaked pumpkin seeds, soaked kali kishmish, anar bowl, protein shake with warm water",
    },
    {
        "name": "Varshit",
        "portion_ratio": 1.25,
        "goes_to_gym": "No",
        "walks_regularly": "Yes",
        "intake_items": "Soya milk with banana, anar bowl, sattu drink, 3 cucumbers salad, digestion aids",
    },
]
PROJECT_DEFAULT_BEFORE_DIDI = "\n".join(
    [
        "Soak dates, almonds, pumpkin seeds, and kali kishmish for the next morning.",
        "Wash and keep cucumbers ready for Varshit.",
        "Check that all required ingredients for brunch, add-ons, and dinner are already available.",
        "Check whether sattu, protein powder, and soya milk are running low.",
    ]
)
PROJECT_DEFAULT_MORNING = "\n".join(
    [
        "Shreya starts with warm water and ghee.",
        "Serve soaked dates, almonds, pumpkin seeds, and kali kishmish.",
        "Varshit has soya milk plus banana around morning calisthenics.",
        "Prepare anar bowls for both.",
        "Keep digestion aids ready for the day.",
        "Start the main cooking for brunch and dinner.",
    ]
)
NUTRITION = {
    "routine": {"you": {"calories": 260, "protein": 18}, "varshit": {"calories": 480, "protein": 24}},
    "Avocado Toast": {"you": {"calories": 240, "protein": 6}, "varshit": {"calories": 320, "protein": 9}},
    "Avocado Salad": {"you": {"calories": 220, "protein": 8}, "varshit": {"calories": 300, "protein": 12}},
    "Chickpea Tacos": {"you": {"calories": 330, "protein": 10}, "varshit": {"calories": 430, "protein": 14}},
    "Delhi Style Matar Chaat": {"you": {"calories": 280, "protein": 10}, "varshit": {"calories": 360, "protein": 14}},
    "Poha": {"you": {"calories": 230, "protein": 5}, "varshit": {"calories": 320, "protein": 7}},
    "Upma": {"you": {"calories": 250, "protein": 6}, "varshit": {"calories": 340, "protein": 8}},
    "Idli Sambar": {"you": {"calories": 240, "protein": 8}, "varshit": {"calories": 320, "protein": 11}},
    "Bhaji Roti": {"you": {"calories": 260, "protein": 7}, "varshit": {"calories": 340, "protein": 10}},
    "Baingan Bharta Roti": {"you": {"calories": 250, "protein": 7}, "varshit": {"calories": 330, "protein": 9}},
    "Chane Sabji Roti": {"you": {"calories": 300, "protein": 12}, "varshit": {"calories": 390, "protein": 16}},
    "Rice Paper Rolls": {"you": {"calories": 260, "protein": 9}, "varshit": {"calories": 360, "protein": 13}},
    "Tofu Tikka Roll": {"you": {"calories": 320, "protein": 16}, "varshit": {"calories": 410, "protein": 22}},
    "Daal Chawal": {"you": {"calories": 270, "protein": 10}, "varshit": {"calories": 340, "protein": 13}},
    "Rajma Chawal": {"you": {"calories": 310, "protein": 11}, "varshit": {"calories": 390, "protein": 15}},
    "Uttapam and Ghee Podi Dosa": {"you": {"calories": 300, "protein": 7}, "varshit": {"calories": 370, "protein": 9}},
    "Morning Portion Only": {"you": {"calories": 180, "protein": 6}, "varshit": {"calories": 240, "protein": 9}},
    "Light Soup or Salad Plate": {"you": {"calories": 110, "protein": 3}, "varshit": {"calories": 150, "protein": 4}},
    "Moong Chilla Light Dinner": {"you": {"calories": 210, "protein": 10}, "varshit": {"calories": 280, "protein": 13}},
    "Soup Light Dinner": {"you": {"calories": 140, "protein": 4}, "varshit": {"calories": 190, "protein": 6}},
}
DAY_PLANS = {
    "Today": {"brunch": "Rajma Chawal", "dinner": "Morning Portion Only"},
    "Monday": {"brunch": "Idli Sambar", "dinner": "Morning Portion Only"},
    "Tuesday": {"brunch": "Uttapam and Ghee Podi Dosa", "dinner": "Morning Portion Only"},
    "Wednesday": {"brunch": "Chane Sabji Roti", "dinner": "Soup Light Dinner"},
    "Thursday": {"brunch": "Daal Chawal", "dinner": "Morning Portion Only"},
    "Friday": {"brunch": "Avocado Toast", "dinner": "Soup Light Dinner"},
    "Saturday": {"brunch": "Chickpea Tacos", "dinner": "Morning Portion Only"},
    "Sunday": {"brunch": "Tofu Tikka Roll", "dinner": "Morning Portion Only"},
}
PORTIONS = {
    "Avocado Toast": {"you": "2 toast", "varshit": "2 to 3 toast"},
    "Avocado Salad": {"you": "1 medium bowl", "varshit": "1 large bowl"},
    "Chickpea Tacos": {"you": "2 tacos", "varshit": "3 tacos"},
    "Delhi Style Matar Chaat": {"you": "1 bowl + 2 rotis", "varshit": "1.5 bowls + 4 rotis"},
    "Poha": {"you": "1 medium bowl", "varshit": "1.5 bowls"},
    "Upma": {"you": "1 medium bowl", "varshit": "1.5 bowls"},
    "Idli Sambar": {"you": "2 idli + 1 bowl sambar", "varshit": "3 idli + 1.5 bowls sambar"},
    "Bhaji Roti": {"you": "1 roti + more bhaji", "varshit": "2 roti + bhaji + cucumber salad"},
    "Baingan Bharta Roti": {"you": "1 roti + more bharta", "varshit": "2 roti + bharta + cucumber salad"},
    "Chane Sabji Roti": {"you": "1 roti + 1 bowl chane", "varshit": "2 roti + 1.5 bowls chane"},
    "Rice Paper Rolls": {"you": "2 rolls", "varshit": "3 rolls"},
    "Tofu Tikka Roll": {"you": "1 roll", "varshit": "1.5 rolls"},
    "Daal Chawal": {"you": "1 bowl dal + 1/2 to 3/4 bowl rice", "varshit": "1.5 bowls dal + 1 bowl rice"},
    "Rajma Chawal": {"you": "1 bowl rajma + 1/2 bowl rice", "varshit": "1.5 bowls rajma + 3/4 to 1 bowl rice"},
    "Uttapam and Ghee Podi Dosa": {"you": "1 ghee podi dosa", "varshit": "1 uttapam + sambar"},
    "Morning Portion Only": {"you": "1 small leftover bowl", "varshit": "1 medium leftover bowl"},
    "Light Soup or Salad Plate": {"you": "1 soup bowl", "varshit": "1 soup bowl + cucumber salad"},
    "Moong Chilla Light Dinner": {"you": "1 to 2 soft chilla", "varshit": "2 chilla"},
    "Soup Light Dinner": {"you": "1 soup bowl", "varshit": "1 larger soup bowl"},
}


def recipe_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")


def normalize_user_id(raw_value):
    value = re.sub(r"[^a-z0-9_-]+", "-", str(raw_value).strip().lower()).strip("-_")
    return value[:40]


def user_storage_dir(user_id):
    return DATA_ROOT / user_id


def user_profile_store_path(user_id):
    return user_storage_dir(user_id) / "profiles_data.json"


def load_remembered_user_id():
    if not USER_PREFERENCE_PATH.exists():
        return ""
    try:
        payload = json.loads(USER_PREFERENCE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return ""
    return normalize_user_id(payload.get("planner_user_id", ""))


def save_remembered_user_id(user_id):
    USER_PREFERENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    USER_PREFERENCE_PATH.write_text(json.dumps({"planner_user_id": normalize_user_id(user_id)}, indent=2))


def clear_remembered_user_id():
    if USER_PREFERENCE_PATH.exists():
        USER_PREFERENCE_PATH.unlink()


def recipe_anchor_id(name):
    return f"recipe-{recipe_slug(name)}"


def dish_names(section):
    return [dish["name"] for dish in DATA["sections"][section]]


def get_dish(section, name):
    return next(dish for dish in DATA["sections"][section] if dish["name"] == name)


def all_recipe_dishes():
    dishes = []
    for section in DATA["sections"].values():
        dishes.extend(section)
    dedup = {}
    for dish in dishes:
        if dish["name"] == "Morning Portion Only":
            continue
        dedup[dish["name"]] = dish
    return list(dedup.values())


def nutrition_for(name):
    return NUTRITION.get(name, {"you": {"calories": 0, "protein": 0}, "varshit": {"calories": 0, "protein": 0}})


def portion_factor(text, default=1.0):
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(text))]
    if not nums:
        return default
    if "to" in str(text) and len(nums) >= 2:
        return sum(nums[:2]) / 2
    return nums[0]


def sedentary_tdee_from_weight(weight_kg):
    return round(22 * weight_kg)


def format_number(value):
    if value is None or value == "":
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


ROUTINE_FIELD_DEFS = [
    ("routine_supplements", "Routine supplements"),
    ("routine_medicines", "Routine medicines"),
    ("juice_preference", "Juice preference"),
    ("protein_preference", "Protein preference"),
    ("dry_fruits_preference", "Dry fruits preference"),
    ("other_add_ons", "Other routine add-ons"),
]

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
HOME_SUPPLY_CATEGORY_NAMES = {
    "Cleaning",
    "Laundry",
    "Paper / Disposables",
    "Personal Care",
    "Utilities",
    "Maintenance",
    "Bathroom",
    "Kitchen Non-Food",
    "Other Supplies",
    "Home Supplies",
}

DEFAULT_STORAGE_LOCATIONS = [
    "Fridge",
    "Freezer",
    "Kitchen shelf",
    "Masala box",
    "Store room",
    "Bathroom cabinet",
    "Utility shelf",
    "Laundry shelf",
    "Cleaning rack",
    "Counter",
    "Other",
]

INVENTORY_SECTIONS = ["Overview", "Items", "Expiry", "Adjustments", "Storage", "Analytics"]
INVENTORY_ADJUSTMENT_REASONS = [
    "manual",
    "purchase",
    "usage",
    "expired",
    "perished/spoiled",
    "spilled/lost",
    "given away",
    "moved",
    "manual correction",
]
SHOPPING_REASON_LABELS = {
    "below_refill": "Below refill level",
    "run_out_soon": "Will run out soon",
    "avg_interval": "Average purchase interval reached",
    "meal_plan": "Needed for meal plan",
    "seasonal": "Seasonal suggestion",
    "home_supply_low": "Home supply low",
    "manual": "Manual add",
}
SEASONAL_ITEMS = {
    "Summer": ["mango", "litchi", "jamun", "watermelon", "cucumber", "curd", "buttermilk"],
    "Winter": ["carrot", "peas", "sarson", "gur", "dry fruits", "soup"],
}
DEFAULT_VENDOR_RECORDS = [
    {"name": "BigBasket", "vendor_type": "Grocery app", "preferred_categories": ["Fruits", "Dairy / Eggs", "Protein / Health"]},
    {"name": "Sabzi Vendor", "vendor_type": "Local vegetable vendor", "preferred_categories": ["Vegetables"]},
    {"name": "Kirana", "vendor_type": "Kirana", "preferred_categories": ["Masale / Spices", "Grains / Rice / Atta", "Dal / Pulses", "Dry Fruits / Seeds", "Oil / Ghee", "Pickles / Papad / Chutney"]},
    {"name": "Pharmacy", "vendor_type": "Pharmacy", "preferred_categories": ["Personal Care", "Bathroom"]},
    {"name": "Amazon / DMart", "vendor_type": "Marketplace", "preferred_categories": ["Cleaning", "Laundry", "Paper / Disposables", "Utilities", "Maintenance", "Kitchen Non-Food", "Other Supplies"]},
    {"name": "Other", "vendor_type": "Other", "preferred_categories": []},
]
WASTE_REASONS = {"mark expired", "mark perished/spoiled", "mark spilled/lost", "mark given away", "expired", "perished/spoiled", "spilled/lost", "given away"}


def try_float(value):
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_ingredient_lines(text):
    ingredients = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        ingredients.append(
            {
                "id": uuid4().hex,
                "name": parts[0],
                "quantity": try_float(parts[1]) if len(parts) > 1 else None,
                "unit": parts[2] if len(parts) > 2 else "",
                "notes": parts[3] if len(parts) > 3 else "",
                "cost_value": None,
                "cost_unit": "",
                "calories": None,
                "protein": None,
                "fat": None,
                "carbohydrates": None,
            }
        )
    return ingredients


def ingredient_lines_from_recipe(recipe):
    lines = []
    for item in recipe.get("ingredients", []):
        qty = format_number(item.get("quantity"))
        unit = item.get("unit", "")
        notes = item.get("notes", "")
        parts = [item.get("name", "")]
        if qty:
            parts.append(qty)
        if unit:
            parts.append(unit)
        if notes:
            parts.append(notes)
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def instructions_text(lines):
    return "\n".join(lines or [])


def normalize_member(member, legacy_preferences=None):
    legacy_preferences = legacy_preferences or {}
    legacy_intake_lines = []
    for key, _label in ROUTINE_FIELD_DEFS:
        legacy_intake_lines.extend(split_list_items(member.get(key, "")))
    normalized = {
        "id": member.get("id", uuid4().hex),
        "name": member.get("name", "Member"),
        "portion_ratio": try_float(member.get("portion_ratio")) or 1.0,
        "goes_to_gym": member.get("goes_to_gym", legacy_preferences.get("goes_to_gym", "No")),
        "walks_regularly": member.get("walks_regularly", legacy_preferences.get("walks_regularly", "Yes")),
        "intake_items": member.get("intake_items", "\n".join(legacy_intake_lines)),
    }
    for key, _label in ROUTINE_FIELD_DEFS:
        normalized[key] = member.get(key, "")
    return normalized


def project_default_members():
    return [normalize_member(member) for member in PROJECT_DEFAULT_MEMBERS]


def should_bootstrap_project_household(profile):
    return (
        not profile.get("household_members")
        and not profile.get("meal_templates")
        and not profile.get("recipes")
        and not profile.get("inventory")
        and not profile.get("meal_log")
    )


def apply_project_household_defaults(profile):
    if not should_bootstrap_project_household(profile):
        return profile
    profile["name"] = profile.get("name") or "Varhshree Household"
    profile["household_members"] = project_default_members()
    profile["preferences"]["before_didi_arrives"] = profile.get("preferences", {}).get("before_didi_arrives") or PROJECT_DEFAULT_BEFORE_DIDI
    profile["preferences"]["morning_routine"] = profile.get("preferences", {}).get("morning_routine") or PROJECT_DEFAULT_MORNING
    profile["preferences"]["setup_complete"] = True
    return profile


def normalize_template(template):
    return {
        "id": template.get("id", uuid4().hex),
        "name": template.get("name", "Untitled Template"),
        "description": template.get("description", ""),
        "linked_recipe_ref": template.get("linked_recipe_ref", ""),
        "favorite": bool(template.get("favorite", False)),
    }


def normalize_recipe(recipe):
    ingredients = []
    for item in recipe.get("ingredients", []):
        ingredients.append(
            {
                "id": item.get("id", uuid4().hex),
                "name": item.get("name", ""),
                "quantity": try_float(item.get("quantity")),
                "unit": item.get("unit", ""),
                "notes": item.get("notes", ""),
                "cost_value": try_float(item.get("cost_value")),
                "cost_unit": item.get("cost_unit", ""),
                "calories": try_float(item.get("calories")),
                "protein": try_float(item.get("protein")),
                "fat": try_float(item.get("fat")),
                "carbohydrates": try_float(item.get("carbohydrates")),
            }
        )
    return {
        "id": recipe.get("id", uuid4().hex),
        "name": recipe.get("name", "Untitled Recipe"),
        "description": recipe.get("description", ""),
        "base_servings": try_float(recipe.get("base_servings")) or 2.0,
        "ingredients": ingredients,
        "instructions": list(recipe.get("instructions", [])),
        "youtube": recipe.get("youtube", ""),
        "favorite": bool(recipe.get("favorite", False)),
    }


def today_iso():
    return date.today().isoformat()


def slugify_name(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")


def default_inventory_categories():
    category_defaults = {
        "Fruits": {"default_unit": "kg", "default_refill_level": 1.0, "default_location_name": "Fridge", "default_vendor_name": "BigBasket", "approx_tracking_mode": "fresh", "exact_tracking_mode": "small fresh purchase"},
        "Vegetables": {"default_unit": "kg", "default_refill_level": 1.0, "default_location_name": "Fridge", "default_vendor_name": "Sabzi Vendor", "approx_tracking_mode": "fresh", "exact_tracking_mode": "small fresh purchase"},
        "Dal / Pulses": {"default_unit": "kg", "default_refill_level": 0.5, "default_location_name": "Kitchen shelf", "default_vendor_name": "Kirana", "approx_tracking_mode": "bulk", "exact_tracking_mode": "sealed packs"},
        "Grains / Rice / Atta": {"default_unit": "kg", "default_refill_level": 1.0, "default_location_name": "Store room", "default_vendor_name": "Kirana", "approx_tracking_mode": "bulk", "exact_tracking_mode": "sealed packs"},
        "Cleaning": {"default_unit": "bottle", "default_refill_level": 1.0, "default_location_name": "Cleaning rack", "default_vendor_name": "Amazon / DMart", "approx_tracking_mode": "unit", "exact_tracking_mode": "bottle/pack"},
        "Laundry": {"default_unit": "pack", "default_refill_level": 1.0, "default_location_name": "Laundry shelf", "default_vendor_name": "Amazon / DMart", "approx_tracking_mode": "unit", "exact_tracking_mode": "pack"},
        "Paper / Disposables": {"default_unit": "pack", "default_refill_level": 1.0, "default_location_name": "Store room", "default_vendor_name": "Amazon / DMart", "approx_tracking_mode": "unit", "exact_tracking_mode": "pack"},
        "Personal Care": {"default_unit": "pc", "default_refill_level": 1.0, "default_location_name": "Bathroom cabinet", "default_vendor_name": "Pharmacy", "approx_tracking_mode": "unit", "exact_tracking_mode": "tube/bottle"},
    }
    return [
        {
            "id": slugify_name(item["name"]),
            "name": item["name"],
            "shelf_life_days": item["shelf_life_days"],
            "default_unit": category_defaults.get(item["name"], {}).get("default_unit", "unit"),
            "default_refill_level": category_defaults.get(item["name"], {}).get("default_refill_level"),
            "default_location_name": category_defaults.get(item["name"], {}).get("default_location_name", ""),
            "default_vendor_name": category_defaults.get(item["name"], {}).get("default_vendor_name", ""),
            "approx_tracking_mode": category_defaults.get(item["name"], {}).get("approx_tracking_mode", "general"),
            "exact_tracking_mode": category_defaults.get(item["name"], {}).get("exact_tracking_mode", "quantity"),
        }
        for item in DEFAULT_INVENTORY_CATEGORIES
    ]


def default_storage_locations():
    return [
        {
            "id": slugify_name(name),
            "name": name,
            "capacity_value": None,
            "capacity_unit": "",
            "notes": "",
        }
        for name in DEFAULT_STORAGE_LOCATIONS
    ]


def normalize_inventory_category(category):
    default_map = {item["name"]: item["shelf_life_days"] for item in DEFAULT_INVENTORY_CATEGORIES}
    default_lookup = {item["id"]: item for item in default_inventory_categories()}
    name = category.get("name", "Other Kitchen").strip() or "Other Kitchen"
    category_id = category.get("id", slugify_name(name))
    defaults = default_lookup.get(category_id, {})
    return {
        "id": category_id,
        "name": name,
        "shelf_life_days": int(try_float(category.get("shelf_life_days")) or default_map.get(name, 60)),
        "default_unit": category.get("default_unit", defaults.get("default_unit", "unit")),
        "default_refill_level": try_float(category.get("default_refill_level")) if category.get("default_refill_level") not in ("", None) else defaults.get("default_refill_level"),
        "default_location_name": category.get("default_location_name", defaults.get("default_location_name", "")),
        "default_vendor_name": category.get("default_vendor_name", defaults.get("default_vendor_name", "")),
        "approx_tracking_mode": category.get("approx_tracking_mode", defaults.get("approx_tracking_mode", "general")),
        "exact_tracking_mode": category.get("exact_tracking_mode", defaults.get("exact_tracking_mode", "quantity")),
    }


def normalize_storage_location(location):
    name = location.get("name", "Other").strip() or "Other"
    return {
        "id": location.get("id", slugify_name(name)),
        "name": name,
        "capacity_value": try_float(location.get("capacity_value")),
        "capacity_unit": location.get("capacity_unit", ""),
        "notes": location.get("notes", ""),
    }


def default_vendor_records():
    return [
        {
            "id": slugify_name(item["name"]),
            "name": item["name"],
            "vendor_type": item["vendor_type"],
            "preferred_categories": list(item.get("preferred_categories", [])),
            "notes": "",
            "purchase_pattern": "",
            "price_trend_summary": "",
        }
        for item in DEFAULT_VENDOR_RECORDS
    ]


def normalize_vendor_record(record):
    name = record.get("name", "Other").strip() or "Other"
    return {
        "id": record.get("id", slugify_name(name)),
        "name": name,
        "vendor_type": record.get("vendor_type", "Other"),
        "preferred_categories": list(record.get("preferred_categories", [])),
        "notes": record.get("notes", ""),
        "purchase_pattern": record.get("purchase_pattern", ""),
        "price_trend_summary": record.get("price_trend_summary", ""),
    }


def normalize_manual_shopping_item(item):
    return {
        "id": item.get("id", uuid4().hex),
        "item_name": item.get("item_name", "Manual item").strip() or "Manual item",
        "quantity": try_float(item.get("quantity")) or 1.0,
        "unit": item.get("unit", "unit").strip() or "unit",
        "vendor_name": item.get("vendor_name", "Other").strip() or "Other",
        "brand": item.get("brand", "").strip(),
        "notes": item.get("notes", "").strip(),
        "status": item.get("status", "active"),
        "created_at": item.get("created_at") or datetime.now().isoformat(timespec="seconds"),
    }


def normalize_purchase_review_item(item):
    return {
        "id": item.get("id", uuid4().hex),
        "detected_name": item.get("detected_name", "Item").strip() or "Item",
        "item_name": item.get("item_name", item.get("detected_name", "Item")).strip() or "Item",
        "matched_item_id": item.get("matched_item_id", ""),
        "category_id": item.get("category_id", slugify_name("Other Kitchen")),
        "destination": item.get("destination", "Inventory"),
        "quantity": try_float(item.get("quantity")) or 0.0,
        "unit": item.get("unit", "unit").strip() or "unit",
        "packet_format": item.get("packet_format", "").strip(),
        "brand": item.get("brand", "").strip(),
        "vendor_name": item.get("vendor_name", "Other").strip() or "Other",
        "price": try_float(item.get("price")),
        "purchase_date": item.get("purchase_date", today_iso()).strip() or today_iso(),
        "location_id": item.get("location_id", ""),
        "confidence": item.get("confidence", "Low"),
        "parse_source": item.get("parse_source", "manual"),
        "raw_text": item.get("raw_text", "").strip(),
        "notes": item.get("notes", "").strip(),
        "status": item.get("status", "pending"),
    }


def normalize_inventory_lot(lot, item=None):
    item = item or {}
    return {
        "id": lot.get("id", uuid4().hex),
        "quantity": try_float(lot.get("quantity")) or 0.0,
        "unit": lot.get("unit") or item.get("unit", "unit"),
        "status": lot.get("status", "sealed"),
        "purchase_date": lot.get("purchase_date") or item.get("purchase_date", "") or today_iso(),
        "opened_date": lot.get("opened_date") or "",
        "expiry_date": lot.get("expiry_date") or item.get("expiry_date", ""),
        "location_id": lot.get("location_id") or item.get("location_id", ""),
        "vendor": lot.get("vendor") or item.get("preferred_vendor", ""),
        "brand": lot.get("brand") or item.get("preferred_brand", ""),
        "price": try_float(lot.get("price")),
        "notes": lot.get("notes", ""),
    }


def normalize_inventory_item(item):
    name = item.get("name", "Ingredient").strip() or "Ingredient"
    category_name = item.get("category_name", "")
    category_id = item.get("category_id") or slugify_name(category_name or "Other Kitchen")
    unit = item.get("unit", "unit").strip() or "unit"
    base = {
        "id": item.get("id", uuid4().hex),
        "name": name,
        "archived": bool(item.get("archived", False)),
        "category_id": category_id,
        "unit": unit,
        "approx_status": item.get("approx_status", ""),
        "refill_level": try_float(item.get("refill_level")),
        "storage_capacity": try_float(item.get("storage_capacity")),
        "shelf_life_days": int(try_float(item.get("shelf_life_days")) or 0),
        "purchase_date": item.get("purchase_date", ""),
        "opened_date": item.get("opened_date", ""),
        "expiry_date": item.get("expiry_date", ""),
        "location_id": item.get("location_id", ""),
        "preferred_vendor": item.get("preferred_vendor", ""),
        "preferred_brand": item.get("preferred_brand", ""),
        "preferred_purchase_quantity": try_float(item.get("preferred_purchase_quantity")),
        "preferred_purchase_unit": item.get("preferred_purchase_unit", ""),
        "aliases": [str(value).strip() for value in item.get("aliases", []) if str(value).strip()],
        "notes": item.get("notes", ""),
        "lots": [],
    }
    lots = [normalize_inventory_lot(lot, base) for lot in item.get("lots", [])]
    legacy_quantity = try_float(item.get("quantity"))
    if not lots and (legacy_quantity is not None or item.get("name")):
        lots = [
            normalize_inventory_lot(
                {
                    "quantity": legacy_quantity or 0.0,
                    "unit": item.get("unit", unit),
                    "status": "opened" if (legacy_quantity or 0.0) > 0 else "finished",
                    "purchase_date": item.get("purchase_date") or today_iso(),
                    "location_id": item.get("location_id", ""),
                    "notes": item.get("notes", ""),
                },
                base,
            )
        ]
    base["lots"] = lots
    return base


def normalize_inventory_transaction(transaction):
    return {
        "id": transaction.get("id", uuid4().hex),
        "created_at": transaction.get("created_at") or datetime.now().isoformat(timespec="seconds"),
        "item_id": transaction.get("item_id", ""),
        "item_name": transaction.get("item_name", ""),
        "change_value": try_float(transaction.get("change_value")) or 0.0,
        "unit": transaction.get("unit", ""),
        "action": transaction.get("action", "manual"),
        "reason": transaction.get("reason", "manual"),
        "notes": transaction.get("notes", ""),
        "source": transaction.get("source", "manual"),
    }


def split_legacy_quantity(quantity):
    if not quantity:
        return "", ""
    parts = [part.strip() for part in str(quantity).split("|")]
    shreya_quantity = parts[0].replace("Shreya:", "").strip() if parts else ""
    varshit_quantity = parts[1].replace("Varshit:", "").strip() if len(parts) > 1 else ""
    return shreya_quantity, varshit_quantity


def normalize_meal_log_entry(entry):
    entry = dict(entry) if isinstance(entry, dict) else {}
    nutrition = nutrition_for(entry.get("meal_name", ""))
    shreya_quantity, varshit_quantity = split_legacy_quantity(entry.get("quantity"))
    logged_at = entry.get("logged_at") or datetime.now().isoformat(timespec="seconds")
    planned_servings = try_float(entry.get("planned_servings")) or 0.0
    actual_servings = try_float(entry.get("actual_servings"))
    if actual_servings is None:
        actual_servings = planned_servings
    leftovers = max(planned_servings - actual_servings, 0.0)
    return {
        "id": entry.get("id", uuid4().hex),
        "meal_name": entry.get("meal_name", "Unknown meal"),
        "shreya_quantity": entry.get("shreya_quantity", shreya_quantity),
        "varshit_quantity": entry.get("varshit_quantity", varshit_quantity),
        "logged_at": logged_at,
        "date": entry.get("date", datetime.fromisoformat(logged_at).strftime("%Y-%m-%d")),
        "time": entry.get("time", datetime.fromisoformat(logged_at).strftime("%I:%M %p")),
        "planned_servings": planned_servings,
        "actual_servings": actual_servings,
        "leftover_servings": try_float(entry.get("leftover_servings")) if entry.get("leftover_servings") is not None else leftovers,
        "recipe_ref": entry.get("recipe_ref", ""),
        "shreya_calories": entry.get("shreya_calories", nutrition["you"]["calories"]),
        "shreya_protein": entry.get("shreya_protein", nutrition["you"]["protein"]),
        "varshit_calories": entry.get("varshit_calories", nutrition["varshit"]["calories"]),
        "varshit_protein": entry.get("varshit_protein", nutrition["varshit"]["protein"]),
    }


def load_legacy_meal_log():
    if not MEAL_LOG_PATH.exists():
        return []
    try:
        raw = json.loads(MEAL_LOG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    return [normalize_meal_log_entry(entry) for entry in raw]


def default_profile(name="New Household"):
    return apply_project_household_defaults(
        {
        "id": uuid4().hex,
        "name": name,
        "household_members": [],
        "meal_templates": [],
        "recipes": [],
        "inventory": [],
        "inventory_categories": default_inventory_categories(),
        "inventory_transactions": [],
        "storage_locations": default_storage_locations(),
        "vendors": default_vendor_records(),
        "shopping_manual_items": [],
        "grocery_data": {"missing_items": {}},
        "preferences": {
            "favorites_only": False,
            "activity_level": "Moderately active",
            "meal_mode": "Normal eating",
            "before_didi_arrives": "",
            "morning_routine": "",
            "weather_mode": "Normal",
            "used_categories": [],
            "setup_complete": False,
        },
        "recent_meals": [],
        "recent_recipes": [],
        "meal_log": [],
        "leftovers": [],
        "planner_preferences": {},
        "shopping_preferences": {"suggestion_overrides": {}},
    }
    )


def normalize_profile(profile):
    profile = dict(profile) if isinstance(profile, dict) else {}
    normalized = default_profile(name=profile.get("name", "Imported Household"))
    normalized["id"] = profile.get("id", normalized["id"])
    normalized["name"] = profile.get("name", normalized["name"])
    legacy_preferences = profile.get("preferences", {})
    normalized["household_members"] = [
        normalize_member(member, legacy_preferences) for member in profile.get("household_members", [])
    ][:MAX_PROFILE_MEMBERS]
    normalized["meal_templates"] = [normalize_template(item) for item in profile.get("meal_templates", [])]
    normalized["recipes"] = [normalize_recipe(item) for item in profile.get("recipes", [])]
    normalized["inventory_categories"] = [normalize_inventory_category(item) for item in profile.get("inventory_categories", [])] or default_inventory_categories()
    category_ids = {item["id"] for item in normalized["inventory_categories"]}
    for default_category in default_inventory_categories():
        if default_category["id"] not in category_ids:
            normalized["inventory_categories"].append(default_category)
    normalized["storage_locations"] = [normalize_storage_location(item) for item in profile.get("storage_locations", [])] or default_storage_locations()
    location_ids = {item["id"] for item in normalized["storage_locations"]}
    for default_location in default_storage_locations():
        if default_location["id"] not in location_ids:
            normalized["storage_locations"].append(default_location)
    normalized["vendors"] = [normalize_vendor_record(item) for item in profile.get("vendors", [])] or default_vendor_records()
    vendor_ids = {item["id"] for item in normalized["vendors"]}
    for default_vendor in default_vendor_records():
        if default_vendor["id"] not in vendor_ids:
            normalized["vendors"].append(default_vendor)
    normalized["inventory"] = [normalize_inventory_item(item) for item in profile.get("inventory", [])]
    normalized["inventory_transactions"] = [normalize_inventory_transaction(item) for item in profile.get("inventory_transactions", [])]
    normalized["shopping_manual_items"] = [normalize_manual_shopping_item(item) for item in profile.get("shopping_manual_items", [])]
    normalized["grocery_data"] = {"missing_items": dict(profile.get("grocery_data", {}).get("missing_items", {}))}
    normalized["preferences"] = {
        "favorites_only": bool(profile.get("preferences", {}).get("favorites_only", False)),
        "activity_level": profile.get("preferences", {}).get("activity_level", "Moderately active"),
        "meal_mode": profile.get("preferences", {}).get("meal_mode", "Normal eating"),
        "before_didi_arrives": profile.get("preferences", {}).get("before_didi_arrives", ""),
        "morning_routine": profile.get("preferences", {}).get("morning_routine", ""),
        "weather_mode": profile.get("preferences", {}).get("weather_mode", "Normal"),
        "used_categories": list(profile.get("preferences", {}).get("used_categories", [])),
        "setup_complete": bool(profile.get("preferences", {}).get("setup_complete", False)),
    }
    normalized["recent_meals"] = list(profile.get("recent_meals", []))[:8]
    normalized["recent_recipes"] = list(profile.get("recent_recipes", []))[:8]
    normalized["meal_log"] = [normalize_meal_log_entry(entry) for entry in profile.get("meal_log", [])]
    normalized["leftovers"] = list(profile.get("leftovers", []))
    normalized["planner_preferences"] = dict(profile.get("planner_preferences", {}))
    normalized["shopping_preferences"] = {"suggestion_overrides": dict(profile.get("shopping_preferences", {}).get("suggestion_overrides", {}))}
    return apply_project_household_defaults(normalized)


def default_profile_store():
    profile = default_profile()
    return {"version": 2, "active_profile_id": profile["id"], "profiles": [profile]}


def normalize_profile_store(store):
    if not isinstance(store, dict):
        return default_profile_store()
    if store.get("version") != 2:
        return default_profile_store()
    profiles = [normalize_profile(profile) for profile in store.get("profiles", [])]
    if not profiles:
        return default_profile_store()
    active_profile_id = store.get("active_profile_id", profiles[0]["id"])
    if active_profile_id not in {profile["id"] for profile in profiles}:
        active_profile_id = profiles[0]["id"]
    return {"version": 2, "active_profile_id": active_profile_id, "profiles": profiles}


def load_profile_store(store_path):
    store_path.parent.mkdir(parents=True, exist_ok=True)
    if not store_path.exists():
        store = default_profile_store()
        store_path.write_text(json.dumps(store, indent=2))
        return store
    try:
        raw = json.loads(store_path.read_text())
    except (json.JSONDecodeError, OSError):
        return default_profile_store()
    return normalize_profile_store(raw)


def save_profile_store(store, store_path):
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(normalize_profile_store(store), indent=2))


def get_active_profile(store):
    return next(profile for profile in store["profiles"] if profile["id"] == store["active_profile_id"])


def replace_profile(store, profile):
    store["profiles"] = [profile if item["id"] == profile["id"] else item for item in store["profiles"]]
    return store


def add_recent_entry(items, label, linked_id=""):
    stamp = datetime.now().isoformat(timespec="seconds")
    updated = [{"label": label, "used_at": stamp, "linked_id": linked_id}]
    for item in items:
        if item.get("label") != label:
            updated.append(item)
    return updated[:8]


def parse_import_payload(file_bytes):
    try:
        payload = json.loads(file_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("The selected file is not valid JSON.")
    if payload.get("type") == "meal_planner_profile" and payload.get("profile"):
        return normalize_profile(payload["profile"])
    if payload.get("profiles"):
        store = normalize_profile_store(payload)
        return normalize_profile(get_active_profile(store))
    if payload.get("name") and payload.get("household_members") is not None:
        return normalize_profile(payload)
    raise ValueError("The import file does not look like a supported meal planner profile package.")


def merge_profiles(existing, imported):
    merged = normalize_profile(existing)
    merged["name"] = imported.get("name", merged["name"])
    member_names = {item["name"].strip().lower(): item for item in merged["household_members"]}
    for item in imported.get("household_members", []):
        member_names[item["name"].strip().lower()] = item
    merged["household_members"] = list(member_names.values())[:MAX_PROFILE_MEMBERS]

    def merge_items(current_items, new_items):
        merged_items = {item["name"].strip().lower(): item for item in current_items}
        for item in new_items:
            merged_items[item["name"].strip().lower()] = item
        return list(merged_items.values())

    merged["meal_templates"] = merge_items(merged["meal_templates"], imported.get("meal_templates", []))
    merged["recipes"] = merge_items(merged["recipes"], imported.get("recipes", []))
    merged["inventory"] = merge_items(merged["inventory"], imported.get("inventory", []))
    merged["grocery_data"]["missing_items"].update(imported.get("grocery_data", {}).get("missing_items", {}))
    merged["preferences"].update(imported.get("preferences", {}))
    merged["meal_log"] = [normalize_meal_log_entry(item) for item in imported.get("meal_log", [])] + merged["meal_log"]
    merged["leftovers"] = imported.get("leftovers", []) + merged["leftovers"]
    merged["recent_meals"] = add_recent_entry(merged.get("recent_meals", []), "Imported profile merge")
    return normalize_profile(merged)


def split_list_items(text):
    items = []
    for chunk in re.split(r"[\n,]+", str(text or "")):
        value = chunk.strip()
        if value:
            items.append(value)
    return items


def planner_members(profile):
    members = profile.get("household_members", [])
    primary = members[0] if len(members) >= 1 else normalize_member({"name": "Member", "portion_ratio": 1})
    secondary = members[1] if len(members) >= 2 else None
    return primary, secondary


def intake_summary(member):
    return ", ".join(split_list_items(member.get("intake_items", "")))


def build_fixed_item_meta(profile):
    primary, secondary = planner_members(profile)

    def item_meta_for(member):
        items = OrderedDict()
        for entry in split_list_items(member.get("intake_items", "")):
            items[entry] = {"calories": 0, "protein": 0, "ingredients": [(entry, "")]}
        return items

    return {
        "primary_name": primary["name"],
        "secondary_name": secondary["name"] if secondary else "",
        "primary": item_meta_for(primary),
        "secondary": item_meta_for(secondary) if secondary else OrderedDict(),
    }


def build_routine_sections(profile):
    members = profile.get("household_members", [])
    before_didi_lines = split_list_items(profile.get("preferences", {}).get("before_didi_arrives", ""))
    morning_lines = split_list_items(profile.get("preferences", {}).get("morning_routine", ""))
    for member in members[:MAX_PROFILE_MEMBERS]:
        intake_bits = split_list_items(member.get("intake_items", ""))
        if intake_bits:
            morning_lines.append(f"Set out {member['name']}'s intake items: {', '.join(intake_bits)}.")
    night_prep = [
        "Check that tomorrow's meal ingredients are available in the kitchen.",
        "Prep or soak any ingredients needed for the selected meals.",
    ]
    morning_start = [
        "Start the main cooking for the day.",
        "Keep each household member's routine items ready before serving meals.",
    ]
    if before_didi_lines:
        night_prep.extend(before_didi_lines[:6])
    if morning_lines:
        morning_start.extend(morning_lines[:8])
    return {"night_prep": night_prep, "morning_start": morning_start}


def activity_multiplier(profile):
    level = profile.get("preferences", {}).get("activity_level", "Moderately active")
    return {
        "Low activity": 1.0,
        "Moderately active": 1.15,
        "Active": 1.3,
    }.get(level, 1.15)


def goal_multiplier(profile):
    mode = profile.get("preferences", {}).get("meal_mode", "Normal eating")
    return {
        "Normal eating": 1.0,
        "Weight maintenance": 1.05,
        "Higher protein intake": 1.08,
    }.get(mode, 1.0)


def built_in_recipe_lookup():
    return {dish["name"]: dish for dish in all_recipe_dishes()}


def profile_recipe_lookup(profile):
    return {recipe["id"]: recipe for recipe in profile.get("recipes", [])}


def linked_recipe_options(profile):
    options = [("", "No linked recipe")]
    for recipe in profile.get("recipes", []):
        options.append((f"profile::{recipe['id']}", f"Profile: {recipe['name']}"))
    for dish in all_recipe_dishes():
        options.append((f"builtin::{dish['name']}", f"Built-in: {dish['name']}"))
    return options


def resolve_linked_recipe(profile, recipe_ref):
    if not recipe_ref:
        return None
    if recipe_ref.startswith("profile::"):
        recipe_id = recipe_ref.split("::", 1)[1]
        recipe = profile_recipe_lookup(profile).get(recipe_id)
        if recipe:
            return {"source": "profile", "recipe": recipe}
    if recipe_ref.startswith("builtin::"):
        recipe_name = recipe_ref.split("::", 1)[1]
        recipe = built_in_recipe_lookup().get(recipe_name)
        if recipe:
            return {"source": "builtin", "recipe": recipe}
    if recipe_ref in built_in_recipe_lookup():
        return {"source": "builtin", "recipe": built_in_recipe_lookup()[recipe_ref]}
    return None


def household_servings(profile):
    total = sum(try_float(member.get("portion_ratio")) or 0.0 for member in profile.get("household_members", []))
    return total or 1.0


def scale_recipe_ingredient(item, factor):
    quantity = try_float(item.get("quantity"))
    scaled_qty = format_number((quantity or 0.0) * factor) if quantity is not None else ""
    qty_text = " ".join(part for part in [scaled_qty, item.get("unit", "")] if part).strip()
    return {"name": item.get("name", ""), "qty": qty_text or item.get("notes", "")}


def recipe_ingredients_for_display(profile, recipe_info):
    if not recipe_info:
        return []
    if recipe_info["source"] == "builtin":
        return [{"name": item["name"], "qty": item.get("qty", "")} for item in recipe_info["recipe"].get("ingredients", [])]
    recipe = recipe_info["recipe"]
    factor = household_servings(profile) / max(recipe.get("base_servings", 2.0), 0.1)
    return [scale_recipe_ingredient(item, factor) for item in recipe.get("ingredients", [])]


def recipe_methods_for_display(recipe_info):
    if not recipe_info:
        return []
    if recipe_info["source"] == "builtin":
        return list(recipe_info["recipe"].get("method", []))
    return list(recipe_info["recipe"].get("instructions", []))


def recipe_summary(recipe_info):
    if not recipe_info:
        return ""
    if recipe_info["source"] == "builtin":
        return recipe_info["recipe"].get("summary", "")
    return recipe_info["recipe"].get("description", "")


def recipe_youtube(recipe_info):
    if not recipe_info:
        return ""
    return recipe_info["recipe"].get("youtube", "")


def meal_template_lookup(profile):
    return {template["id"]: template for template in profile.get("meal_templates", [])}


def planner_option_id(kind, value):
    return f"{kind}::{value}"


def build_planner_options(profile):
    options = []
    label_map = {}
    seen_labels = set()
    for template in profile.get("meal_templates", []):
        option_id = planner_option_id("template", template["id"])
        label = template["name"]
        if label in seen_labels:
            label = f"{label} (Template)"
        seen_labels.add(label)
        options.append(option_id)
        label_map[option_id] = label
    for dish_name in dish_names("brunch"):
        option_id = planner_option_id("builtin", dish_name)
        label = dish_name if dish_name not in seen_labels else f"{dish_name} (Built-in)"
        seen_labels.add(label)
        options.append(option_id)
        label_map[option_id] = label
    return options, label_map


def default_brunch_option(profile):
    defaults = DAY_PLANS.get("Today", DAY_PLANS["Today"])
    return planner_option_id("builtin", defaults["brunch"])


def default_dinner_option(profile):
    defaults = DAY_PLANS.get("Today", DAY_PLANS["Today"])
    if defaults["dinner"] != "Morning Portion Only":
        return planner_option_id("builtin", defaults["dinner"])
    return default_brunch_option(profile)


def meal_template_portion_text(profile):
    members = profile.get("household_members", [])
    if not members:
        return {"you": "", "varshit": ""}
    first = members[0]
    second = members[1] if len(members) > 1 else None
    return {
        "you": f"{format_number(first.get('portion_ratio', 1.0))} serving",
        "varshit": f"{format_number(second.get('portion_ratio', 1.0))} serving" if second else "",
    }


def adapt_portion_defaults(profile, defaults):
    members = profile.get("household_members", [])
    if not members:
        return {"you": "", "varshit": ""}
    if len(members) == 1:
        return {"you": defaults.get("you", ""), "varshit": ""}
    return defaults


def portion_defaults_for_option(profile, option_id, current_brunch_option_id=None):
    kind, value = option_id.split("::", 1)
    if kind == "special":
        reference = current_brunch_option_id or default_brunch_option(profile)
        defaults = portion_defaults_for_option(profile, reference, reference)
        return adapt_portion_defaults(profile, {"you": "1 small leftover bowl", "varshit": "1 medium leftover bowl"}) if value == "Morning Portion Only" else defaults
    if kind == "builtin":
        return adapt_portion_defaults(profile, PORTIONS.get(value, {"you": "1 serving", "varshit": "1 serving"}))
    return meal_template_portion_text(profile)


def sync_portions_from_selection(profile):
    brunch_option_id = st.session_state.get("brunch_option_id", default_brunch_option(profile))
    dinner_option_id = st.session_state.get("dinner_option_id", default_dinner_option(profile))
    brunch_defaults = portion_defaults_for_option(profile, brunch_option_id)
    dinner_defaults = portion_defaults_for_option(profile, dinner_option_id, brunch_option_id)
    st.session_state.portion_you_suggestion = brunch_defaults["you"]
    st.session_state.portion_varshit_suggestion = brunch_defaults["varshit"]
    st.session_state.dinner_portion_you_suggestion = dinner_defaults["you"]
    st.session_state.dinner_portion_varshit_suggestion = dinner_defaults["varshit"]


def choose_random_meals(profile, brunch_options, dinner_options):
    st.session_state.brunch_option_id = random.choice(brunch_options)
    st.session_state.dinner_option_id = random.choice(dinner_options)
    sync_portions_from_selection(profile)


def option_to_dish(profile, option_id, brunch_dish=None):
    kind, value = option_id.split("::", 1)
    if kind == "special" and value == "Morning Portion Only":
        return {
            "name": "Morning Portion Only",
            "summary": "Eat a measured lighter portion of the brunch meal for dinner.",
            "ingredients": [],
            "method": ["Portion the dinner share in the morning itself.", "Reheat gently and keep dinner smaller than brunch."],
            "youtube": "",
            "recipe_ref": "",
            "has_recipe": False,
        }
    if kind == "builtin":
        dish = deepcopy(get_dish("brunch", value))
        dish["recipe_ref"] = f"builtin::{dish['name']}"
        dish["has_recipe"] = True
        return dish
    template = meal_template_lookup(profile).get(value)
    linked_recipe = resolve_linked_recipe(profile, template.get("linked_recipe_ref", "")) if template else None
    return {
        "name": template.get("name", "Meal Template"),
        "summary": template.get("description", "") or recipe_summary(linked_recipe) or "Saved meal template.",
        "ingredients": recipe_ingredients_for_display(profile, linked_recipe),
        "method": recipe_methods_for_display(linked_recipe),
        "youtube": recipe_youtube(linked_recipe),
        "recipe_ref": template.get("linked_recipe_ref", ""),
        "has_recipe": bool(linked_recipe),
    }


def collect_ingredients(dishes):
    items = OrderedDict()
    for dish in dishes:
        for item in dish.get("ingredients", []):
            items[item["name"]] = item.get("qty", "")
    return items


def meal_log_quantity(portion_you, portion_varshit):
    return f"Shreya: {portion_you} | Varshit: {portion_varshit}"


def open_recipe(name):
    st.session_state.pending_workspace = "Recipes"
    st.session_state.selected_recipe_slug = recipe_slug(name)
    st.session_state.jump_anchor = "recipes-section"


def jump_to_anchor(anchor, force_setup_open=False):
    st.session_state.jump_anchor = anchor
    if force_setup_open:
        st.session_state.force_open_setup = True


DESKTOP_WORKSPACE_TABS = ["Planner", "Recipes", "Inventory", "Home Supplies", "Shopping", "Insights", "Setup"]
MOBILE_PRIMARY_WORKSPACES = ["Planner", "Inventory", "Shopping", "Recipes", "More"]
MOBILE_MORE_WORKSPACES = ["Home Supplies", "Insights", "Setup"]
MOBILE_SECTION_LABELS = {
    "Overview": "Overview",
    "Items": "Items",
    "Expiry": "Expiry",
    "Adjustments": "Adjust",
    "Storage": "Storage",
    "Analytics": "Analytics",
}


def set_active_workspace(workspace):
    if workspace not in DESKTOP_WORKSPACE_TABS:
        return
    st.session_state.active_workspace = workspace
    st.session_state.workspace_selector_desktop = workspace
    st.session_state.workspace_selector_mobile = workspace if workspace in MOBILE_PRIMARY_WORKSPACES else "More"
    if workspace in MOBILE_MORE_WORKSPACES:
        st.session_state.mobile_more_workspace = workspace


def on_desktop_workspace_change():
    set_active_workspace(st.session_state.get("workspace_selector_desktop", "Planner"))


def on_mobile_workspace_change():
    choice = st.session_state.get("workspace_selector_mobile", "Planner")
    if choice == "More":
        set_active_workspace(st.session_state.get("mobile_more_workspace", MOBILE_MORE_WORKSPACES[0]))
    else:
        set_active_workspace(choice)


def on_mobile_more_workspace_change():
    set_active_workspace(st.session_state.get("mobile_more_workspace", MOBILE_MORE_WORKSPACES[0]))


def set_inventory_section(section):
    if section not in INVENTORY_SECTIONS:
        return
    st.session_state.inventory_section = section
    st.session_state.inventory_section_desktop = section
    st.session_state.inventory_section_mobile = section


def on_inventory_section_desktop_change():
    set_inventory_section(st.session_state.get("inventory_section_desktop", "Overview"))


def on_inventory_section_mobile_change():
    set_inventory_section(st.session_state.get("inventory_section_mobile", "Overview"))


def set_home_supply_section(section):
    if section not in INVENTORY_SECTIONS:
        return
    st.session_state.home_supply_section = section
    st.session_state.home_supply_section_desktop = section
    st.session_state.home_supply_section_mobile = section


def on_home_supply_section_desktop_change():
    set_home_supply_section(st.session_state.get("home_supply_section_desktop", "Overview"))


def on_home_supply_section_mobile_change():
    set_home_supply_section(st.session_state.get("home_supply_section_mobile", "Overview"))


def toggle_state(key, value=True):
    st.session_state[key] = value


def logMeal(profile, meal_name, shreya_quantity, varshit_quantity, planned_servings, actual_servings, recipe_ref=""):
    logged_at = datetime.now().isoformat(timespec="seconds")
    nutrition = nutrition_for(meal_name)
    leftovers = max(planned_servings - actual_servings, 0.0)
    entry = {
        "id": uuid4().hex,
        "meal_name": meal_name,
        "shreya_quantity": shreya_quantity,
        "varshit_quantity": varshit_quantity,
        "logged_at": logged_at,
        "date": datetime.fromisoformat(logged_at).strftime("%Y-%m-%d"),
        "time": datetime.fromisoformat(logged_at).strftime("%I:%M %p"),
        "planned_servings": planned_servings,
        "actual_servings": actual_servings,
        "leftover_servings": leftovers,
        "recipe_ref": recipe_ref,
        "shreya_calories": nutrition["you"]["calories"],
        "shreya_protein": nutrition["you"]["protein"],
        "varshit_calories": nutrition["varshit"]["calories"],
        "varshit_protein": nutrition["varshit"]["protein"],
    }
    profile["meal_log"] = [entry, *profile.get("meal_log", [])]
    profile["recent_meals"] = add_recent_entry(profile.get("recent_meals", []), meal_name, recipe_ref)
    if recipe_ref:
        profile["recent_recipes"] = add_recent_entry(profile.get("recent_recipes", []), meal_name, recipe_ref)
    if leftovers > 0:
        profile["leftovers"] = [
            {
                "id": uuid4().hex,
                "recipe_name": meal_name,
                "remaining_servings": leftovers,
                "created_at": logged_at,
            },
            *profile.get("leftovers", []),
        ]
    return profile


def deleteMealLogEntry(profile, entry_id):
    profile["meal_log"] = [entry for entry in profile.get("meal_log", []) if entry.get("id") != entry_id]
    return profile


def MealLogTab(profile):
    meal_log = profile.get("meal_log", [])
    if not meal_log:
        st.info("No meals logged yet.")
        return
    primary_member, secondary_member = planner_members(profile)
    sorted_log = sorted(meal_log, key=lambda item: item.get("logged_at", ""), reverse=True)
    rows = []
    for entry in sorted_log:
        rows.append(
            {
                "Meal": entry.get("meal_name", "Unknown meal"),
                "Date": datetime.fromisoformat(entry["logged_at"]).strftime("%d %b %Y") if entry.get("logged_at") else entry.get("date", ""),
                "Time": entry.get("time", ""),
                f"{primary_member['name']} Quantity": entry.get("shreya_quantity", ""),
                "Planned Servings": format_number(entry.get("planned_servings", 0)),
                "Actual Servings": format_number(entry.get("actual_servings", 0)),
                "Leftovers": format_number(entry.get("leftover_servings", 0)),
            }
        )
        if secondary_member:
            rows[-1][f"{secondary_member['name']} Quantity"] = entry.get("varshit_quantity", "")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    delete_options = {
        f"{entry.get('meal_name', 'Unknown meal')} | {entry.get('date', '')} {entry.get('time', '')}": entry.get("id")
        for entry in sorted_log
    }
    selected_delete_label = st.selectbox("Remove a logged meal", ["Select a meal to remove"] + list(delete_options.keys()))
    if selected_delete_label != "Select a meal to remove":
        if st.button("Delete selected meal", type="secondary"):
            profile = deleteMealLogEntry(profile, delete_options[selected_delete_label])
            persist_active_profile(profile)
            st.rerun()


def persist_active_profile(profile):
    user_id = st.session_state.get("planner_user_id", "")
    if not user_id:
        return
    store_path = user_profile_store_path(user_id)
    store = load_profile_store(store_path)
    store = replace_profile(store, normalize_profile(profile))
    save_profile_store(store, store_path)


def sync_profile_state(profile):
    changed = False
    meal_log = st.session_state.get("mealLog", [])
    if profile.get("meal_log") != meal_log:
        profile["meal_log"] = meal_log
        changed = True
    grocery_items = dict(st.session_state.get("grocery_list", OrderedDict()))
    if profile.get("grocery_data", {}).get("missing_items", {}) != grocery_items:
        profile["grocery_data"]["missing_items"] = grocery_items
        changed = True
    return changed


def inject_ui_styles():
    st.markdown(
        """
        <style>
        :root {
            color-scheme: light dark;
            --soft-green-bg: #e8f5ec;
            --soft-green-border: #c8e2cf;
            --soft-green-text: #14532d;
            --soft-hover-bg: #f3faf5;
        }
        html {
            scroll-behavior: smooth;
        }
        .stApp {
            color: var(--text-color);
            background: var(--background-color);
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-bottom: 6.25rem;
            }
        }
        .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-color);
            margin: 1rem 0 0.55rem;
        }
        .library-note {
            padding: 0.7rem 0.9rem;
            border-radius: 12px;
            background: color-mix(in srgb, var(--secondary-background-color) 74%, var(--background-color) 26%);
            border: 1px solid color-mix(in srgb, var(--text-color) 12%, transparent 88%);
        }
        .recipe-anchor {
            display: block;
            scroll-margin-top: 5rem;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: color-mix(in srgb, var(--secondary-background-color) 72%, var(--background-color) 28%);
            border: 1px solid color-mix(in srgb, var(--text-color) 12%, transparent 88%);
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            padding: 0.2rem;
            margin-bottom: 1rem;
        }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp p, .stApp li, .stApp label, .stApp div, .stApp span,
        .stApp [data-baseweb="select"] *, .stApp [data-baseweb="tab"] * {
            color: var(--text-color);
        }
        .stApp a {
            color: var(--link-color, #0f766e);
            text-decoration-color: var(--link-color, #0f766e);
        }
        .stApp .stTabs button[role="tab"] {
            color: var(--text-color);
            background: transparent;
            font-weight: 600;
            border-radius: 999px;
            padding-inline: 0.8rem;
        }
        .stApp .stTabs button[aria-selected="true"] {
            color: var(--text-color);
            background: color-mix(in srgb, var(--soft-green-bg) 88%, var(--background-color) 12%);
        }
        .stApp .stButton button {
            font-weight: 600;
            color: var(--text-color);
            border-radius: 12px;
        }
        .stApp [data-baseweb="select"] > div,
        .stApp .stTextInput input,
        .stApp .stNumberInput input,
        .stApp textarea {
            color: var(--text-color);
            background: color-mix(in srgb, var(--background-color) 85%, var(--secondary-background-color) 15%);
        }
        .stApp [data-baseweb="select"] svg,
        .stApp .stExpander svg {
            fill: var(--text-color);
        }
        .stApp .stExpander {
            border: 1px solid color-mix(in srgb, var(--text-color) 12%, transparent 88%);
            border-radius: 12px;
            background: color-mix(in srgb, var(--background-color) 86%, var(--secondary-background-color) 14%);
        }
        .stApp .stExpander summary,
        .stApp .stExpander summary p {
            color: var(--text-color);
            font-weight: 600;
        }
        .stApp [data-testid="stDataFrame"],
        .stApp [data-testid="stDataFrame"] * {
            color: var(--text-color);
        }
        .stApp .stAlert,
        .stApp .stAlert * {
            color: var(--text-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def reset_user_session_state():
    for key in [
        "active_profile_loaded",
        "grocery_list",
        "mealLog",
        "selected_recipe_slug",
        "portion_you",
        "portion_varshit",
        "dinner_portion_you",
        "dinner_portion_varshit",
        "portion_you_suggestion",
        "portion_varshit_suggestion",
        "dinner_portion_you_suggestion",
        "dinner_portion_varshit_suggestion",
    ]:
        st.session_state.pop(key, None)


def render_user_gate():
    st.title("Main Meal Planner Varhshree")
    st.write("Enter your user ID to open your Varhshree planner.")
    with st.form("user_gate_form"):
        raw_user_id = st.text_input("User ID")
        remember_user = st.checkbox("Remember this User ID on this device", value=True)
        open_planner = st.form_submit_button("Open planner")
    if open_planner:
        normalized = normalize_user_id(raw_user_id)
        if not normalized:
            st.error("Enter a valid user ID using letters, numbers, hyphens, or underscores.")
        else:
            st.session_state.planner_user_id = normalized
            reset_user_session_state()
            if remember_user:
                save_remembered_user_id(normalized)
            else:
                clear_remembered_user_id()
            st.rerun()
    st.stop()


def section_intro(anchor, title):
    st.markdown(
        f"""
        <div id="{anchor}"></div>
        <div class="section-title">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def render_recent_lists(profile):
    recent_col, favorites_col = st.columns(2)
    with recent_col:
        st.markdown("**Recent meals**")
        if profile.get("recent_meals"):
            st.markdown("- " + "\n- ".join(item["label"] for item in profile["recent_meals"][:5]))
        else:
            st.write("No recent meals yet.")
    with favorites_col:
        st.markdown("**Recent recipes**")
        if profile.get("recent_recipes"):
            st.markdown("- " + "\n- ".join(item["label"] for item in profile["recent_recipes"][:5]))
        else:
            st.write("No recent recipes yet.")


def render_household_manager(profile, key_scope="default"):
    editor_key = f"member_editor_{key_scope}_{profile['id']}"
    confirm_delete_key = f"confirm_delete_member_{key_scope}_{profile['id']}"
    st.markdown("**Household members**")
    if profile.get("household_members"):
        rows = [
            {
                "Name": member["name"],
                "Fooding Ratio": member["portion_ratio"],
                "Gym": member.get("goes_to_gym", "No"),
                "Walk": member.get("walks_regularly", "Yes"),
                "Supplements / Protein / Medicine / Intake": intake_summary(member),
            }
            for member in profile["household_members"]
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No household members yet. Create household and member details to start planning meals.")

    member_options = {"Add new member": ""}
    for member in profile.get("household_members", []):
        member_options[f"Edit {member['name']}"] = member["id"]
    selected_member_id = st.selectbox(
        "Household member",
        list(member_options.values()),
        format_func=lambda item: next(label for label, value in member_options.items() if value == item),
        key=editor_key,
    )
    selected_member = next((member for member in profile.get("household_members", []) if member["id"] == selected_member_id), None)
    default_name = selected_member["name"] if selected_member else ""
    existing_members = profile.get("household_members", [])
    existing_index = next((idx for idx, item in enumerate(existing_members) if selected_member and item["id"] == selected_member["id"]), None)
    is_first_member = (selected_member is None and not existing_members) or existing_index == 0
    default_ratio = 1.0 if is_first_member else (selected_member["portion_ratio"] if selected_member else 1.0)
    with st.form(f"member_form_{key_scope}_{profile['id']}"):
        member_name = st.text_input("Member name", value=default_name)
        if is_first_member:
            st.text_input("Fooding ratio", value="1", disabled=True)
            portion_ratio = 1.0
        else:
            portion_ratio = st.number_input("Fooding ratio", min_value=0.25, max_value=3.0, step=0.25, value=float(default_ratio))
        gym_value = selected_member.get("goes_to_gym", "No") if selected_member else "No"
        walk_value = selected_member.get("walks_regularly", "Yes") if selected_member else "Yes"
        goes_to_gym = st.selectbox("Gym", ["No", "Yes"], index=["No", "Yes"].index(gym_value))
        walks_regularly = st.selectbox("Walk", ["No", "Yes"], index=["No", "Yes"].index(walk_value))
        intake_items = st.text_input(
            "Supplements / Protein / Medicine / Intake",
            value=selected_member.get("intake_items", "") if selected_member else "",
            placeholder="Supplements, medicines, juice, protein, dry fruits",
        )
        save_member = st.form_submit_button("Save member")
        delete_member = st.form_submit_button("Delete member") if selected_member else False
    if save_member:
        if not member_name.strip():
            st.error("Member name is required.")
        elif not selected_member and len(profile.get("household_members", [])) >= MAX_PROFILE_MEMBERS:
            st.error("You can add up to 5 household members.")
        else:
            member = normalize_member(
                {
                    "id": selected_member["id"] if selected_member else uuid4().hex,
                    "name": member_name.strip(),
                    "portion_ratio": 1.0 if is_first_member else portion_ratio,
                    "goes_to_gym": goes_to_gym,
                    "walks_regularly": walks_regularly,
                    "intake_items": intake_items.strip(),
                    "routine_supplements": "",
                    "routine_medicines": "",
                    "juice_preference": "",
                    "protein_preference": "",
                    "dry_fruits_preference": "",
                    "other_add_ons": "",
                }
            )
            items = [item for item in profile.get("household_members", []) if item["id"] != member["id"]]
            items.append(member)
            profile["household_members"] = items[:MAX_PROFILE_MEMBERS]
            persist_active_profile(profile)
            st.rerun()
    if delete_member and selected_member:
        st.session_state[confirm_delete_key] = selected_member["id"]
        st.rerun()
    pending_delete_id = st.session_state.get(confirm_delete_key)
    if pending_delete_id:
        member_to_delete = next((item for item in profile.get("household_members", []) if item["id"] == pending_delete_id), None)
        if member_to_delete:
            st.warning(f"Delete {member_to_delete['name']} and their member-level details?")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Confirm delete", key=f"confirm_delete_btn_{key_scope}_{profile['id']}", type="primary", use_container_width=True):
                profile["household_members"] = [item for item in profile.get("household_members", []) if item["id"] != pending_delete_id]
                st.session_state.pop(confirm_delete_key, None)
                persist_active_profile(profile)
                st.rerun()
            if cancel_col.button("Cancel", key=f"cancel_delete_btn_{key_scope}_{profile['id']}", use_container_width=True):
                st.session_state.pop(confirm_delete_key, None)
                st.rerun()
        else:
            st.session_state.pop(confirm_delete_key, None)


def render_template_manager(profile, favorites_only):
    st.markdown("**Meal templates**")
    templates = profile.get("meal_templates", [])
    visible_templates = [item for item in templates if not favorites_only or item.get("favorite")]
    if visible_templates:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Name": item["name"],
                        "Description": item.get("description", ""),
                        "Linked Recipe": item.get("linked_recipe_ref", "").replace("builtin::", "").replace("profile::", "Profile recipe: "),
                        "Favorite": "Yes" if item.get("favorite") else "",
                    }
                    for item in visible_templates
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No meal templates yet.")

    template_options = {"Add new template": ""}
    for item in templates:
        template_options[f"Edit {item['name']}"] = item["id"]
    selected_template_id = st.selectbox("Meal template", list(template_options.values()), format_func=lambda item: next(label for label, value in template_options.items() if value == item), key=f"template_editor_{profile['id']}")
    selected_template = next((item for item in templates if item["id"] == selected_template_id), None)
    recipe_refs = linked_recipe_options(profile)
    selected_ref = selected_template.get("linked_recipe_ref", "") if selected_template else ""
    with st.form(f"template_form_{profile['id']}"):
        template_name = st.text_input("Template name", value=selected_template.get("name", "") if selected_template else "")
        template_description = st.text_area("Optional description", value=selected_template.get("description", "") if selected_template else "", height=80)
        linked_recipe_ref = st.selectbox("Linked recipe", [value for value, _ in recipe_refs], format_func=lambda item: next(label for value, label in recipe_refs if value == item), index=next((index for index, (value, _) in enumerate(recipe_refs) if value == selected_ref), 0))
        favorite_template = st.checkbox("Favorite template", value=selected_template.get("favorite", False) if selected_template else False)
        save_template = st.form_submit_button("Save template")
        delete_template = st.form_submit_button("Delete template") if selected_template else False
    if save_template:
        if not template_name.strip():
            st.error("Template name is required.")
        else:
            template = {
                "id": selected_template["id"] if selected_template else uuid4().hex,
                "name": template_name.strip(),
                "description": template_description.strip(),
                "linked_recipe_ref": linked_recipe_ref,
                "favorite": favorite_template,
            }
            profile["meal_templates"] = [item for item in templates if item["id"] != template["id"]] + [template]
            persist_active_profile(profile)
            st.rerun()
    if delete_template and selected_template:
        profile["meal_templates"] = [item for item in templates if item["id"] != selected_template["id"]]
        persist_active_profile(profile)
        st.rerun()


def render_recipe_manager(profile, favorites_only):
    st.markdown("**Recipes**")
    recipes = profile.get("recipes", [])
    builtin_count = len(all_recipe_dishes())
    visible_recipes = [item for item in recipes if not favorites_only or item.get("favorite")]
    if visible_recipes:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Name": item["name"],
                        "Serves": format_number(item.get("base_servings", 2.0)),
                        "Favorite": "Yes" if item.get("favorite") else "",
                    }
                    for item in visible_recipes
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(f"No custom recipes yet. The planner still includes {builtin_count} built-in YAML recipes below.")
        if st.button("Add Recipes", key=f"empty_recipes_{profile['id']}", use_container_width=True):
            jump_to_anchor("recipes-section")
            st.rerun()

    recipe_options = {"Add new recipe": ""}
    for item in recipes:
        recipe_options[f"Edit {item['name']}"] = item["id"]
    selected_recipe_id = st.selectbox("Recipe", list(recipe_options.values()), format_func=lambda item: next(label for label, value in recipe_options.items() if value == item), key=f"recipe_editor_{profile['id']}")
    selected_recipe = next((item for item in recipes if item["id"] == selected_recipe_id), None)
    with st.form(f"recipe_form_{profile['id']}"):
        recipe_name = st.text_input("Recipe name", value=selected_recipe.get("name", "") if selected_recipe else "")
        recipe_description = st.text_area("Description", value=selected_recipe.get("description", "") if selected_recipe else "", height=80)
        base_servings = st.number_input("Base serving count", min_value=1.0, max_value=12.0, step=0.5, value=float(selected_recipe.get("base_servings", 2.0) if selected_recipe else 2.0))
        recipe_ingredients = st.text_area("Ingredients (one per line: name | quantity | unit | notes)", value=ingredient_lines_from_recipe(selected_recipe) if selected_recipe else "", height=150)
        recipe_instructions = st.text_area("Instructions (one step per line)", value=instructions_text(selected_recipe.get("instructions", [])) if selected_recipe else "", height=150)
        recipe_youtube_link = st.text_input("Optional YouTube link", value=selected_recipe.get("youtube", "") if selected_recipe else "")
        favorite_recipe = st.checkbox("Favorite recipe", value=selected_recipe.get("favorite", False) if selected_recipe else False)
        save_recipe = st.form_submit_button("Save recipe")
        delete_recipe = st.form_submit_button("Delete recipe") if selected_recipe else False
    if save_recipe:
        if not recipe_name.strip():
            st.error("Recipe name is required.")
        else:
            recipe = normalize_recipe(
                {
                    "id": selected_recipe["id"] if selected_recipe else uuid4().hex,
                    "name": recipe_name.strip(),
                    "description": recipe_description.strip(),
                    "base_servings": base_servings,
                    "ingredients": parse_ingredient_lines(recipe_ingredients),
                    "instructions": [line.strip() for line in recipe_instructions.splitlines() if line.strip()],
                    "youtube": recipe_youtube_link.strip(),
                    "favorite": favorite_recipe,
                }
            )
            profile["recipes"] = [item for item in recipes if item["id"] != recipe["id"]] + [recipe]
            persist_active_profile(profile)
            st.rerun()
    if delete_recipe and selected_recipe:
        profile["recipes"] = [item for item in recipes if item["id"] != selected_recipe["id"]]
        profile["meal_templates"] = [
            {**template, "linked_recipe_ref": "" if template.get("linked_recipe_ref") == f"profile::{selected_recipe['id']}" else template.get("linked_recipe_ref", "")}
            for template in profile.get("meal_templates", [])
        ]
        persist_active_profile(profile)
        st.rerun()

    st.markdown(
        f"<div class='library-note'>Current household serving total: <strong>{format_number(household_servings(profile))}</strong>. "
        "Profile recipe ingredients scale against this total in the planner and recipe view.</div>",
        unsafe_allow_html=True,
    )


def inventory_category_lookup(profile):
    return {item["id"]: item for item in profile.get("inventory_categories", [])}


def inventory_location_lookup(profile):
    return {item["id"]: item for item in profile.get("storage_locations", [])}


def inventory_item_lookup(profile):
    return {item["id"]: item for item in profile.get("inventory", [])}


def active_lots(item):
    return [lot for lot in item.get("lots", []) if lot.get("status") not in {"finished", "expired"}]


def inventory_total_quantity(item):
    return sum(lot.get("quantity", 0.0) for lot in active_lots(item))


def item_expiry_date(profile, item, lot):
    if lot.get("expiry_date"):
        return lot["expiry_date"]
    base_date = lot.get("opened_date") or lot.get("purchase_date") or item.get("opened_date") or item.get("purchase_date")
    if not base_date:
        return ""
    try:
        start = date.fromisoformat(base_date)
    except ValueError:
        return ""
    category = inventory_category_lookup(profile).get(item.get("category_id", ""))
    shelf_life_days = item.get("shelf_life_days") or (category or {}).get("shelf_life_days") or 0
    if not shelf_life_days:
        return ""
    return (start + timedelta(days=int(shelf_life_days))).isoformat()


def days_to_expiry(expiry_value):
    if not expiry_value:
        return None
    try:
        return (date.fromisoformat(expiry_value) - date.today()).days
    except ValueError:
        return None


def item_low_stock(item):
    refill_level = item.get("refill_level")
    return refill_level is not None and inventory_total_quantity(item) <= refill_level


def item_over_capacity(item):
    capacity = item.get("storage_capacity")
    return capacity is not None and inventory_total_quantity(item) > capacity


def item_approx_status(item):
    if item.get("approx_status"):
        return item["approx_status"]
    total = inventory_total_quantity(item)
    if total <= 0:
        return "Finished"
    capacity = item.get("storage_capacity")
    refill_level = item.get("refill_level")
    if capacity and capacity > 0:
        ratio = total / capacity
        if ratio >= 0.66:
            return "Full"
        if ratio >= 0.33:
            return "Half"
        return "Low"
    if refill_level is not None:
        return "Low" if total <= refill_level else "Half"
    return "Half"


def item_status(profile, item):
    if inventory_total_quantity(item) <= 0:
        return "Low"
    if item_over_capacity(item):
        return "Over Capacity"
    for lot in active_lots(item):
        expiry_value = item_expiry_date(profile, item, lot)
        if days_to_expiry(expiry_value) is not None and days_to_expiry(expiry_value) <= 7:
            return "Expiring"
    if item_low_stock(item):
        return "Low"
    return "OK"


def item_location_name(profile, item):
    location = inventory_location_lookup(profile).get(item.get("location_id", ""))
    if location:
        return location["name"]
    first_lot = item.get("lots", [{}])[0]
    return inventory_location_lookup(profile).get(first_lot.get("location_id", ""), {}).get("name", "")


def category_name(profile, category_id):
    return inventory_category_lookup(profile).get(category_id, {}).get("name", "Other Kitchen")


def category_defaults_for_id(profile, category_id):
    return inventory_category_lookup(profile).get(category_id, {})


def location_id_from_default_name(profile, location_name):
    if not location_name:
        return ""
    for location in profile.get("storage_locations", []):
        if location["name"] == location_name:
            return location["id"]
    return ""


def is_home_supply_category_name(name):
    return name in HOME_SUPPLY_CATEGORY_NAMES


def is_home_supply_item(profile, item):
    return is_home_supply_category_name(category_name(profile, item.get("category_id", "")))


def food_inventory_items(profile):
    return [item for item in profile.get("inventory", []) if not item.get("archived") and not is_home_supply_item(profile, item)]


def home_supply_items(profile):
    return [item for item in profile.get("inventory", []) if not item.get("archived") and is_home_supply_item(profile, item)]


def home_supply_category_ids(profile):
    return [item["id"] for item in profile.get("inventory_categories", []) if is_home_supply_category_name(item["name"])]


def inventory_rows_for_items(profile, items):
    rows = []
    for item in items:
        rows.append(
            {
                "id": item["id"],
                "Item name": item["name"],
                "Category": category_name(profile, item.get("category_id", "")),
                "Current quantity": format_number(inventory_total_quantity(item)),
                "Unit": item.get("unit", ""),
                "Approx status": item_approx_status(item),
                "Refill level": format_number(item.get("refill_level")),
                "Storage capacity": format_number(item.get("storage_capacity")),
                "Location": item_location_name(profile, item),
                "Preferred vendor": item.get("preferred_vendor", ""),
                "Preferred brand": item.get("preferred_brand", ""),
                "Status": item_status(profile, item),
            }
        )
    return rows


def inventory_rows(profile):
    return inventory_rows_for_items(profile, profile.get("inventory", []))


def inventory_empty(profile, items=None):
    if items is None:
        items = profile.get("inventory", [])
    return not items


def save_inventory_item(profile, item):
    profile["inventory"] = [entry for entry in profile.get("inventory", []) if entry["id"] != item["id"]] + [normalize_inventory_item(item)]


def add_inventory_transaction(profile, item, change_value, action, reason, notes=""):
    profile["inventory_transactions"] = [
        normalize_inventory_transaction(
            {
                "item_id": item.get("id", ""),
                "item_name": item.get("name", ""),
                "change_value": change_value,
                "unit": item.get("unit", ""),
                "action": action,
                "reason": reason,
                "notes": notes,
                "source": "manual",
            }
        ),
        *profile.get("inventory_transactions", []),
    ]


def add_inventory_transaction_with_source(profile, item, change_value, action, reason, notes="", source="manual"):
    profile["inventory_transactions"] = [
        normalize_inventory_transaction(
            {
                "item_id": item.get("id", ""),
                "item_name": item.get("name", ""),
                "change_value": change_value,
                "unit": item.get("unit", ""),
                "action": action,
                "reason": reason,
                "notes": notes,
                "source": source,
            }
        ),
        *profile.get("inventory_transactions", []),
    ]


def build_new_item(name, quantity, category_id, unit="unit"):
    purchase_date = today_iso()
    defaults = category_defaults_for_id({"inventory_categories": default_inventory_categories()}, category_id)
    resolved_unit = unit or defaults.get("default_unit") or "unit"
    item = normalize_inventory_item(
        {
            "name": name,
            "category_id": category_id,
            "unit": resolved_unit,
            "purchase_date": purchase_date,
            "refill_level": defaults.get("default_refill_level"),
            "location_id": location_id_from_default_name({"storage_locations": default_storage_locations()}, defaults.get("default_location_name", "")),
            "preferred_vendor": defaults.get("default_vendor_name", ""),
            "lots": [
                {
                    "quantity": quantity,
                    "unit": resolved_unit,
                    "status": "sealed" if quantity > 0 else "finished",
                    "purchase_date": purchase_date,
                }
            ],
        }
    )
    return item


def parse_purchase_date(value):
    raw = str(value or "").strip()
    if not raw:
        return today_iso()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def purchase_import_category_id(profile, item_name, unit):
    name = str(item_name or "").lower()
    unit_value = str(unit or "").lower()
    keyword_map = [
        ("Dry Fruits / Seeds", ["kaju", "chironji", "pumpkin seeds"]),
        ("Fruits", ["mango", "pomegranate", "cherry", "jamun", "peach", "avocado"]),
        ("Vegetables", ["ginger", "cucumber", "capsicum", "coriander", "lauki", "gourd", "onion", "sweet potato", "pumpkin", "tomato", "jackfruit"]),
        ("Masale / Spices", ["haldi", "mirch", "jeera", "kalonji", "black salt", "meetha soda"]),
        ("Grains / Rice / Atta", ["besan", "matar"]),
        ("Dairy / Eggs", ["cream cheese", "dosa batter"]),
        ("Protein / Health", ["tofu"]),
        ("Pickles / Papad / Chutney", ["papad", "imli", "vinegar"]),
        ("Snacks / Makhana", ["bread"]),
    ]
    if unit_value == "adjustment":
        return slugify_name("Other Kitchen")
    for category, keywords in keyword_map:
        if any(keyword in name for keyword in keywords):
            return slugify_name(category)
    return slugify_name("Other Kitchen")


def parse_purchase_import_rows(raw_text):
    text = str(raw_text or "").strip()
    if not text:
        return []
    reader = csv.DictReader(StringIO(text))
    rows = []
    for row in reader:
        if not row:
            continue
        item_name = str(row.get("Item", "")).strip()
        if not item_name:
            continue
        quantity = try_float(row.get("Quantity"))
        rate_value = try_float(row.get("Rate (₹)"))
        amount_value = try_float(row.get("Amount (₹)"))
        rows.append(
            {
                "date": parse_purchase_date(row.get("Date", "")),
                "location": str(row.get("Location", "")).strip(),
                "bill_no": str(row.get("Bill No", "")).strip(),
                "item": item_name,
                "quantity": quantity or 0.0,
                "unit": str(row.get("Unit", "")).strip() or "unit",
                "rate": rate_value,
                "amount": amount_value,
            }
        )
    return rows


def review_items_from_import_rows(profile, rows, parse_source="csv"):
    items = []
    for row in rows:
        notes = " | ".join(
            part
            for part in [
                f"Bill {row['bill_no']}" if row.get("bill_no") else "",
                f"Rate Rs {format_number(row['rate'])}" if row.get("rate") is not None else "",
                f"Amount Rs {format_number(row['amount'])}" if row.get("amount") is not None else "",
            ]
            if part
        )
        items.append(
            build_review_item(
                profile,
                row["item"],
                row["quantity"],
                row["unit"],
                vendor_name=row.get("location", ""),
                price=row.get("amount"),
                purchase_date=row.get("date", today_iso()),
                notes=notes,
                parse_source=parse_source,
                raw_text=row.get("item", ""),
            )
        )
    return items


def tokenize_name(value):
    return [token for token in re.split(r"[^a-z0-9]+", str(value or "").lower()) if token]


def home_supply_keywords():
    return ["lizol", "detergent", "garbage", "toilet cleaner", "toothpaste", "harpic", "phenyl", "cleaner", "dishwash"]


def destination_for_item_name(name):
    lowered = str(name or "").lower()
    return "Home Supplies" if any(keyword in lowered for keyword in home_supply_keywords()) else "Inventory"


def home_supply_category_id_for_name(name):
    lowered = str(name or "").lower()
    if any(keyword in lowered for keyword in ["lizol", "toilet cleaner", "floor cleaner", "bathroom cleaner", "dishwash", "scrub"]):
        return slugify_name("Cleaning")
    if any(keyword in lowered for keyword in ["detergent", "fabric softener", "stain remover"]):
        return slugify_name("Laundry")
    if any(keyword in lowered for keyword in ["tissue", "kitchen roll", "toilet paper", "garbage", "foil", "cling wrap", "butter paper"]):
        return slugify_name("Paper / Disposables")
    if any(keyword in lowered for keyword in ["toothpaste", "soap", "shampoo", "conditioner", "face wash", "deodorant", "shaving", "sanitary"]):
        return slugify_name("Personal Care")
    if any(keyword in lowered for keyword in ["battery", "bulb", "candle", "matchbox", "lighter", "mosquito repellent"]):
        return slugify_name("Utilities")
    if any(keyword in lowered for keyword in ["ro filter", "gas cylinder", "appliance"]):
        return slugify_name("Maintenance")
    return slugify_name("Other Supplies")


def category_for_detected_name(profile, name, unit):
    if destination_for_item_name(name) == "Home Supplies":
        return home_supply_category_id_for_name(name)
    return purchase_import_category_id(profile, name, unit)


def parser_confidence(score):
    if score >= 0.88:
        return "High"
    if score >= 0.68:
        return "Medium"
    return "Low"


def match_inventory_item(profile, detected_name, brand=""):
    detected_tokens = set(tokenize_name(detected_name))
    best_item = None
    best_score = 0.0
    for item in profile.get("inventory", []):
        names = [item.get("name", "")] + item.get("aliases", [])
        if item.get("preferred_brand"):
            names.append(f"{item['preferred_brand']} {item.get('name', '')}")
        for candidate in names:
            ratio = SequenceMatcher(None, str(candidate).lower(), str(detected_name).lower()).ratio()
            candidate_tokens = set(tokenize_name(candidate))
            overlap = len(detected_tokens & candidate_tokens) / max(len(detected_tokens | candidate_tokens), 1)
            score = max(ratio, overlap)
            if brand and item.get("preferred_brand", "").lower() == brand.lower():
                score += 0.1
            if score > best_score:
                best_item = item
                best_score = score
    return best_item, min(best_score, 1.0)


def build_review_item(profile, detected_name, quantity, unit, vendor_name="", brand="", price=None, purchase_date="", notes="", parse_source="manual", raw_text=""):
    matched_item, score = match_inventory_item(profile, detected_name, brand)
    category_id = matched_item.get("category_id", slugify_name("Other Kitchen")) if matched_item else category_for_detected_name(profile, detected_name, unit)
    item_name = matched_item["name"] if matched_item else detected_name
    destination = "Home Supplies" if is_home_supply_category_name(category_name(profile, category_id)) else "Inventory"
    return normalize_purchase_review_item(
        {
            "detected_name": detected_name,
            "item_name": item_name,
            "matched_item_id": matched_item["id"] if matched_item else "",
            "category_id": category_id,
            "destination": destination,
            "quantity": quantity,
            "unit": unit,
            "packet_format": unit,
            "brand": brand or (matched_item.get("preferred_brand", "") if matched_item else ""),
            "vendor_name": vendor_name or (matched_item.get("preferred_vendor", "") if matched_item else "Other"),
            "price": price,
            "purchase_date": purchase_date or today_iso(),
            "confidence": parser_confidence(score),
            "parse_source": parse_source,
            "raw_text": raw_text,
            "notes": notes,
        }
    )


def parse_purchase_fragment(fragment):
    text = str(fragment or "").strip(" .")
    if not text:
        return None
    match = re.search(r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|gm|l|ml|litre|liter|pc|pcs|packet|packets|pack|packs|bottle|bottles|box|boxes|dozen)?\s+(?P<name>.+)", text, re.I)
    if match:
        quantity = try_float(match.group("qty")) or 0.0
        unit = (match.group("unit") or "unit").lower()
        name = match.group("name").strip()
    else:
        quantity = 1.0
        unit = "unit"
        name = text
    name = re.sub(r"^(of|x)\s+", "", name, flags=re.I).strip()
    brand = ""
    brand_match = re.match(r"([A-Z][A-Za-z0-9&']+)\s+(.+)", name)
    if brand_match and len(tokenize_name(brand_match.group(2))) >= 1:
        brand = brand_match.group(1)
    normalized_unit = {
        "pcs": "pc",
        "packets": "packet",
        "packs": "pack",
        "bottles": "bottle",
        "boxes": "box",
        "litre": "L",
        "liter": "L",
    }.get(unit, unit)
    return {"detected_name": name, "quantity": quantity, "unit": normalized_unit, "brand": brand}


def parse_text_purchase_rows(profile, raw_text):
    text = str(raw_text or "").strip()
    if not text:
        return [], ""
    vendor_name = ""
    vendor_match = re.search(r"\bfrom\s+([A-Za-z0-9 /&'-]+)", text, re.I)
    if vendor_match:
        vendor_name = vendor_match.group(1).strip().rstrip(".")
        text = text[:vendor_match.start()].strip(" .")
    text = re.sub(r"^bought\s+", "", text, flags=re.I)
    parts = [part.strip() for part in re.split(r",|\band\b", text) if part.strip()]
    review_items = []
    for part in parts:
        parsed = parse_purchase_fragment(part)
        if not parsed:
            continue
        review_items.append(
            build_review_item(
                profile,
                parsed["detected_name"],
                parsed["quantity"],
                parsed["unit"],
                vendor_name=vendor_name,
                brand=parsed.get("brand", ""),
                parse_source="text",
                raw_text=raw_text,
            )
        )
    error_message = "" if review_items else "We could not confidently read this. You can edit the detected text or add items manually."
    return review_items, error_message


def parse_invoice_image_rows(profile, uploaded_image, helper_text):
    if helper_text.strip():
        return parse_text_purchase_rows(profile, helper_text)
    if uploaded_image is None:
        return [], ""
    return [], "We could not confidently read this. You can edit the detected text or add items manually."


def set_purchase_review_items(items, source="", error_message=""):
    st.session_state.purchase_review_items = [normalize_purchase_review_item(item) for item in items]
    st.session_state.purchase_review_source = source
    st.session_state.purchase_review_error = error_message


def get_purchase_review_items():
    return [normalize_purchase_review_item(item) for item in st.session_state.get("purchase_review_items", [])]


def confirm_purchase_review_item(profile, review_item):
    matched_item = inventory_item_lookup(profile).get(review_item.get("matched_item_id", ""))
    item = matched_item
    if not item:
        item = build_new_item(review_item["item_name"], review_item["quantity"], review_item["category_id"], review_item["unit"])
        item["lots"] = []
        defaults = category_defaults_for_id(profile, review_item["category_id"])
        item["refill_level"] = defaults.get("default_refill_level")
        if not review_item.get("location_id"):
            review_item["location_id"] = location_id_from_default_name(profile, defaults.get("default_location_name", ""))
        if not review_item.get("vendor_name"):
            review_item["vendor_name"] = defaults.get("default_vendor_name", "Other") or "Other"
    lot = normalize_inventory_lot(
        {
            "quantity": review_item["quantity"],
            "unit": review_item["packet_format"] or review_item["unit"],
            "status": "sealed",
            "purchase_date": review_item["purchase_date"],
            "location_id": review_item.get("location_id", ""),
            "vendor": review_item["vendor_name"],
            "brand": review_item["brand"],
            "price": review_item.get("price"),
            "notes": review_item.get("notes", ""),
        },
        item,
    )
    item["name"] = review_item["item_name"]
    item["category_id"] = review_item["category_id"]
    item["preferred_vendor"] = review_item["vendor_name"]
    item["preferred_brand"] = review_item["brand"]
    item["preferred_purchase_quantity"] = review_item["quantity"]
    item["preferred_purchase_unit"] = review_item["packet_format"] or review_item["unit"]
    item["purchase_date"] = review_item["purchase_date"]
    item["location_id"] = review_item.get("location_id", "")
    item["unit"] = item.get("unit") or review_item["unit"]
    item["lots"] = [lot, *item.get("lots", [])]
    save_inventory_item(profile, item)
    add_inventory_transaction_with_source(profile, item, review_item["quantity"], "Add", "purchase", review_item.get("notes", ""), source=f"{review_item.get('parse_source', 'manual')}_review")
    for suggestion in build_shopping_suggestions(profile):
        if suggestion["item_name"].strip().lower() == review_item["item_name"].strip().lower():
            clear_shopping_override(profile, suggestion["id"], "quantity_override", "unit_override", "vendor_name", "skipped_on", "snooze_until", "removed")
            if suggestion["source"] == "manual":
                for manual_item in profile.get("shopping_manual_items", []):
                    if manual_item["id"] == suggestion["manual_id"]:
                        manual_item["status"] = "purchased"
    return item


def import_purchase_rows(profile, rows):
    imported_count = 0
    total_amount = 0.0
    for row in rows:
        item_name = row["item"]
        unit = row["unit"] or "unit"
        category_id = purchase_import_category_id(profile, item_name, unit)
        existing = next((item for item in profile.get("inventory", []) if item["name"].strip().lower() == item_name.strip().lower()), None)
        notes = " | ".join(
            part
            for part in [
                f"Bill {row['bill_no']}" if row.get("bill_no") else "",
                f"Rate Rs {format_number(row['rate'])}" if row.get("rate") is not None else "",
                f"Amount Rs {format_number(row['amount'])}" if row.get("amount") is not None else "",
            ]
            if part
        )
        if existing:
            new_lot = normalize_inventory_lot(
                {
                    "quantity": row["quantity"],
                    "unit": unit,
                    "status": "sealed" if row["quantity"] > 0 else "finished",
                    "purchase_date": row["date"],
                    "vendor": row.get("location", ""),
                    "price": row.get("amount"),
                    "notes": notes,
                },
                existing,
            )
            existing["lots"] = [new_lot, *existing.get("lots", [])]
            if row.get("location"):
                existing["preferred_vendor"] = row["location"]
            save_inventory_item(profile, existing)
            add_inventory_transaction_with_source(profile, existing, row["quantity"], "Add", "purchase", notes, source="purchase_import")
        else:
            item = build_new_item(item_name, row["quantity"], category_id, unit)
            item["purchase_date"] = row["date"]
            item["preferred_vendor"] = row.get("location", "")
            item["preferred_purchase_quantity"] = row["quantity"] or None
            item["preferred_purchase_unit"] = unit
            item["notes"] = notes
            item["lots"][0]["purchase_date"] = row["date"]
            item["lots"][0]["vendor"] = row.get("location", "")
            item["lots"][0]["price"] = row.get("amount")
            item["lots"][0]["notes"] = notes
            save_inventory_item(profile, item)
            add_inventory_transaction_with_source(profile, item, row["quantity"], "Add", "purchase", notes, source="purchase_import")
        imported_count += 1
        total_amount += row.get("amount") or 0.0
    return imported_count, round(total_amount, 2)


def quantity_delta_text(change_value, unit):
    if change_value > 0:
        return f"+{format_number(change_value)} {unit}".strip()
    return f"{format_number(change_value)} {unit}".strip()


def vendor_lookup(profile):
    return {item["name"]: item for item in profile.get("vendors", [])}


def default_vendor_name_for_category(profile, category_id):
    category = category_name(profile, category_id)
    for vendor in profile.get("vendors", []):
        if category in vendor.get("preferred_categories", []):
            return vendor["name"]
    if category in {"Cleaning", "Laundry", "Paper / Disposables", "Utilities", "Maintenance", "Kitchen Non-Food", "Other Supplies"}:
        return "Amazon / DMart"
    if category in {"Personal Care", "Bathroom"}:
        return "Pharmacy"
    if category == "Vegetables":
        return "Sabzi Vendor"
    if category in {"Fruits", "Dairy / Eggs", "Protein / Health"}:
        return "BigBasket"
    if category in {"Masale / Spices", "Grains / Rice / Atta", "Dal / Pulses", "Dry Fruits / Seeds", "Oil / Ghee", "Pickles / Papad / Chutney"}:
        return "Kirana"
    return "Other"


def purchase_history_for_item(item):
    rows = []
    for lot in item.get("lots", []):
        if not lot.get("purchase_date"):
            continue
        price = try_float(lot.get("price"))
        quantity = try_float(lot.get("quantity")) or 0.0
        price_per_unit = round(price / quantity, 2) if price is not None and quantity > 0 else None
        rows.append(
            {
                "date": lot.get("purchase_date", ""),
                "vendor": lot.get("vendor", ""),
                "brand": lot.get("brand", ""),
                "quantity": quantity,
                "unit": lot.get("unit", item.get("unit", "")),
                "price": price,
                "price_per_unit": price_per_unit,
                "status": lot.get("status", ""),
                "notes": lot.get("notes", ""),
            }
        )
    rows.sort(key=lambda row: row["date"], reverse=True)
    return rows


def price_summary_for_item(item):
    history = purchase_history_for_item(item)
    prices = [row["price_per_unit"] for row in history if row.get("price_per_unit") is not None]
    last_purchase = history[0] if history else None
    if not prices:
        return {
            "last_purchase": last_purchase,
            "last_price": last_purchase.get("price") if last_purchase else None,
            "average_price": None,
            "lowest_price": None,
            "highest_price": None,
            "trend": "usual",
        }
    average_price = round(sum(prices) / len(prices), 2)
    last_price = prices[0]
    if last_price >= average_price * 1.1:
        trend = "slightly higher"
    elif last_price <= average_price * 0.9:
        trend = "lower"
    else:
        trend = "usual"
    return {
        "last_purchase": last_purchase,
        "last_price": last_purchase.get("price") if last_purchase else None,
        "average_price": average_price,
        "lowest_price": min(prices),
        "highest_price": max(prices),
        "trend": trend,
    }


def average_purchase_interval_days(item):
    purchase_dates = []
    for row in purchase_history_for_item(item):
        try:
            purchase_dates.append(date.fromisoformat(row["date"]))
        except ValueError:
            continue
    unique_dates = sorted(set(purchase_dates))
    if len(unique_dates) < 2:
        return None
    intervals = [(later - earlier).days for earlier, later in zip(unique_dates, unique_dates[1:]) if (later - earlier).days > 0]
    if not intervals:
        return None
    return round(sum(intervals) / len(intervals))


def latest_purchase_date(item):
    history = purchase_history_for_item(item)
    return history[0]["date"] if history else ""


def parse_iso_date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def inventory_transactions_for_item(profile, item):
    return [entry for entry in profile.get("inventory_transactions", []) if entry.get("item_id") == item.get("id")]


def usage_transactions_for_item(profile, item):
    rows = []
    for entry in inventory_transactions_for_item(profile, item):
        change_value = try_float(entry.get("change_value")) or 0.0
        reason = str(entry.get("reason", "")).lower()
        action = str(entry.get("action", "")).lower()
        if change_value >= 0:
            continue
        if reason in WASTE_REASONS or action in WASTE_REASONS:
            continue
        rows.append(entry)
    return rows


def waste_transactions_for_item(profile, item):
    rows = []
    for entry in inventory_transactions_for_item(profile, item):
        reason = str(entry.get("reason", "")).lower()
        action = str(entry.get("action", "")).lower()
        if reason in WASTE_REASONS or action in WASTE_REASONS:
            rows.append(entry)
    return rows


def average_usage_metrics(profile, item):
    usage_rows = usage_transactions_for_item(profile, item)
    if not usage_rows:
        return {
            "weekly": None,
            "monthly": None,
            "avg_event_quantity": None,
            "trend": "stable",
            "confidence": "Low",
            "daily_rate": None,
            "events": 0,
        }
    dated = []
    for entry in usage_rows:
        used_on = parse_iso_date(str(entry.get("created_at", "")).split("T")[0])
        if used_on is None:
            continue
        dated.append((used_on, abs(try_float(entry.get("change_value")) or 0.0)))
    if not dated:
        return {
            "weekly": None,
            "monthly": None,
            "avg_event_quantity": None,
            "trend": "stable",
            "confidence": "Low",
            "daily_rate": None,
            "events": 0,
        }
    dated.sort(key=lambda item: item[0])
    days_span = max((dated[-1][0] - dated[0][0]).days, 1)
    total_used = sum(value for _day, value in dated)
    daily_rate = total_used / max(days_span, 1)
    weekly = round(daily_rate * 7, 2)
    monthly = round(daily_rate * 30, 2)
    avg_event_quantity = round(total_used / len(dated), 2)
    recent_30 = sum(value for day, value in dated if (date.today() - day).days <= 30)
    prev_30 = sum(value for day, value in dated if 30 < (date.today() - day).days <= 60)
    if prev_30 and recent_30 >= prev_30 * 1.2:
        trend = "increasing"
    elif prev_30 and recent_30 <= prev_30 * 0.8:
        trend = "decreasing"
    else:
        trend = "stable"
    confidence = "High" if len(dated) >= 6 else "Medium" if len(dated) >= 3 else "Low"
    return {
        "weekly": weekly,
        "monthly": monthly,
        "avg_event_quantity": avg_event_quantity,
        "trend": trend,
        "confidence": confidence,
        "daily_rate": round(daily_rate, 4),
        "events": len(dated),
    }


def item_prediction_summary(profile, item):
    metrics = average_usage_metrics(profile, item)
    current_qty = inventory_total_quantity(item)
    refill_level = item.get("refill_level")
    capacity = item.get("storage_capacity")
    preferred_qty = item.get("preferred_purchase_quantity")
    preferred_unit = item.get("preferred_purchase_unit", "") or item.get("unit", "")
    interval_days = average_purchase_interval_days(item)
    daily_rate = metrics.get("daily_rate")
    days_until_refill = None
    if daily_rate and daily_rate > 0 and refill_level is not None and current_qty > refill_level:
        days_until_refill = max(round((current_qty - refill_level) / daily_rate), 0)
    elif daily_rate and daily_rate > 0 and current_qty > 0:
        days_until_refill = max(round(current_qty / daily_rate), 0)
    monthly_use = metrics.get("monthly")
    predicted_buy_qty = preferred_qty or 0.0
    if monthly_use:
        predicted_buy_qty = max(predicted_buy_qty, round(monthly_use / 2, 2))
    if refill_level is not None:
        predicted_buy_qty = max(predicted_buy_qty, max(refill_level - current_qty, 0.0))
    if predicted_buy_qty <= 0:
        predicted_buy_qty = preferred_qty or 0.0
    capacity_note = ""
    if capacity is not None and predicted_buy_qty > 0:
        remaining_capacity = max(capacity - current_qty, 0.0)
        if predicted_buy_qty > remaining_capacity and remaining_capacity > 0:
            predicted_buy_qty = round(remaining_capacity, 2)
            capacity_note = "Storage capacity limits suggested quantity."
        elif remaining_capacity <= 0:
            capacity_note = "Storage capacity is already full."
    confidence = metrics.get("confidence", "Low")
    why_parts = []
    if monthly_use:
        why_parts.append(f"monthly use is about {format_number(monthly_use)} {item.get('unit', '')}")
    if refill_level is not None:
        why_parts.append(f"refill level is {format_number(refill_level)}")
    if current_qty is not None:
        why_parts.append(f"current stock is {format_number(current_qty)}")
    if interval_days:
        why_parts.append(f"usual purchase interval is {interval_days} days")
    return {
        "days_until_refill": days_until_refill,
        "predicted_buy_qty": round(predicted_buy_qty, 2) if predicted_buy_qty else 0.0,
        "predicted_unit": preferred_unit,
        "confidence": confidence,
        "why": ", ".join(why_parts),
        "capacity_note": capacity_note,
        "monthly_use": monthly_use,
        "weekly_use": metrics.get("weekly"),
        "trend": metrics.get("trend", "stable"),
    }


def vendor_price_rows(profile):
    rows = []
    for item in profile.get("inventory", []):
        for row in purchase_history_for_item(item):
            if row.get("price_per_unit") is None:
                continue
            rows.append(
                {
                    "item_name": item["name"],
                    "vendor": row["vendor"] or item.get("preferred_vendor", "Other"),
                    "brand": row["brand"] or item.get("preferred_brand", ""),
                    "category": category_name(profile, item.get("category_id", "")),
                    "price": row["price"],
                    "price_per_unit": row["price_per_unit"],
                    "quantity": row["quantity"],
                    "unit": row["unit"],
                    "date": row["date"],
                }
            )
    return rows


def vendor_comparison_rows(profile):
    by_vendor = OrderedDict()
    for row in vendor_price_rows(profile):
        vendor = row["vendor"] or "Other"
        bucket = by_vendor.setdefault(vendor, {"vendor": vendor, "items": set(), "categories": set(), "spend": 0.0, "prices": [], "recent": []})
        bucket["items"].add(row["item_name"])
        bucket["categories"].add(row["category"])
        bucket["spend"] += row.get("price") or 0.0
        bucket["prices"].append(row["price_per_unit"])
        bucket["recent"].append(row)
    rows = []
    for vendor, bucket in by_vendor.items():
        rows.append(
            {
                "Vendor": vendor,
                "Items": len(bucket["items"]),
                "Preferred categories": ", ".join(sorted(bucket["categories"])),
                "Average spend": round(bucket["spend"] / max(len(bucket["recent"]), 1), 2),
                "Average price/unit": round(sum(bucket["prices"]) / len(bucket["prices"]), 2) if bucket["prices"] else None,
                "Recent purchases": len(bucket["recent"]),
            }
        )
    return rows


def waste_insight_rows(profile):
    rows = []
    for item in profile.get("inventory", []):
        waste_rows = waste_transactions_for_item(profile, item)
        if not waste_rows:
            continue
        total_waste = round(sum(abs(try_float(entry.get("change_value")) or 0.0) for entry in waste_rows), 2)
        reason_counts = OrderedDict()
        for entry in waste_rows:
            reason = entry.get("reason", "") or entry.get("action", "")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        suggestion = "Consider a smaller buying quantity." if total_waste > 0 else ""
        rows.append(
            {
                "Item": item["name"],
                "Category": category_name(profile, item.get("category_id", "")),
                "Quantity wasted": total_waste,
                "Reasons": ", ".join(reason_counts.keys()),
                "Suggested action": suggestion or "Use earlier in the cycle.",
            }
        )
    return rows


def storage_insight_rows(profile):
    rows = []
    for location in profile.get("storage_locations", []):
        usage = 0.0
        top_items = []
        for item in profile.get("inventory", []):
            item_usage = 0.0
            for lot in active_lots(item):
                if lot.get("location_id") == location["id"]:
                    item_usage += lot.get("quantity", 0.0)
            if item_usage:
                usage += item_usage
                top_items.append((item["name"], item_usage))
        top_items.sort(key=lambda item: item[1], reverse=True)
        rows.append(
            {
                "Location": location["name"],
                "Usage": format_number(usage),
                "Capacity": format_number(location.get("capacity_value")),
                "Status": "Over Capacity" if location.get("capacity_value") and usage > location.get("capacity_value") else "OK",
                "Top items": ", ".join(name for name, _qty in top_items[:3]),
            }
        )
    return rows


def current_season_label():
    month = date.today().month
    if month in {4, 5, 6, 7, 8}:
        return "Summer"
    if month in {11, 12, 1, 2}:
        return "Winter"
    return "Between seasons"


def seasonal_insight_rows(profile):
    season = current_season_label()
    rows = []
    for item in profile.get("inventory", []):
        lowered = item.get("name", "").lower()
        matched_season = next((label for label, names in SEASONAL_ITEMS.items() if any(name in lowered for name in names)), "")
        if not matched_season:
            continue
        waste_rows = waste_transactions_for_item(profile, item)
        weather_mode = profile.get("preferences", {}).get("weather_mode", "Normal")
        reason = f"{item['name']} is commonly used in {matched_season.lower()}."
        if weather_mode == "Hot / Humid" and category_name(profile, item.get("category_id", "")) in {"Fruits", "Vegetables", "Dairy / Eggs"}:
            reason += " Hot/humid conditions make spoilage risk higher."
        if waste_rows:
            reason += " Past waste suggests buying a little less."
        rows.append(
            {
                "Item": item["name"],
                "Season": matched_season,
                "Current stock": format_number(inventory_total_quantity(item)),
                "Reason": reason,
                "Confidence": "Medium" if waste_rows else "Low",
            }
        )
    return rows


def prediction_rows(profile):
    rows = []
    for item in profile.get("inventory", []):
        prediction = item_prediction_summary(profile, item)
        if prediction["days_until_refill"] is None and not prediction["predicted_buy_qty"]:
            continue
        rows.append(
            {
                "Item": item["name"],
                "Next refill": "" if prediction["days_until_refill"] is None else f"{prediction['days_until_refill']} days",
                "Suggested quantity": "" if not prediction["predicted_buy_qty"] else f"{format_number(prediction['predicted_buy_qty'])} {prediction['predicted_unit']}".strip(),
                "Confidence": prediction["confidence"],
                "Why": prediction["why"] or "Based on current stock and purchase history.",
            }
        )
    return rows
def has_sealed_stock(item):
    return any(lot.get("status") == "sealed" and lot.get("quantity", 0) > 0 for lot in active_lots(item))


def shopping_overrides(profile):
    return profile.get("shopping_preferences", {}).setdefault("suggestion_overrides", {})


def update_shopping_override(profile, suggestion_id, **updates):
    overrides = shopping_overrides(profile)
    current = dict(overrides.get(suggestion_id, {}))
    current.update({key: value for key, value in updates.items() if value is not None})
    overrides[suggestion_id] = current


def clear_shopping_override(profile, suggestion_id, *keys):
    overrides = shopping_overrides(profile)
    current = dict(overrides.get(suggestion_id, {}))
    for key in keys:
        current.pop(key, None)
    if current:
        overrides[suggestion_id] = current
    else:
        overrides.pop(suggestion_id, None)


def should_hide_suggestion(profile, suggestion_id):
    state = shopping_overrides(profile).get(suggestion_id, {})
    if state.get("removed"):
        return True
    if state.get("skipped_on") == today_iso():
        return True
    snooze_until = state.get("snooze_until", "")
    if snooze_until and snooze_until >= today_iso():
        return True
    return False


def suggestion_confidence(reasons):
    keys = {reason["key"] for reason in reasons}
    if "below_refill" in keys and "avg_interval" in keys:
        return "High"
    if "below_refill" in keys or "run_out_soon" in keys:
        return "High"
    if "avg_interval" in keys:
        return "Medium"
    return "Low"


def build_suggestion_reason(key, detail):
    return {"key": key, "label": SHOPPING_REASON_LABELS[key], "detail": detail}


def estimate_suggestion_price(item, suggested_quantity):
    history = purchase_history_for_item(item)
    if not history:
        return None
    last = history[0]
    last_qty = last.get("quantity") or 0.0
    last_price = last.get("price")
    if last_price is None or last_qty <= 0:
        return last_price
    return round((last_price / last_qty) * suggested_quantity, 2)


def build_inventory_shopping_suggestion(profile, item):
    current = inventory_total_quantity(item)
    refill = item.get("refill_level")
    capacity = item.get("storage_capacity")
    preferred_qty = item.get("preferred_purchase_quantity")
    preferred_unit = item.get("preferred_purchase_unit", "") or item.get("unit", "")
    interval_days = average_purchase_interval_days(item)
    last_purchase = latest_purchase_date(item)
    prediction = item_prediction_summary(profile, item)
    waste_rows = waste_transactions_for_item(profile, item)
    days_since = None
    if last_purchase:
        try:
            days_since = (date.today() - date.fromisoformat(last_purchase)).days
        except ValueError:
            days_since = None

    reasons = []
    if refill is not None and current <= refill:
        reasons.append(build_suggestion_reason("below_refill", f"Current stock is {format_number(current)} {item.get('unit', '')} against refill level {format_number(refill)}."))
    if current > 0 and not has_sealed_stock(item) and ((refill is not None and current <= max(refill * 1.25, 1)) or current <= 1):
        reasons.append(build_suggestion_reason("run_out_soon", "Only open or low working stock is left."))
    if interval_days and days_since is not None and days_since >= interval_days:
        reasons.append(build_suggestion_reason("avg_interval", f"Last bought {days_since} days ago, around the usual {interval_days}-day interval."))
    if is_home_supply_item(profile, item) and refill is not None and current <= refill:
        reasons.append(build_suggestion_reason("home_supply_low", "Home supplies stock is nearing its refill point."))
    if not reasons:
        return None

    needed_qty = max((refill - current), 0.0) if refill is not None else 0.0
    suggested_qty = preferred_qty or needed_qty or 0.0
    if preferred_qty and needed_qty > 0:
        suggested_qty = max(preferred_qty, needed_qty)
    if suggested_qty <= 0 and preferred_qty:
        suggested_qty = preferred_qty
    if prediction.get("predicted_buy_qty"):
        suggested_qty = max(suggested_qty, prediction["predicted_buy_qty"])
    if suggested_qty <= 0:
        return None

    capacity_warning = ""
    if capacity is not None:
        remaining_capacity = max(capacity - current, 0.0)
        if remaining_capacity <= 0:
            capacity_warning = "May exceed storage capacity."
            suggested_qty = min(suggested_qty, preferred_qty or suggested_qty)
        elif suggested_qty > remaining_capacity:
            suggested_qty = remaining_capacity
            capacity_warning = "May exceed storage capacity."
    if suggested_qty <= 0:
        return None

    suggestion_id = f"inventory::{item['id']}"
    state = shopping_overrides(profile).get(suggestion_id, {})
    vendor_name = state.get("vendor_name") or item.get("preferred_vendor") or default_vendor_name_for_category(profile, item.get("category_id", ""))
    quantity_value = try_float(state.get("quantity_override"))
    final_qty = quantity_value if quantity_value is not None else round(suggested_qty, 2)
    unit_value = state.get("unit_override") or preferred_unit or item.get("unit", "")
    price_summary = price_summary_for_item(item)
    seasonal_note = ""
    season = current_season_label()
    lowered_name = item.get("name", "").lower()
    if any(name in lowered_name for name in SEASONAL_ITEMS.get(season, [])):
        seasonal_note = f"{item['name']} is seasonal in {season.lower()}."
    waste_note = "Past waste suggests buying a smaller quantity." if waste_rows else ""
    return {
        "id": suggestion_id,
        "source": "inventory",
        "item_id": item["id"],
        "item_name": item["name"],
        "vendor_name": vendor_name,
        "brand": item.get("preferred_brand", ""),
        "quantity": final_qty,
        "unit": unit_value,
        "base_unit": item.get("unit", ""),
        "reason_details": reasons,
        "reason_summary": ", ".join(reason["label"] for reason in reasons),
        "confidence": prediction.get("confidence") or suggestion_confidence(reasons),
        "last_price": price_summary.get("last_price"),
        "estimated_price": estimate_suggestion_price(item, final_qty),
        "capacity_warning": capacity_warning or prediction.get("capacity_note", ""),
        "why": {
            "current_quantity": current,
            "refill_level": refill,
            "storage_capacity": capacity,
            "preferred_purchase_quantity": preferred_qty,
            "preferred_purchase_unit": preferred_unit,
            "average_purchase_interval_days": interval_days,
            "last_purchase_date": last_purchase,
            "predicted_refill_days": prediction.get("days_until_refill"),
            "prediction_why": prediction.get("why", ""),
            "waste_note": waste_note,
            "seasonal_note": seasonal_note,
        },
    }


def build_manual_shopping_suggestion(profile, manual_item):
    suggestion_id = f"manual::{manual_item['id']}"
    state = shopping_overrides(profile).get(suggestion_id, {})
    quantity_value = try_float(state.get("quantity_override"))
    return {
        "id": suggestion_id,
        "source": "manual",
        "item_id": "",
        "manual_id": manual_item["id"],
        "item_name": manual_item["item_name"],
        "vendor_name": state.get("vendor_name") or manual_item.get("vendor_name", "Other"),
        "brand": manual_item.get("brand", ""),
        "quantity": quantity_value if quantity_value is not None else manual_item.get("quantity", 1.0),
        "unit": state.get("unit_override") or manual_item.get("unit", ""),
        "base_unit": manual_item.get("unit", ""),
        "reason_details": [build_suggestion_reason("manual", manual_item.get("notes", "") or "Added manually to the shopping list.")],
        "reason_summary": SHOPPING_REASON_LABELS["manual"],
        "confidence": "Low",
        "last_price": None,
        "estimated_price": None,
        "capacity_warning": "",
        "why": {"notes": manual_item.get("notes", "")},
    }


def build_shopping_suggestions(profile):
    suggestions = []
    for item in profile.get("inventory", []):
        suggestion = build_inventory_shopping_suggestion(profile, item)
        if suggestion and not should_hide_suggestion(profile, suggestion["id"]):
            suggestions.append(suggestion)
    for manual_item in profile.get("shopping_manual_items", []):
        if manual_item.get("status") != "active":
            continue
        suggestion = build_manual_shopping_suggestion(profile, manual_item)
        if not should_hide_suggestion(profile, suggestion["id"]):
            suggestions.append(suggestion)
    suggestions.sort(key=lambda item: (item["vendor_name"], item["item_name"]))
    return suggestions


def suggestion_groups_by_vendor(profile):
    grouped = OrderedDict()
    for vendor in [item["name"] for item in profile.get("vendors", [])]:
        grouped[vendor] = []
    for suggestion in build_shopping_suggestions(profile):
        grouped.setdefault(suggestion["vendor_name"], []).append(suggestion)
    return OrderedDict((key, value) for key, value in grouped.items() if value)


def mark_suggestion_purchased(profile, suggestion, quantity, unit, vendor_name, brand, price, purchase_date, lot_status, notes):
    item = None
    if suggestion["source"] == "inventory":
        item = inventory_item_lookup(profile).get(suggestion["item_id"])
    if not item:
        category_id = slugify_name("Other Kitchen")
        if suggestion["source"] == "manual":
            category_id = slugify_name("Other Kitchen")
        item = build_new_item(suggestion["item_name"], quantity, category_id, unit)
        item["lots"] = []
    lot = normalize_inventory_lot(
        {
            "quantity": quantity,
            "unit": unit,
            "status": lot_status,
            "purchase_date": purchase_date,
            "vendor": vendor_name,
            "brand": brand,
            "price": price,
            "notes": notes,
        },
        item,
    )
    item["name"] = suggestion["item_name"]
    item["preferred_vendor"] = vendor_name
    item["preferred_brand"] = brand
    item["preferred_purchase_quantity"] = quantity
    item["preferred_purchase_unit"] = unit
    item["purchase_date"] = purchase_date
    item["unit"] = item.get("unit") or unit
    item["lots"] = [lot, *item.get("lots", [])]
    save_inventory_item(profile, item)
    add_inventory_transaction_with_source(profile, item, quantity, "Add", "purchase", notes, source="shopping")
    clear_shopping_override(profile, suggestion["id"], "quantity_override", "unit_override", "vendor_name", "skipped_on", "snooze_until", "removed")
    if suggestion["source"] == "manual":
        for manual_item in profile.get("shopping_manual_items", []):
            if manual_item["id"] == suggestion["manual_id"]:
                manual_item["status"] = "purchased"
    return item


def deduct_from_item(item, amount):
    remaining = amount
    lots = []
    sorted_lots = sorted(item.get("lots", []), key=lambda lot: (lot.get("status") != "opened", lot.get("purchase_date", "")))
    for lot in sorted_lots:
        updated = dict(lot)
        if updated.get("status") in {"finished", "expired"}:
            lots.append(updated)
            continue
        available = updated.get("quantity", 0.0)
        if remaining > 0 and available > 0:
            used = min(available, remaining)
            updated["quantity"] = round(available - used, 2)
            remaining = round(remaining - used, 2)
            if updated["quantity"] <= 0:
                updated["quantity"] = 0.0
                updated["status"] = "finished"
        lots.append(updated)
    item["lots"] = lots
    return round(amount - remaining, 2)


def set_exact_item_quantity(item, target_quantity):
    current = inventory_total_quantity(item)
    if target_quantity > current:
        item["lots"] = [
            normalize_inventory_lot(
                {
                    "quantity": round(target_quantity - current, 2),
                    "unit": item.get("unit", "unit"),
                    "status": "opened",
                    "purchase_date": today_iso(),
                    "location_id": item.get("location_id", ""),
                },
                item,
            ),
            *item.get("lots", []),
        ]
        return round(target_quantity - current, 2)
    removed = deduct_from_item(item, round(current - target_quantity, 2))
    return -removed


def mark_item_status(item, new_status):
    lots = []
    for lot in item.get("lots", []):
        updated = dict(lot)
        if updated.get("status") not in {"finished", "expired"}:
            updated["status"] = new_status
            if new_status in {"finished", "expired"}:
                updated["quantity"] = 0.0
        lots.append(updated)
    item["lots"] = lots


def inventory_overview(profile, items=None):
    items = items if items is not None else profile.get("inventory", [])
    expiring = []
    low_stock = []
    open_items = 0
    over_capacity = 0
    for item in items:
        if any(lot.get("status") == "opened" for lot in active_lots(item)):
            open_items += 1
        if item_over_capacity(item):
            over_capacity += 1
        if item_low_stock(item):
            low_stock.append(item)
        for lot in active_lots(item):
            expiry_value = item_expiry_date(profile, item, lot)
            days = days_to_expiry(expiry_value)
            if days is not None and days <= 7:
                expiring.append((days, item, lot, expiry_value))
    expiring.sort(key=lambda item: item[0])
    low_stock.sort(key=lambda item: inventory_total_quantity(item))
    return {
        "low_stock": low_stock,
        "expiring": expiring,
        "open_items": open_items,
        "over_capacity": over_capacity,
    }


def render_setup_panel(profile):
    setup_complete = profile.get("preferences", {}).get("setup_complete", False)
    expanded = st.session_state.pop("force_open_setup", False) or not setup_complete
    st.markdown("<div id='setup-section'></div>", unsafe_allow_html=True)
    with st.expander("Setup", expanded=expanded):
        st.markdown("**Set up a few basics to make inventory useful right away.**")
        st.caption("1. Choose categories used at home  2. Add current stock quickly  3. Add storage locations  4. Add vendors")
        setup_tabs = st.tabs(["Household Setup", "Members", "Routines", "Goals", "Vendors", "Storage Locations", "Inventory Defaults", "Home Supplies Defaults", "Categories", "Item Aliases"])

        with setup_tabs[0]:
            used_categories = st.multiselect(
                "Choose categories used at home",
                [item["name"] for item in profile.get("inventory_categories", [])],
                default=profile.get("preferences", {}).get("used_categories", []),
                key=f"used_categories_{profile['id']}",
            )
            quick_rows = [
                {"Item": item["name"], "Qty": format_number(inventory_total_quantity(item)), "Category": category_name(profile, item.get("category_id", ""))}
                for item in profile.get("inventory", [])[:8]
            ]
            if quick_rows:
                st.dataframe(pd.DataFrame(quick_rows), use_container_width=True, hide_index=True)
            quick1, quick2 = st.columns(2)
            if quick1.button("Add current stock quickly", use_container_width=True, key=f"setup_quick_stock_{profile['id']}"):
                st.session_state.pending_workspace = "Inventory"
                st.session_state.inventory_section = "Items"
                st.session_state.inventory_quick_action = "add_item"
                st.rerun()
            if quick2.button("Skip for now", use_container_width=True, key=f"setup_skip_{profile['id']}"):
                profile["preferences"]["used_categories"] = used_categories
                persist_active_profile(profile)
                st.rerun()
            if st.button("Save setup basics", use_container_width=True, key=f"setup_save_basics_{profile['id']}"):
                profile["preferences"]["used_categories"] = used_categories
                profile["preferences"]["setup_complete"] = bool(profile.get("household_members"))
                persist_active_profile(profile)
                st.rerun()

        with setup_tabs[1]:
            render_household_manager(profile, key_scope="setup")

        with setup_tabs[2]:
            with st.form(f"setup_routines_{profile['id']}"):
                before_didi = st.text_area("Before cook arrives", value=profile.get("preferences", {}).get("before_didi_arrives", ""), height=120)
                morning_routine = st.text_area("Morning routine", value=profile.get("preferences", {}).get("morning_routine", ""), height=120)
                save_routines = st.form_submit_button("Save routines")
            if save_routines:
                profile["preferences"]["before_didi_arrives"] = before_didi.strip()
                profile["preferences"]["morning_routine"] = morning_routine.strip()
                persist_active_profile(profile)
                st.rerun()

        with setup_tabs[3]:
            with st.form(f"setup_goals_{profile['id']}"):
                activity_level = st.selectbox("Activity level", ["Low activity", "Moderately active", "Active"], index=["Low activity", "Moderately active", "Active"].index(profile.get("preferences", {}).get("activity_level", "Moderately active")))
                meal_mode = st.selectbox("Goal / meal mode", ["Normal eating", "Weight maintenance", "Higher protein intake"], index=["Normal eating", "Weight maintenance", "Higher protein intake"].index(profile.get("preferences", {}).get("meal_mode", "Normal eating")))
                save_goals = st.form_submit_button("Save goals")
            if save_goals:
                profile["preferences"]["activity_level"] = activity_level
                profile["preferences"]["meal_mode"] = meal_mode
                persist_active_profile(profile)
                st.rerun()

        with setup_tabs[4]:
            vendor_names = [vendor["name"] for vendor in profile.get("vendors", [])]
            st.write(", ".join(vendor_names) if vendor_names else "No vendors yet.")
            selected_vendor_id = st.selectbox("Vendor", [""] + [vendor["id"] for vendor in profile.get("vendors", [])], format_func=lambda value: next((vendor["name"] for vendor in profile.get("vendors", []) if vendor["id"] == value), "Add vendor"), key=f"setup_vendor_select_{profile['id']}")
            selected_vendor = next((vendor for vendor in profile.get("vendors", []) if vendor["id"] == selected_vendor_id), None)
            with st.form(f"setup_vendor_form_{profile['id']}"):
                vendor_name = st.text_input("Vendor name", value=selected_vendor.get("name", "") if selected_vendor else "")
                vendor_type = st.selectbox("Vendor type", ["Grocery app", "Local vegetable vendor", "Kirana", "Pharmacy", "Marketplace", "Dairy", "Other"], index=["Grocery app", "Local vegetable vendor", "Kirana", "Pharmacy", "Marketplace", "Dairy", "Other"].index(selected_vendor.get("vendor_type", "Other") if selected_vendor else "Other"))
                preferred_categories = st.multiselect("Preferred categories", [item["name"] for item in profile.get("inventory_categories", [])], default=selected_vendor.get("preferred_categories", []) if selected_vendor else [])
                notes = st.text_input("Notes", value=selected_vendor.get("notes", "") if selected_vendor else "")
                save_vendor = st.form_submit_button("Save vendor")
            if save_vendor and vendor_name.strip():
                vendor = normalize_vendor_record({"id": selected_vendor["id"] if selected_vendor else uuid4().hex, "name": vendor_name.strip(), "vendor_type": vendor_type, "preferred_categories": preferred_categories, "notes": notes.strip()})
                profile["vendors"] = [item for item in profile.get("vendors", []) if item["id"] != vendor["id"]] + [vendor]
                persist_active_profile(profile)
                st.rerun()
            if selected_vendor and st.button("Delete vendor", key=f"delete_vendor_{selected_vendor['id']}", use_container_width=True):
                st.session_state[f"confirm_delete_vendor_{selected_vendor['id']}"] = True
                st.rerun()
            if selected_vendor and st.session_state.get(f"confirm_delete_vendor_{selected_vendor['id']}"):
                linked = any(item.get("preferred_vendor") == selected_vendor["name"] for item in profile.get("inventory", []))
                st.warning("Delete this vendor? Linked items will keep their history but should be reassigned first." if linked else "Delete this vendor?")
                confirm_col, cancel_col = st.columns(2)
                if confirm_col.button("Confirm delete", key=f"confirm_delete_vendor_btn_{selected_vendor['id']}", type="primary", use_container_width=True):
                    if not linked:
                        profile["vendors"] = [item for item in profile.get("vendors", []) if item["id"] != selected_vendor["id"]]
                        persist_active_profile(profile)
                    st.session_state.pop(f"confirm_delete_vendor_{selected_vendor['id']}", None)
                    st.rerun()
                if cancel_col.button("Cancel", key=f"cancel_delete_vendor_btn_{selected_vendor['id']}", use_container_width=True):
                    st.session_state.pop(f"confirm_delete_vendor_{selected_vendor['id']}", None)
                    st.rerun()

        with setup_tabs[5]:
            selected_location_id = st.selectbox("Storage location", [""] + [location["id"] for location in profile.get("storage_locations", [])], format_func=lambda value: next((location["name"] for location in profile.get("storage_locations", []) if location["id"] == value), "Add location"), key=f"setup_location_select_{profile['id']}")
            selected_location = next((location for location in profile.get("storage_locations", []) if location["id"] == selected_location_id), None)
            with st.form(f"setup_location_form_{profile['id']}"):
                location_name = st.text_input("Location name", value=selected_location.get("name", "") if selected_location else "")
                capacity_value = st.number_input("Capacity", min_value=0.0, step=0.25, value=float(selected_location.get("capacity_value", 0.0) if selected_location and selected_location.get("capacity_value") is not None else 0.0))
                capacity_unit = st.text_input("Capacity unit", value=selected_location.get("capacity_unit", "") if selected_location else "")
                notes = st.text_input("Notes", value=selected_location.get("notes", "") if selected_location else "")
                save_location = st.form_submit_button("Save location")
            if save_location and location_name.strip():
                location = normalize_storage_location({"id": selected_location["id"] if selected_location else uuid4().hex, "name": location_name.strip(), "capacity_value": capacity_value or None, "capacity_unit": capacity_unit.strip(), "notes": notes.strip()})
                profile["storage_locations"] = [item for item in profile.get("storage_locations", []) if item["id"] != location["id"]] + [location]
                persist_active_profile(profile)
                st.rerun()
            if selected_location and st.button("Delete location", key=f"delete_location_{selected_location['id']}", use_container_width=True):
                st.session_state[f"confirm_delete_location_{selected_location['id']}"] = True
                st.rerun()
            if selected_location and st.session_state.get(f"confirm_delete_location_{selected_location['id']}"):
                linked = any(item.get("location_id") == selected_location["id"] for item in profile.get("inventory", []))
                st.warning("Delete this location? Linked items should be moved first." if linked else "Delete this location?")
                confirm_col, cancel_col = st.columns(2)
                if confirm_col.button("Confirm delete", key=f"confirm_delete_location_btn_{selected_location['id']}", type="primary", use_container_width=True):
                    if not linked:
                        profile["storage_locations"] = [item for item in profile.get("storage_locations", []) if item["id"] != selected_location["id"]]
                        persist_active_profile(profile)
                    st.session_state.pop(f"confirm_delete_location_{selected_location['id']}", None)
                    st.rerun()
                if cancel_col.button("Cancel", key=f"cancel_delete_location_btn_{selected_location['id']}", use_container_width=True):
                    st.session_state.pop(f"confirm_delete_location_{selected_location['id']}", None)
                    st.rerun()

        def render_category_defaults(filter_home_supplies, form_key):
            categories = [item for item in profile.get("inventory_categories", []) if is_home_supply_category_name(item["name"]) == filter_home_supplies]
            selected_category_id = st.selectbox("Category", [item["id"] for item in categories], format_func=lambda value: category_name(profile, value), key=f"{form_key}_select")
            selected_category = inventory_category_lookup(profile).get(selected_category_id)
            with st.form(f"{form_key}_form"):
                default_unit = st.text_input("Default unit", value=selected_category.get("default_unit", "unit"))
                default_refill_level = st.number_input("Default refill level", min_value=0.0, step=0.25, value=float(selected_category.get("default_refill_level") or 0.0))
                default_location_name = st.text_input("Default storage location", value=selected_category.get("default_location_name", ""))
                default_vendor_name = st.text_input("Default preferred vendor", value=selected_category.get("default_vendor_name", ""))
                approx_tracking_mode = st.text_input("Default approximate tracking mode", value=selected_category.get("approx_tracking_mode", "general"))
                exact_tracking_mode = st.text_input("Default exact tracking mode", value=selected_category.get("exact_tracking_mode", "quantity"))
                shelf_life_days = st.number_input("Default shelf life (days)", min_value=0, step=1, value=int(selected_category.get("shelf_life_days") or 0))
                save_category_defaults = st.form_submit_button("Save defaults")
            if save_category_defaults:
                updated_category = normalize_inventory_category({**selected_category, "default_unit": default_unit.strip() or "unit", "default_refill_level": default_refill_level or None, "default_location_name": default_location_name.strip(), "default_vendor_name": default_vendor_name.strip(), "approx_tracking_mode": approx_tracking_mode.strip(), "exact_tracking_mode": exact_tracking_mode.strip(), "shelf_life_days": shelf_life_days})
                profile["inventory_categories"] = [item for item in profile.get("inventory_categories", []) if item["id"] != updated_category["id"]] + [updated_category]
                persist_active_profile(profile)
                st.rerun()

        with setup_tabs[6]:
            render_category_defaults(False, f"inventory_defaults_{profile['id']}")

        with setup_tabs[7]:
            render_category_defaults(True, f"home_defaults_{profile['id']}")

        with setup_tabs[8]:
            with st.form(f"setup_category_form_{profile['id']}"):
                category_title = st.text_input("Category name")
                category_shelf_life = st.number_input("Shelf life (days)", min_value=1, step=1, value=30)
                save_category = st.form_submit_button("Add category")
            if save_category and category_title.strip():
                category = normalize_inventory_category({"name": category_title.strip(), "shelf_life_days": category_shelf_life})
                profile["inventory_categories"] = [entry for entry in profile.get("inventory_categories", []) if entry["id"] != category["id"]] + [category]
                persist_active_profile(profile)
                st.rerun()

        with setup_tabs[9]:
            items_with_aliases = [item for item in profile.get("inventory", []) if not item.get("archived")]
            alias_options = {"Add aliases later": ""}
            for item in items_with_aliases:
                alias_options[item["name"]] = item["id"]
            selected_item_id = st.selectbox("Item", list(alias_options.values()), format_func=lambda value: next(label for label, item_id in alias_options.items() if item_id == value), key=f"alias_item_select_{profile['id']}")
            selected_item = inventory_item_lookup(profile).get(selected_item_id)
            if selected_item:
                with st.form(f"alias_form_{profile['id']}"):
                    alias_text = st.text_area("Aliases", value=", ".join(selected_item.get("aliases", [])), height=100, placeholder="atta, flour, chawal, rice")
                    save_aliases = st.form_submit_button("Save aliases")
                if save_aliases:
                    selected_item["aliases"] = [part.strip() for part in re.split(r"[\n,]+", alias_text) if part.strip()]
                    save_inventory_item(profile, selected_item)
                    persist_active_profile(profile)
                    st.rerun()


def render_setup_workspace(profile):
    st.markdown("**Setup**")
    render_setup_panel(profile)


def inventory_category_options(profile):
    categories = profile.get("inventory_categories", [])
    return {category["name"]: category["id"] for category in categories}


def render_inventory_quick_add(profile, form_key, add_purchase=False, category_ids=None):
    categories = [item for item in profile.get("inventory_categories", []) if category_ids is None or item["id"] in category_ids]
    default_category_id = categories[0]["id"] if categories else slugify_name("Other Kitchen")
    default_category = category_defaults_for_id(profile, default_category_id)
    with st.form(form_key):
        item_name = st.text_input("Item name", key=f"{form_key}_name")
        quantity = st.number_input("Quantity", min_value=0.0, step=0.25, value=1.0, key=f"{form_key}_quantity")
        category_id = st.selectbox(
            "Category",
            [item["id"] for item in categories],
            format_func=lambda item: category_name(profile, item),
            index=0,
            key=f"{form_key}_category",
        ) if categories else default_category_id
        selected_defaults = category_defaults_for_id(profile, category_id)
        unit = st.text_input("Unit", value=selected_defaults.get("default_unit", default_category.get("default_unit", "unit")) or "unit", key=f"{form_key}_unit")
        details = {}
        with st.expander("Optional details", expanded=add_purchase):
            details["preferred_vendor"] = st.text_input("Preferred vendor" if not add_purchase else "Vendor", value=selected_defaults.get("default_vendor_name", ""), key=f"{form_key}_vendor")
            details["preferred_brand"] = st.text_input("Preferred brand" if not add_purchase else "Brand", key=f"{form_key}_brand")
            details["location_id"] = st.selectbox(
                "Storage location",
                [item["id"] for item in profile.get("storage_locations", [])],
                format_func=lambda item: inventory_location_lookup(profile).get(item, {}).get("name", item),
                index=next((idx for idx, entry in enumerate(profile.get("storage_locations", [])) if entry["id"] == location_id_from_default_name(profile, selected_defaults.get("default_location_name", ""))), 0),
                key=f"{form_key}_location",
            ) if profile.get("storage_locations") else ""
            details["purchase_date"] = st.text_input("Purchase date", value=today_iso(), key=f"{form_key}_purchase_date")
            details["expiry_date"] = st.text_input("Expiry / best before", value="", key=f"{form_key}_expiry_date")
            details["notes"] = st.text_area("Notes", height=80, key=f"{form_key}_notes")
            if add_purchase:
                details["price"] = st.number_input("Price", min_value=0.0, step=1.0, value=0.0, key=f"{form_key}_price")
                details["lot_status"] = st.selectbox("Lot status", ["sealed", "opened"], key=f"{form_key}_lot_status")
        save_label = "Add purchase" if add_purchase else "Add item"
        submitted = st.form_submit_button(save_label)
    if submitted:
        if not item_name.strip():
            st.error("Item name is required.")
            return
        existing = next((item for item in profile.get("inventory", []) if item["name"].strip().lower() == item_name.strip().lower()), None)
        if existing and add_purchase:
            new_lot = normalize_inventory_lot(
                {
                    "quantity": quantity,
                    "unit": unit,
                    "status": details.get("lot_status", "sealed"),
                    "purchase_date": details.get("purchase_date", today_iso()),
                    "expiry_date": details.get("expiry_date", ""),
                    "location_id": details.get("location_id", ""),
                    "vendor": details.get("preferred_vendor", ""),
                    "brand": details.get("preferred_brand", ""),
                    "price": details.get("price"),
                    "notes": details.get("notes", ""),
                },
                existing,
            )
            existing["lots"] = [new_lot, *existing.get("lots", [])]
            if details.get("location_id"):
                existing["location_id"] = details["location_id"]
            if details.get("preferred_vendor"):
                existing["preferred_vendor"] = details["preferred_vendor"]
            if details.get("preferred_brand"):
                existing["preferred_brand"] = details["preferred_brand"]
            save_inventory_item(profile, existing)
            add_inventory_transaction(profile, existing, quantity, "Add", "purchase", details.get("notes", ""))
        else:
            item = build_new_item(item_name.strip(), quantity, category_id, unit)
            item["preferred_vendor"] = details.get("preferred_vendor", "")
            item["preferred_brand"] = details.get("preferred_brand", "")
            item["location_id"] = details.get("location_id", "")
            item["notes"] = details.get("notes", "")
            item["refill_level"] = item.get("refill_level") or category_defaults_for_id(profile, category_id).get("default_refill_level")
            if details.get("expiry_date"):
                item["expiry_date"] = details["expiry_date"]
                item["lots"][0]["expiry_date"] = details["expiry_date"]
            save_inventory_item(profile, item)
            add_inventory_transaction(profile, item, quantity, "Add", "purchase" if add_purchase else "manual", details.get("notes", ""))
        persist_active_profile(profile)
        st.session_state.inventory_section = "Items"
        st.rerun()


def render_voice_capture_bridge(textarea_label):
    components.html(
        f"""
        <div style="margin:0.25rem 0 0.75rem;">
          <button id="voice-capture-btn" style="padding:0.65rem 1rem;border-radius:10px;border:1px solid #bbb;background:#fff;cursor:pointer;">
            Start Voice Capture
          </button>
          <div id="voice-status" style="font-size:0.9rem;margin-top:0.45rem;color:#555;"></div>
        </div>
        <script>
        const btn = document.getElementById("voice-capture-btn");
        const status = document.getElementById("voice-status");
        btn.onclick = () => {{
          const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!SR) {{
            status.textContent = "Speech recognition is not available here. Type or paste your transcript below.";
            return;
          }}
          const recognition = new SR();
          recognition.lang = "en-IN";
          recognition.interimResults = false;
          recognition.maxAlternatives = 1;
          status.textContent = "Listening...";
          recognition.onresult = (event) => {{
            const transcript = event.results[0][0].transcript;
            const parentDoc = window.parent.document;
            const area = [...parentDoc.querySelectorAll("textarea")].find((node) => node.getAttribute("aria-label") === {json.dumps(textarea_label)});
            if (area) {{
              area.value = transcript;
              area.dispatchEvent(new Event("input", {{ bubbles: true }}));
              status.textContent = "Voice captured. Review or edit the transcript below.";
            }} else {{
              status.textContent = transcript;
            }}
          }};
          recognition.onerror = () => {{
            status.textContent = "Could not capture voice. Type or paste your transcript below.";
          }};
          recognition.onend = () => {{
            if (status.textContent === "Listening...") {{
              status.textContent = "No speech captured. Type or paste your transcript below.";
            }}
          }};
          recognition.start();
        }};
        </script>
        """,
        height=96,
    )


def render_purchase_review(profile):
    review_items = get_purchase_review_items()
    changed = False
    if not review_items and not st.session_state.get("purchase_review_error"):
        return
    with st.container(border=True):
        st.markdown("**Review Purchases Before Updating Inventory**")
        if st.session_state.get("purchase_review_error") and not review_items:
            st.warning(st.session_state["purchase_review_error"])
            retry_col, edit_col, manual_col = st.columns(3)
            if retry_col.button("Try Again", use_container_width=True):
                st.rerun()
            if edit_col.button("Edit Text", use_container_width=True):
                st.session_state.inventory_quick_action = "add_purchase"
                st.rerun()
            if manual_col.button("Manual Entry", use_container_width=True):
                st.session_state.inventory_quick_action = "add_purchase"
                st.rerun()
            return
        categories = profile.get("inventory_categories", [])
        category_ids = [item["id"] for item in categories]
        vendor_names = [item["name"] for item in profile.get("vendors", [])]
        locations = [""] + [item["id"] for item in profile.get("storage_locations", [])]
        updated_items = []
        for review_item in review_items:
            if review_item.get("status") != "pending":
                updated_items.append(review_item)
                continue
            with st.container(border=True):
                st.markdown(f"**{review_item['detected_name']}**")
                badge_cols = st.columns(4)
                badge_cols[0].write(f"Match: {next((item['name'] for item in profile.get('inventory', []) if item['id'] == review_item.get('matched_item_id')), 'New item')}")
                badge_cols[1].write(f"Confidence: {review_item['confidence']}")
                badge_cols[2].write(f"Destination: {review_item['destination']}")
                badge_cols[3].write(f"Source: {review_item['parse_source'].title()}")
                with st.form(f"review_form_{review_item['id']}"):
                    row1 = st.columns(3)
                    item_name = row1[0].text_input("Item name", value=review_item["item_name"])
                    quantity = row1[1].number_input("Quantity", min_value=0.0, step=0.25, value=float(review_item["quantity"]))
                    unit = row1[2].text_input("Unit", value=review_item["unit"])
                    row2 = st.columns(3)
                    packet_format = row2[0].text_input("Packet format", value=review_item.get("packet_format", "") or review_item["unit"])
                    destination = row2[1].selectbox("Destination", ["Inventory", "Home Supplies"], index=["Inventory", "Home Supplies"].index(review_item.get("destination", "Inventory")))
                    category_id_default = home_supply_category_id_for_name(item_name) if destination == "Home Supplies" else review_item.get("category_id", category_ids[0] if category_ids else "")
                    category_id = row2[2].selectbox("Category", category_ids, index=category_ids.index(category_id_default) if category_id_default in category_ids else 0, format_func=lambda value: category_name(profile, value))
                    row3 = st.columns(4)
                    brand = row3[0].text_input("Brand", value=review_item.get("brand", ""))
                    vendor_name = row3[1].selectbox("Vendor", vendor_names, index=vendor_names.index(review_item.get("vendor_name", "Other")) if review_item.get("vendor_name", "Other") in vendor_names else 0)
                    price = row3[2].number_input("Price", min_value=0.0, step=1.0, value=float(review_item.get("price") or 0.0))
                    purchase_date = row3[3].text_input("Purchase date", value=review_item.get("purchase_date", today_iso()))
                    row4 = st.columns(2)
                    matched_options = [""] + [item["id"] for item in profile.get("inventory", [])]
                    matched_item_id = row4[0].selectbox("Matched inventory item", matched_options, index=matched_options.index(review_item.get("matched_item_id", "")) if review_item.get("matched_item_id", "") in matched_options else 0, format_func=lambda value: next((item["name"] for item in profile.get("inventory", []) if item["id"] == value), "Create new item") if value else "Create new item")
                    location_id = row4[1].selectbox("Location", locations, index=locations.index(review_item.get("location_id", "")) if review_item.get("location_id", "") in locations else 0, format_func=lambda value: inventory_location_lookup(profile).get(value, {}).get("name", "Not set") if value else "Not set")
                    notes = st.text_area("Notes", value=review_item.get("notes", ""), height=70)
                    confirm_col, ignore_col, create_col = st.columns(3)
                    confirm = confirm_col.form_submit_button("Confirm")
                    ignore = ignore_col.form_submit_button("Ignore")
                    create_new = create_col.form_submit_button("Create New Item")
                review_item.update(
                    {
                        "item_name": item_name.strip() or review_item["item_name"],
                        "quantity": quantity,
                        "unit": unit.strip() or "unit",
                        "packet_format": packet_format.strip(),
                        "destination": destination,
                        "category_id": home_supply_category_id_for_name(item_name) if destination == "Home Supplies" else category_id,
                        "brand": brand.strip(),
                        "vendor_name": vendor_name,
                        "price": price or None,
                        "purchase_date": purchase_date.strip() or today_iso(),
                        "matched_item_id": "" if create_new else matched_item_id,
                        "location_id": location_id,
                        "notes": notes.strip(),
                    }
                )
                if ignore:
                    review_item["status"] = "ignored"
                    changed = True
                elif confirm or create_new:
                    if create_new:
                        review_item["matched_item_id"] = ""
                    confirm_purchase_review_item(profile, review_item)
                    review_item["status"] = "confirmed"
                    changed = True
            updated_items.append(review_item)
        st.session_state.purchase_review_items = updated_items
        if changed:
            persist_active_profile(profile)
        pending = [item for item in updated_items if item.get("status") == "pending"]
        if pending:
            st.caption(f"{len(pending)} purchase item(s) still need review.")
        else:
            st.success("Reviewed purchases applied.")
            st.session_state.purchase_review_error = ""
            if st.button("Clear Review Queue", use_container_width=True):
                st.session_state.purchase_review_items = []
                st.rerun()


def render_purchase_intake(profile, form_key):
    mode_hint = st.session_state.pop("purchase_mode_hint", "")
    if mode_hint:
        st.caption(f"Quick action opened purchase entry. Suggested mode: {mode_hint}.")
    manual_tab, text_tab, voice_tab, invoice_tab = st.tabs(["Manual", "Text", "Voice", "Invoice Image"])
    with manual_tab:
        categories = profile.get("inventory_categories", [])
        category_ids = [item["id"] for item in categories]
        vendors = [item["name"] for item in profile.get("vendors", [])]
        locations = [""] + [item["id"] for item in profile.get("storage_locations", [])]
        with st.form(f"{form_key}_manual"):
            row1 = st.columns(4)
            item_name = row1[0].text_input("Item name")
            quantity = row1[1].number_input("Quantity", min_value=0.0, step=0.25, value=1.0)
            unit = row1[2].text_input("Unit", value="unit")
            packet_format = row1[3].text_input("Packet format", value="")
            row2 = st.columns(4)
            brand = row2[0].text_input("Brand")
            vendor = row2[1].selectbox("Vendor", vendors, index=vendors.index("Other") if "Other" in vendors else 0)
            price = row2[2].number_input("Price", min_value=0.0, step=1.0, value=0.0)
            purchase_date = row2[3].text_input("Purchase date", value=today_iso())
            row3 = st.columns(2)
            category_id = row3[0].selectbox("Category", category_ids, format_func=lambda value: category_name(profile, value))
            location_id = row3[1].selectbox("Location", locations, format_func=lambda value: inventory_location_lookup(profile).get(value, {}).get("name", "Not set") if value else "Not set")
            notes = st.text_area("Notes", height=70)
            manual_submit = st.form_submit_button("Send To Review")
        if manual_submit:
            set_purchase_review_items(
                [
                    normalize_purchase_review_item(
                        {
                            "detected_name": item_name.strip(),
                            "item_name": item_name.strip(),
                            "category_id": category_id,
                            "destination": "Home Supplies" if is_home_supply_category_name(category_name(profile, category_id)) else "Inventory",
                            "quantity": quantity,
                            "unit": unit.strip() or "unit",
                            "packet_format": packet_format.strip() or unit.strip() or "unit",
                            "brand": brand.strip(),
                            "vendor_name": vendor,
                            "price": price or None,
                            "purchase_date": purchase_date.strip() or today_iso(),
                            "location_id": location_id,
                            "confidence": "High",
                            "parse_source": "manual",
                            "notes": notes.strip(),
                        }
                    )
                ],
                source="manual",
            )
            st.rerun()
    with text_tab:
        text_value = st.text_area("Paste or type purchase update", height=130, key=f"{form_key}_text_value", placeholder="Bought 2kg tomato, 1kg onion, 10kg Aashirvaad atta, 2 packets makhana, and 1 Lizol from BigBasket.")
        if st.button("Parse Text", key=f"{form_key}_parse_text", use_container_width=True):
            items, error_message = parse_text_purchase_rows(profile, text_value)
            set_purchase_review_items(items, source="text", error_message=error_message)
            st.rerun()
    with voice_tab:
        st.caption("Use browser speech recognition if available. If not, dictate into your phone/keyboard mic and edit the transcript below.")
        render_voice_capture_bridge("Voice transcript")
        transcript = st.text_area("Voice transcript", height=130, key=f"{form_key}_voice_transcript", placeholder="Bought 2kg tomato and 1 bottle Lizol from BigBasket.")
        if st.button("Parse Voice Transcript", key=f"{form_key}_parse_voice", use_container_width=True):
            items, error_message = parse_text_purchase_rows(profile, transcript)
            for item in items:
                item["parse_source"] = "voice"
            set_purchase_review_items(items, source="voice", error_message=error_message)
            st.rerun()
    with invoice_tab:
        st.caption("Upload or capture the invoice, then optionally correct the detected text before review.")
        captured = st.camera_input("Capture invoice", key=f"{form_key}_camera")
        uploaded = st.file_uploader("Upload invoice image", type=["png", "jpg", "jpeg"], key=f"{form_key}_invoice_file")
        helper_text = st.text_area("Detected / corrected invoice text", height=130, key=f"{form_key}_invoice_text", placeholder="Paste OCR text here if available.")
        if st.button("Read Invoice", key=f"{form_key}_parse_invoice", use_container_width=True):
            image_obj = uploaded or captured
            items, error_message = parse_invoice_image_rows(profile, image_obj, helper_text)
            for item in items:
                item["parse_source"] = "invoice"
            set_purchase_review_items(items, source="invoice", error_message=error_message)
            st.rerun()
    render_purchase_review(profile)


def render_inventory_empty_state(profile, heading="Add your first inventory item or purchase to start tracking what is at home.", add_item_label="Add Item", add_purchase_label="Add Purchase", setup_label="Start with Sample Categories", key_prefix="inventory_empty", section_name="Items", quick_item_action="add_item", quick_purchase_action="add_purchase"):
    st.info(heading)
    col1, col2, col3 = st.columns(3)
    if col1.button(add_item_label, use_container_width=True, key=f"{key_prefix}_add_item"):
        st.session_state.inventory_section = section_name
        st.session_state.inventory_quick_action = quick_item_action
        st.rerun()
    if col2.button(add_purchase_label, use_container_width=True, key=f"{key_prefix}_add_purchase"):
        st.session_state.inventory_section = section_name
        st.session_state.inventory_quick_action = quick_purchase_action
        st.rerun()
    if col3.button(setup_label, use_container_width=True, key=f"{key_prefix}_defaults"):
        profile["inventory_categories"] = default_inventory_categories()
        profile["storage_locations"] = default_storage_locations()
        persist_active_profile(profile)
        st.rerun()


def render_inventory_item_editor(profile, item):
    categories = profile.get("inventory_categories", [])
    category_ids = [entry["id"] for entry in categories]
    locations = profile.get("storage_locations", [])
    location_ids = [""] + [entry["id"] for entry in locations]
    with st.form(f"inventory_detail_{item['id']}"):
        item_name = st.text_input("Item name", value=item.get("name", ""))
        category_id = st.selectbox(
            "Category",
            category_ids,
            index=category_ids.index(item.get("category_id", category_ids[0])) if item.get("category_id", "") in category_ids else 0,
            format_func=lambda value: category_name(profile, value),
        )
        st.text_input("Current total quantity", value=f"{format_number(inventory_total_quantity(item))} {item.get('unit', '')}".strip(), disabled=True)
        unit = st.text_input("Unit", value=item.get("unit", "unit"))
        approx_status = st.selectbox("Approx status", ["", "Full", "Half", "Low", "Finished"], index=["", "Full", "Half", "Low", "Finished"].index(item.get("approx_status", "")))
        refill_level = st.number_input("Refill level", min_value=0.0, step=0.25, value=float(item.get("refill_level") or 0.0))
        storage_capacity = st.number_input("Storage capacity", min_value=0.0, step=0.25, value=float(item.get("storage_capacity") or 0.0))
        shelf_life_days = st.number_input("Shelf life (days)", min_value=0, step=1, value=int(item.get("shelf_life_days") or 0))
        purchase_date = st.text_input("Purchase date", value=item.get("purchase_date", ""))
        opened_date = st.text_input("Open date", value=item.get("opened_date", ""))
        expiry_date = st.text_input("Expiry / best-before estimate", value=item.get("expiry_date", ""))
        location_id = st.selectbox(
            "Storage location",
            location_ids,
            index=location_ids.index(item.get("location_id", "")) if item.get("location_id", "") in location_ids else 0,
            format_func=lambda value: inventory_location_lookup(profile).get(value, {}).get("name", "Not set") if value else "Not set",
        )
        preferred_vendor = st.text_input("Preferred vendor", value=item.get("preferred_vendor", ""))
        preferred_brand = st.text_input("Preferred brand", value=item.get("preferred_brand", ""))
        preferred_purchase_quantity = st.number_input("Preferred purchase quantity", min_value=0.0, step=0.25, value=float(item.get("preferred_purchase_quantity") or 0.0))
        preferred_purchase_unit = st.text_input("Preferred purchase unit", value=item.get("preferred_purchase_unit", ""))
        aliases_text = st.text_area("Aliases", value=", ".join(item.get("aliases", [])), height=70, placeholder="atta, flour, aashirvaad atta")
        notes = st.text_area("Notes", value=item.get("notes", ""), height=100)
        save_item = st.form_submit_button("Save item details")
    if save_item:
        item.update(
            {
                "name": item_name.strip() or item["name"],
                "category_id": category_id,
                "unit": unit.strip() or "unit",
                "approx_status": approx_status,
                "refill_level": refill_level or None,
                "storage_capacity": storage_capacity or None,
                "shelf_life_days": shelf_life_days,
                "purchase_date": purchase_date.strip(),
                "opened_date": opened_date.strip(),
                "expiry_date": expiry_date.strip(),
                "location_id": location_id,
                "preferred_vendor": preferred_vendor.strip(),
                "preferred_brand": preferred_brand.strip(),
                "preferred_purchase_quantity": preferred_purchase_quantity or None,
                "preferred_purchase_unit": preferred_purchase_unit.strip(),
                "aliases": [part.strip() for part in re.split(r"[\n,]+", aliases_text) if part.strip()],
                "notes": notes.strip(),
            }
        )
        save_inventory_item(profile, item)
        persist_active_profile(profile)
        st.success("Item details updated.")
        st.rerun()
    delete_key = f"confirm_archive_item_{item['id']}"
    has_history = bool(inventory_transactions_for_item(profile, item))
    action_col1, action_col2 = st.columns(2)
    action_label = "Archive item" if has_history else "Delete item"
    if action_col1.button(action_label, key=f"archive_item_btn_{item['id']}", use_container_width=True):
        st.session_state[delete_key] = True
        st.rerun()
    if st.session_state.get(delete_key):
        st.warning(f"{action_label} for {item['name']}? This will keep history safe.")
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("Confirm", key=f"confirm_archive_item_btn_{item['id']}", type="primary", use_container_width=True):
            if has_history:
                item["archived"] = True
                save_inventory_item(profile, item)
            else:
                profile["inventory"] = [entry for entry in profile.get("inventory", []) if entry["id"] != item["id"]]
            st.session_state.pop(delete_key, None)
            persist_active_profile(profile)
            st.rerun()
        if cancel_col.button("Cancel", key=f"cancel_archive_item_btn_{item['id']}", use_container_width=True):
            st.session_state.pop(delete_key, None)
            st.rerun()


def render_inventory_lots(profile, item):
    lots = item.get("lots", [])
    if lots:
        lot_rows = []
        for lot in lots:
            lot_rows.append(
                {
                    "Quantity": format_number(lot.get("quantity", 0)),
                    "Unit": lot.get("unit", ""),
                    "Status": lot.get("status", ""),
                    "Purchase date": lot.get("purchase_date", ""),
                    "Opened date": lot.get("opened_date", ""),
                    "Expiry": item_expiry_date(profile, item, lot),
                    "Location": inventory_location_lookup(profile).get(lot.get("location_id", ""), {}).get("name", ""),
                    "Vendor": lot.get("vendor", ""),
                    "Brand": lot.get("brand", ""),
                    "Price": format_number(lot.get("price")),
                }
            )
        st.dataframe(pd.DataFrame(lot_rows), use_container_width=True, hide_index=True)
    else:
        st.write("No lots yet.")

    lot_options = {"Add new lot": ""}
    for lot in lots:
        label = f"{format_number(lot.get('quantity', 0))} {lot.get('unit', '')} | {lot.get('status', '')} | {lot.get('purchase_date', '')}"
        lot_options[label] = lot["id"]
    selected_lot_id = st.selectbox("Lot / packet", list(lot_options.values()), format_func=lambda value: next(label for label, lot_id in lot_options.items() if lot_id == value), key=f"lot_editor_{item['id']}")
    selected_lot = next((lot for lot in lots if lot["id"] == selected_lot_id), None)
    location_ids = [""] + [entry["id"] for entry in profile.get("storage_locations", [])]
    with st.form(f"inventory_lot_form_{item['id']}"):
        quantity = st.number_input("Quantity", min_value=0.0, step=0.25, value=float(selected_lot.get("quantity", 0.0) if selected_lot else 1.0))
        unit = st.text_input("Unit", value=selected_lot.get("unit", item.get("unit", "unit")) if selected_lot else item.get("unit", "unit"))
        status = st.selectbox("Status", ["sealed", "opened", "finished", "expired"], index=["sealed", "opened", "finished", "expired"].index(selected_lot.get("status", "sealed") if selected_lot else "sealed"))
        purchase_date = st.text_input("Purchase date", value=selected_lot.get("purchase_date", today_iso()) if selected_lot else today_iso())
        opened_date = st.text_input("Opened date", value=selected_lot.get("opened_date", "") if selected_lot else "")
        expiry_date = st.text_input("Expiry estimate", value=selected_lot.get("expiry_date", "") if selected_lot else "")
        location_id = st.selectbox(
            "Location",
            location_ids,
            index=location_ids.index(selected_lot.get("location_id", "") if selected_lot else item.get("location_id", "")) if (selected_lot.get("location_id", "") if selected_lot else item.get("location_id", "")) in location_ids else 0,
            format_func=lambda value: inventory_location_lookup(profile).get(value, {}).get("name", "Not set") if value else "Not set",
        )
        vendor = st.text_input("Vendor", value=selected_lot.get("vendor", "") if selected_lot else item.get("preferred_vendor", ""))
        brand = st.text_input("Brand", value=selected_lot.get("brand", "") if selected_lot else item.get("preferred_brand", ""))
        price = st.number_input("Price", min_value=0.0, step=1.0, value=float(selected_lot.get("price", 0.0) if selected_lot and selected_lot.get("price") is not None else 0.0))
        notes = st.text_input("Notes", value=selected_lot.get("notes", "") if selected_lot else "")
        save_lot = st.form_submit_button("Save lot")
        delete_lot = st.form_submit_button("Delete lot") if selected_lot else False
    if save_lot:
        lot = normalize_inventory_lot(
            {
                "id": selected_lot["id"] if selected_lot else uuid4().hex,
                "quantity": quantity,
                "unit": unit,
                "status": status,
                "purchase_date": purchase_date.strip(),
                "opened_date": opened_date.strip(),
                "expiry_date": expiry_date.strip(),
                "location_id": location_id,
                "vendor": vendor.strip(),
                "brand": brand.strip(),
                "price": price or None,
                "notes": notes.strip(),
            },
            item,
        )
        item["lots"] = [entry for entry in lots if entry["id"] != lot["id"]] + [lot]
        save_inventory_item(profile, item)
        persist_active_profile(profile)
        st.rerun()
    if delete_lot and selected_lot:
        item["lots"] = [entry for entry in lots if entry["id"] != selected_lot["id"]]
        save_inventory_item(profile, item)
        persist_active_profile(profile)
        st.rerun()


def render_item_purchase_history(item):
    summary = price_summary_for_item(item)
    history = purchase_history_for_item(item)
    st.markdown("**Price snapshot**")
    col1, col2, col3, col4, col5 = st.columns(5)
    last_purchase = summary.get("last_purchase") or {}
    col1.metric("Last purchase", last_purchase.get("date", ""))
    col2.metric("Last price", f"Rs {format_number(summary.get('last_price'))}" if summary.get("last_price") is not None else "")
    col3.metric("Average price/unit", f"Rs {format_number(summary.get('average_price'))}" if summary.get("average_price") is not None else "")
    col4.metric("Lowest / Highest", "" if summary.get("lowest_price") is None else f"Rs {format_number(summary.get('lowest_price'))} / Rs {format_number(summary.get('highest_price'))}")
    col5.metric("Trend", summary.get("trend", "usual"))
    if history:
        st.markdown("**Purchase history**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Date": row["date"],
                        "Vendor": row["vendor"],
                        "Brand": row["brand"],
                        "Qty": f"{format_number(row['quantity'])} {row['unit']}".strip(),
                        "Price": f"Rs {format_number(row['price'])}" if row.get("price") is not None else "",
                        "Price / unit": f"Rs {format_number(row['price_per_unit'])}" if row.get("price_per_unit") is not None else "",
                        "Status": row["status"],
                    }
                    for row in history[:10]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_item_detail(profile, item, workspace_name):
    st.caption(f"{workspace_name} > {category_name(profile, item.get('category_id', ''))} > {item['name']}")
    st.markdown(f"### {item['name']}")
    stock_tab, price_tab, history_tab, consumption_tab = st.tabs(["Stock Lots", "Price History", "Purchase History", "Consumption"])
    with stock_tab:
        render_inventory_item_editor(profile, item)
        st.markdown("**Lots / packets**")
        render_inventory_lots(profile, item)
    with price_tab:
        render_item_purchase_history(item)
    with history_tab:
        history = purchase_history_for_item(item)
        if history:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Date": row["date"],
                            "Vendor": row["vendor"],
                            "Brand": row["brand"],
                            "Qty": f"{format_number(row['quantity'])} {row['unit']}".strip(),
                            "Price": f"Rs {format_number(row['price'])}" if row.get("price") is not None else "",
                            "Status": row["status"],
                        }
                        for row in history[:20]
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("No purchase history yet.")
    with consumption_tab:
        metrics = average_usage_metrics(profile, item)
        prediction = next_refill_prediction(profile, item)
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg weekly usage", f"{format_number(metrics.get('weekly_usage'))} {item.get('unit', '')}".strip() if metrics.get("weekly_usage") is not None else "")
        col2.metric("Avg monthly usage", f"{format_number(metrics.get('monthly_usage'))} {item.get('unit', '')}".strip() if metrics.get("monthly_usage") is not None else "")
        col3.metric("Avg purchase interval", f"{prediction.get('average_interval_days')} days" if prediction.get("average_interval_days") is not None else "")
        if prediction.get("why"):
            st.caption(prediction["why"])


def vendor_purchase_rows(profile, vendor_name):
    rows = []
    for item in profile.get("inventory", []):
        for row in purchase_history_for_item(item):
            if row.get("vendor") == vendor_name:
                rows.append(
                    {
                        "item_name": item["name"],
                        "category": category_name(profile, item.get("category_id", "")),
                        **row,
                    }
                )
    rows.sort(key=lambda row: row["date"], reverse=True)
    return rows


def render_vendor_detail(profile, vendor_name):
    vendor = vendor_lookup(profile).get(vendor_name)
    if not vendor:
        st.write("No vendor selected.")
        return
    rows = vendor_purchase_rows(profile, vendor_name)
    st.caption(f"Shopping > {vendor_name} > Vendor Detail")
    st.markdown(f"### {vendor_name}")
    overview_tab, history_tab, items_tab = st.tabs(["Overview", "Purchase History", "Items Bought"])
    with overview_tab:
        meta1, meta2, meta3 = st.columns(3)
        meta1.metric("Vendor type", vendor.get("vendor_type", "Other"))
        meta2.metric("Recent purchases", len(rows))
        average_spend = round(sum(row.get("price") or 0.0 for row in rows) / len(rows), 2) if rows else 0.0
        meta3.metric("Average spend", f"Rs {format_number(average_spend)}" if rows else "")
        if vendor.get("preferred_categories"):
            st.caption("Preferred categories: " + ", ".join(vendor["preferred_categories"]))
        if vendor.get("notes"):
            st.write(vendor["notes"])
        if vendor.get("purchase_pattern"):
            st.caption(f"Purchase pattern: {vendor['purchase_pattern']}")
        if vendor.get("price_trend_summary"):
            st.caption(f"Price trend summary: {vendor['price_trend_summary']}")
    with history_tab:
        if rows:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Date": row["date"],
                            "Item": row["item_name"],
                            "Category": row["category"],
                            "Qty": f"{format_number(row['quantity'])} {row['unit']}".strip(),
                            "Price": f"Rs {format_number(row['price'])}" if row.get("price") is not None else "",
                        }
                        for row in rows[:15]
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("No purchase history for this vendor yet.")
    with items_tab:
        if rows:
            categories = sorted({row["category"] for row in rows})
            items = sorted({row["item_name"] for row in rows})
            st.caption("Categories usually bought: " + ", ".join(categories))
            st.caption("Items bought from this vendor: " + ", ".join(items[:10]) + ("..." if len(items) > 10 else ""))
        else:
            st.write("No items recorded for this vendor yet.")


def render_inventory_adjustment_form(profile):
    items = profile.get("inventory", [])
    if not items:
        st.write("No items yet to adjust.")
        return
    item_ids = [item["id"] for item in items]
    item_id = st.selectbox("Item", item_ids, format_func=lambda value: inventory_item_lookup(profile).get(value, {}).get("name", value), key="inventory_adjust_item")
    item = inventory_item_lookup(profile)[item_id]
    with st.form(f"inventory_adjustment_{item_id}"):
        action = st.selectbox("Action", ["Add", "Deduct", "Set exact quantity", "Mark expired", "Mark perished/spoiled", "Mark spilled/lost", "Mark given away", "Move location", "Manual correction"])
        quantity = st.number_input("Quantity", min_value=0.0, step=0.25, value=1.0)
        location_ids = [""] + [entry["id"] for entry in profile.get("storage_locations", [])]
        move_location = st.selectbox(
            "Move to location",
            location_ids,
            format_func=lambda value: inventory_location_lookup(profile).get(value, {}).get("name", "Keep current") if value else "Keep current",
        )
        notes = st.text_area("Notes", height=80)
        submit = st.form_submit_button("Apply adjustment")
    if submit:
        change_value = 0.0
        reason = action.lower()
        if action == "Add":
            item["lots"] = [
                normalize_inventory_lot(
                    {
                        "quantity": quantity,
                        "unit": item.get("unit", "unit"),
                        "status": "opened",
                        "purchase_date": today_iso(),
                        "location_id": move_location or item.get("location_id", ""),
                    },
                    item,
                ),
                *item.get("lots", []),
            ]
            change_value = quantity
        elif action == "Deduct":
            change_value = -deduct_from_item(item, quantity)
        elif action == "Set exact quantity":
            change_value = set_exact_item_quantity(item, quantity)
        elif action in {"Mark expired", "Mark perished/spoiled", "Mark spilled/lost", "Mark given away"}:
            current = inventory_total_quantity(item)
            mark_item_status(item, "expired" if action == "Mark expired" else "finished")
            change_value = -current
        elif action == "Move location":
            if move_location:
                item["location_id"] = move_location
                item["lots"] = [{**lot, "location_id": move_location} for lot in item.get("lots", [])]
        elif action == "Manual correction":
            change_value = set_exact_item_quantity(item, quantity)
            reason = "manual correction"
        save_inventory_item(profile, item)
        add_inventory_transaction(profile, item, change_value, action, reason, notes.strip())
        persist_active_profile(profile)
        st.success(f"Applied {action.lower()} to {item['name']}.")
        st.rerun()


def render_adjustment_form_for_items(profile, items, key_prefix="inventory_adjust", allow_expired=True):
    if not items:
        st.write("No items yet to adjust.")
        return
    item_ids = [item["id"] for item in items]
    item_id = st.selectbox("Item", item_ids, format_func=lambda value: inventory_item_lookup(profile).get(value, {}).get("name", value), key=f"{key_prefix}_item")
    item = inventory_item_lookup(profile)[item_id]
    action_options = ["Add", "Deduct", "Set exact quantity", "Mark finished", "Mark spilled/lost", "Mark given away", "Move location", "Manual correction"]
    if allow_expired:
        action_options.insert(3, "Mark expired")
        action_options.insert(4, "Mark perished/spoiled")
    with st.form(f"{key_prefix}_{item_id}"):
        action = st.selectbox("Action", action_options)
        quantity = st.number_input("Quantity", min_value=0.0, step=0.25, value=1.0, key=f"{key_prefix}_qty")
        location_ids = [""] + [entry["id"] for entry in profile.get("storage_locations", [])]
        move_location = st.selectbox(
            "Move to location",
            location_ids,
            format_func=lambda value: inventory_location_lookup(profile).get(value, {}).get("name", "Keep current") if value else "Keep current",
            key=f"{key_prefix}_move",
        )
        notes = st.text_area("Notes", height=80, key=f"{key_prefix}_notes")
        submit = st.form_submit_button("Apply adjustment")
    if submit:
        change_value = 0.0
        reason = action.lower()
        if action == "Add":
            item["lots"] = [
                normalize_inventory_lot(
                    {
                        "quantity": quantity,
                        "unit": item.get("unit", "unit"),
                        "status": "opened",
                        "purchase_date": today_iso(),
                        "location_id": move_location or item.get("location_id", ""),
                    },
                    item,
                ),
                *item.get("lots", []),
            ]
            change_value = quantity
        elif action == "Deduct":
            change_value = -deduct_from_item(item, quantity)
        elif action == "Set exact quantity":
            change_value = set_exact_item_quantity(item, quantity)
        elif action in {"Mark expired", "Mark perished/spoiled", "Mark spilled/lost", "Mark given away", "Mark finished"}:
            current = inventory_total_quantity(item)
            mark_item_status(item, "expired" if action == "Mark expired" else "finished")
            change_value = -current
        elif action == "Move location":
            if move_location:
                item["location_id"] = move_location
                item["lots"] = [{**lot, "location_id": move_location} for lot in item.get("lots", [])]
        elif action == "Manual correction":
            change_value = set_exact_item_quantity(item, quantity)
            reason = "manual correction"
        save_inventory_item(profile, item)
        add_inventory_transaction(profile, item, change_value, action, reason, notes.strip())
        persist_active_profile(profile)
        st.success(f"Applied {action.lower()} to {item['name']}.")
        st.rerun()


def render_inventory_workspace(profile):
    st.markdown("**Inventory**")
    current_section = st.session_state.get("inventory_section", "Overview")
    inventory_items = food_inventory_items(profile)
    left_col, main_col = st.columns([1, 3], gap="large")
    with left_col:
        st.caption("Inventory sections")
        desktop_section = st.radio("Section", INVENTORY_SECTIONS, index=INVENTORY_SECTIONS.index(current_section), label_visibility="collapsed")
        if desktop_section != current_section:
            set_inventory_section(desktop_section)
            current_section = desktop_section
        category_choices = [item["name"] for item in profile.get("inventory_categories", []) if not is_home_supply_category_name(item["name"])]
        selected_categories = st.multiselect("Categories", category_choices, default=st.session_state.get("inventory_category_filters", []))
        st.session_state.inventory_category_filters = selected_categories
    with main_col:
        if hasattr(st, "segmented_control"):
            mobile_section = st.segmented_control("Inventory section", INVENTORY_SECTIONS, default=current_section, selection_mode="single")
        else:
            mobile_section = st.selectbox("Inventory section", INVENTORY_SECTIONS, index=INVENTORY_SECTIONS.index(current_section))
        if mobile_section != current_section:
            set_inventory_section(mobile_section)
            current_section = mobile_section

        filtered_items = []
        allowed_categories = set(st.session_state.get("inventory_category_filters", []))
        for item in inventory_items:
            if allowed_categories and category_name(profile, item.get("category_id", "")) not in allowed_categories:
                continue
            filtered_items.append(item)

        if inventory_empty(profile, inventory_items):
            render_inventory_empty_state(profile)

        if current_section == "Overview":
            overview = inventory_overview(profile)
            card1, card2, card3, card4, card5 = st.columns(5)
            card1.metric("Low Stock", len(overview["low_stock"]))
            card2.metric("Expiring Soon", len(overview["expiring"]))
            card3.metric("Over Capacity", overview["over_capacity"])
            card4.metric("Open Items", overview["open_items"])
            card5.metric("Meal Plan Impact", "Soon")
            quick_cols = st.columns(6)
            if quick_cols[0].button("Add Item", use_container_width=True):
                st.session_state.inventory_section = "Items"
                st.session_state.inventory_quick_action = "add_item"
                st.rerun()
            if quick_cols[1].button("Add Purchase", use_container_width=True):
                st.session_state.inventory_section = "Items"
                st.session_state.inventory_quick_action = "add_purchase"
                st.rerun()
            if quick_cols[2].button("Adjust Stock", use_container_width=True):
                st.session_state.inventory_section = "Adjustments"
                st.rerun()
            if quick_cols[3].button("Scan Invoice", use_container_width=True):
                st.session_state.inventory_section = "Items"
                st.session_state.inventory_quick_action = "add_purchase"
                st.session_state.purchase_mode_hint = "Invoice Image"
                st.rerun()
            if quick_cols[4].button("Voice Update", use_container_width=True):
                st.session_state.inventory_section = "Items"
                st.session_state.inventory_quick_action = "add_purchase"
                st.session_state.purchase_mode_hint = "Voice"
                st.rerun()
            if quick_cols[5].button("Search", use_container_width=True):
                st.session_state.inventory_section = "Items"
                st.rerun()

            preview_col, low_col = st.columns(2)
            with preview_col:
                st.markdown("**Expiring soon preview**")
                if overview["expiring"]:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Item": item["name"],
                                    "Expiry": expiry_value,
                                    "Days left": days,
                                }
                                for days, item, _lot, expiry_value in overview["expiring"][:5]
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.write("Nothing urgent right now.")
            with low_col:
                st.markdown("**Top items running low**")
                if overview["low_stock"]:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Item": item["name"],
                                    "Quantity": format_number(inventory_total_quantity(item)),
                                    "Refill level": format_number(item.get("refill_level")),
                                }
                                for item in overview["low_stock"][:5]
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.write("No low stock items yet.")
            with st.container(border=True):
                st.markdown("**Seasonal picks**")
                st.write("Seasonal suggestions and planner links will connect here in a later phase.")

        elif current_section == "Items":
            quick_action = st.session_state.pop("inventory_quick_action", "")
            add_item_expanded = quick_action == "add_item"
            add_purchase_expanded = quick_action == "add_purchase"
            with st.expander("Add Item", expanded=add_item_expanded):
                render_inventory_quick_add(profile, f"inventory_add_item_{profile['id']}", add_purchase=False)
            with st.expander("Add Purchase", expanded=add_purchase_expanded):
                render_purchase_intake(profile, f"inventory_add_purchase_{profile['id']}")
            with st.expander("Bulk Purchase Import", expanded=quick_action == "bulk_import"):
                st.caption("Paste a bill CSV with columns like Date, Location, Bill No, Item, Quantity, Unit, Rate (Rs), Amount (Rs), or upload a .csv file.")
                uploaded_purchase_file = st.file_uploader("Upload purchase CSV", type=["csv"], key=f"purchase_import_file_{profile['id']}")
                purchase_import_text = st.text_area(
                    "Or paste purchase CSV",
                    value=st.session_state.get("purchase_import_text", ""),
                    height=220,
                    key="purchase_import_text",
                )
                import_source_text = purchase_import_text
                if uploaded_purchase_file is not None:
                    import_source_text = uploaded_purchase_file.getvalue().decode("utf-8")
                parsed_rows = parse_purchase_import_rows(import_source_text)
                if parsed_rows:
                    preview_rows = [
                        {
                            "Date": row["date"],
                            "Store": row["location"],
                            "Bill": row["bill_no"],
                            "Item": row["item"],
                            "Qty": format_number(row["quantity"]),
                            "Unit": row["unit"],
                            "Amount": format_number(row["amount"]),
                        }
                        for row in parsed_rows[:12]
                    ]
                    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)
                    st.caption(
                        f"{len(parsed_rows)} rows ready to import | Total Rs {format_number(sum(row.get('amount') or 0.0 for row in parsed_rows))}"
                    )
                    if st.button("Send CSV To Review", use_container_width=True, key=f"purchase_import_apply_{profile['id']}"):
                        set_purchase_review_items(
                            review_items_from_import_rows(profile, parsed_rows, parse_source="csv"),
                            source="csv",
                        )
                        st.session_state.inventory_section = "Items"
                        st.rerun()
                elif import_source_text.strip():
                    st.warning("Could not parse any purchase rows. Check that the CSV header matches the bill columns.")
            with st.expander("Add category", expanded=False):
                with st.form(f"inventory_category_form_{profile['id']}"):
                    category_title = st.text_input("Category name")
                    category_shelf_life = st.number_input("Default shelf life (days)", min_value=1, step=1, value=30)
                    save_category = st.form_submit_button("Save category")
                if save_category and category_title.strip():
                    category = normalize_inventory_category({"name": category_title.strip(), "shelf_life_days": category_shelf_life})
                    profile["inventory_categories"] = [entry for entry in profile.get("inventory_categories", []) if entry["id"] != category["id"]] + [category]
                    persist_active_profile(profile)
                    st.rerun()
            search = st.text_input("Search items", key="inventory_search")
            if st.session_state.get("inventory_flash"):
                st.success(st.session_state.pop("inventory_flash"))
            rows = [
                row
                for row in inventory_rows_for_items(profile, filtered_items)
                if row["id"] in {item["id"] for item in filtered_items}
                and search.lower() in row["Item name"].lower()
            ]
            if rows:
                st.dataframe(pd.DataFrame([{key: value for key, value in row.items() if key != "id"} for row in rows]), use_container_width=True, hide_index=True)
            item_options = {"Select an item": ""}
            for item in filtered_items:
                item_options[f"{item['name']} | {category_name(profile, item.get('category_id', ''))}"] = item["id"]
            selected_item_id = st.selectbox("Item detail", list(item_options.values()), format_func=lambda value: next(label for label, item_id in item_options.items() if item_id == value), key=f"inventory_item_select_{profile['id']}")
            selected_item = inventory_item_lookup(profile).get(selected_item_id)
            if selected_item:
                render_item_detail(profile, selected_item, "Inventory")

        elif current_section == "Expiry":
            urgency_groups = {"Use today": [], "Use in next 3 days": [], "Use in next 7 days": [], "Watch list": []}
            for item in filtered_items:
                nearest = None
                for lot in active_lots(item):
                    expiry_value = item_expiry_date(profile, item, lot)
                    days = days_to_expiry(expiry_value)
                    if days is None:
                        continue
                    nearest = (days, expiry_value) if nearest is None or days < nearest[0] else nearest
                if not nearest:
                    continue
                days, expiry_value = nearest
                row = {"Item": item["name"], "Category": category_name(profile, item.get("category_id", "")), "Expiry": expiry_value, "Days left": days}
                if days <= 0:
                    urgency_groups["Use today"].append(row)
                elif days <= 3:
                    urgency_groups["Use in next 3 days"].append(row)
                elif days <= 7:
                    urgency_groups["Use in next 7 days"].append(row)
                else:
                    urgency_groups["Watch list"].append(row)
            for group_name, rows in urgency_groups.items():
                with st.expander(group_name, expanded=group_name != "Watch list"):
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.write("No items in this group.")

        elif current_section == "Adjustments":
            with st.container(border=True):
                st.markdown("**Adjust Stock**")
                render_adjustment_form_for_items(profile, filtered_items, key_prefix=f"inventory_adjust_food_{profile['id']}", allow_expired=True)
            st.markdown("**Adjustment history**")
            transactions = [
                item
                for item in profile.get("inventory_transactions", [])
                if inventory_item_lookup(profile).get(item.get("item_id", "")) and not is_home_supply_item(profile, inventory_item_lookup(profile).get(item.get("item_id", "")))
            ]
            if transactions:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Date/time": item.get("created_at", "").replace("T", " "),
                                "Item": item.get("item_name", ""),
                                "Change": quantity_delta_text(item.get("change_value", 0.0), item.get("unit", "")),
                                "Reason": item.get("reason", ""),
                                "Notes": item.get("notes", ""),
                                "Source": item.get("source", "manual"),
                            }
                            for item in transactions
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.write("No adjustments yet.")

        elif current_section == "Storage":
            st.markdown("**Storage locations**")
            location_rows = []
            for location in profile.get("storage_locations", []):
                usage = 0.0
                unit = location.get("capacity_unit", "")
                for item in filtered_items:
                    for lot in active_lots(item):
                        if lot.get("location_id") == location["id"] and (not unit or lot.get("unit", "") == unit):
                            usage += lot.get("quantity", 0.0)
                capacity_value = location.get("capacity_value")
                location_rows.append(
                    {
                        "Location": location["name"],
                        "Capacity": f"{format_number(capacity_value)} {unit}".strip() if capacity_value else "",
                        "Usage": f"{format_number(usage)} {unit}".strip() if usage else "0",
                        "Status": "Over Capacity" if capacity_value and usage > capacity_value else "OK",
                    }
                )
            st.dataframe(pd.DataFrame(location_rows), use_container_width=True, hide_index=True)
            location_options = {"Add location": ""}
            for location in profile.get("storage_locations", []):
                location_options[f"Edit {location['name']}"] = location["id"]
            selected_location_id = st.selectbox("Location detail", list(location_options.values()), format_func=lambda value: next(label for label, location_id in location_options.items() if location_id == value), key=f"storage_location_select_{profile['id']}")
            selected_location = next((entry for entry in profile.get("storage_locations", []) if entry["id"] == selected_location_id), None)
            with st.form(f"storage_form_{profile['id']}"):
                location_name = st.text_input("Location name", value=selected_location.get("name", "") if selected_location else "")
                capacity_value = st.number_input("Optional capacity", min_value=0.0, step=0.25, value=float(selected_location.get("capacity_value", 0.0) if selected_location and selected_location.get("capacity_value") is not None else 0.0))
                capacity_unit = st.text_input("Capacity unit", value=selected_location.get("capacity_unit", "") if selected_location else "")
                location_notes = st.text_input("Notes", value=selected_location.get("notes", "") if selected_location else "")
                save_location = st.form_submit_button("Save location")
            if save_location and location_name.strip():
                location = normalize_storage_location(
                    {
                        "id": selected_location["id"] if selected_location else uuid4().hex,
                        "name": location_name.strip(),
                        "capacity_value": capacity_value or None,
                        "capacity_unit": capacity_unit.strip(),
                        "notes": location_notes.strip(),
                    }
                )
                profile["storage_locations"] = [entry for entry in profile.get("storage_locations", []) if entry["id"] != location["id"]] + [location]
                persist_active_profile(profile)
                st.rerun()

        elif current_section == "Analytics":
            rows = inventory_rows_for_items(profile, filtered_items)
            if rows:
                by_category = {}
                by_status = {}
                for row in rows:
                    by_category[row["Category"]] = by_category.get(row["Category"], 0) + 1
                    by_status[row["Status"]] = by_status.get(row["Status"], 0) + 1
                col1, col2 = st.columns(2)
                col1.dataframe(pd.DataFrame([{"Category": key, "Items": value} for key, value in by_category.items()]), use_container_width=True, hide_index=True)
                col2.dataframe(pd.DataFrame([{"Status": key, "Items": value} for key, value in by_status.items()]), use_container_width=True, hide_index=True)
            else:
                st.write("Add inventory items to unlock analytics.")


def render_home_supplies_workspace(profile):
    st.markdown("**Home Supplies**")
    current_section = st.session_state.get("home_supply_section", "Overview")
    items = home_supply_items(profile)
    left_col, main_col = st.columns([1, 3], gap="large")
    with left_col:
        st.caption("Home supplies sections")
        desktop_section = st.radio("Section", INVENTORY_SECTIONS, index=INVENTORY_SECTIONS.index(current_section), label_visibility="collapsed", key=f"home_supply_radio_{profile['id']}")
        if desktop_section != current_section:
            set_home_supply_section(desktop_section)
            current_section = desktop_section
        category_choices = [item["name"] for item in profile.get("inventory_categories", []) if is_home_supply_category_name(item["name"])]
        selected_categories = st.multiselect("Categories", category_choices, default=st.session_state.get("home_supply_category_filters", []), key=f"home_supply_categories_{profile['id']}")
        st.session_state.home_supply_category_filters = selected_categories
    with main_col:
        if hasattr(st, "segmented_control"):
            mobile_section = st.segmented_control("Home supplies section", INVENTORY_SECTIONS, default=current_section, selection_mode="single", key=f"home_supply_segment_{profile['id']}")
        else:
            mobile_section = st.selectbox("Home supplies section", INVENTORY_SECTIONS, index=INVENTORY_SECTIONS.index(current_section), key=f"home_supply_select_{profile['id']}")
        if mobile_section != current_section:
            set_home_supply_section(mobile_section)
            current_section = mobile_section

        allowed_categories = set(st.session_state.get("home_supply_category_filters", []))
        filtered_items = []
        for item in items:
            if allowed_categories and category_name(profile, item.get("category_id", "")) not in allowed_categories:
                continue
            filtered_items.append(item)

        if inventory_empty(profile, items):
            render_inventory_empty_state(
                profile,
                heading="Track cleaners, toiletries, laundry, and household supplies here.",
                add_item_label="Add Supply",
                add_purchase_label="Add Purchase",
                setup_label="Set Up Categories",
                key_prefix="home_supplies_empty",
                section_name="Items",
                quick_item_action="home_add_item",
                quick_purchase_action="home_add_purchase",
            )

        if current_section == "Overview":
            overview = inventory_overview(profile, filtered_items)
            recent_purchases = sum(
                1
                for item in filtered_items
                for lot in item.get("lots", [])
                if lot.get("purchase_date", "") >= (date.today() - timedelta(days=30)).isoformat()
            )
            monthly_spend = sum(
                (try_float(lot.get("price")) or 0.0)
                for item in filtered_items
                for lot in item.get("lots", [])
                if lot.get("purchase_date", "") >= (date.today() - timedelta(days=30)).isoformat()
            )
            card1, card2, card3, card4, card5 = st.columns(5)
            card1.metric("Low Stock", len(overview["low_stock"]))
            card2.metric("Refill Due", len(overview["low_stock"]))
            card3.metric("Over Capacity", overview["over_capacity"])
            card4.metric("Recently Purchased", recent_purchases)
            card5.metric("Monthly Spend", f"Rs {format_number(monthly_spend)}" if monthly_spend else "")
            quick_cols = st.columns(4)
            if quick_cols[0].button("Add Supply", use_container_width=True, key=f"home_supply_add_{profile['id']}"):
                st.session_state.home_supply_section = "Items"
                st.session_state.inventory_quick_action = "home_add_item"
                st.rerun()
            if quick_cols[1].button("Add Purchase", use_container_width=True, key=f"home_supply_purchase_{profile['id']}"):
                st.session_state.home_supply_section = "Items"
                st.session_state.inventory_quick_action = "home_add_purchase"
                st.rerun()
            if quick_cols[2].button("Adjust Supply", use_container_width=True, key=f"home_supply_adjust_{profile['id']}"):
                st.session_state.home_supply_section = "Adjustments"
                st.rerun()
            if quick_cols[3].button("Search", use_container_width=True, key=f"home_supply_search_btn_{profile['id']}"):
                st.session_state.home_supply_section = "Items"
                st.rerun()

        elif current_section == "Items":
            quick_action = st.session_state.pop("inventory_quick_action", "")
            add_item_expanded = quick_action == "home_add_item"
            add_purchase_expanded = quick_action == "home_add_purchase"
            allowed_category_ids = home_supply_category_ids(profile)
            with st.expander("Add Supply", expanded=add_item_expanded):
                render_inventory_quick_add(profile, f"home_supply_add_item_{profile['id']}", add_purchase=False, category_ids=allowed_category_ids)
            with st.expander("Add Purchase", expanded=add_purchase_expanded):
                render_purchase_intake(profile, f"home_supply_add_purchase_{profile['id']}")
            search = st.text_input("Search supplies", key=f"home_supply_search_{profile['id']}")
            if st.session_state.get("inventory_flash"):
                st.success(st.session_state.pop("inventory_flash"))
            rows = [
                row
                for row in inventory_rows_for_items(profile, filtered_items)
                if search.lower() in row["Item name"].lower()
            ]
            if rows:
                st.dataframe(pd.DataFrame([{key: value for key, value in row.items() if key != "id"} for row in rows]), use_container_width=True, hide_index=True)
            item_options = {"Select a supply": ""}
            for item in filtered_items:
                item_options[f"{item['name']} | {category_name(profile, item.get('category_id', ''))}"] = item["id"]
            selected_item_id = st.selectbox("Supply detail", list(item_options.values()), format_func=lambda value: next(label for label, item_id in item_options.items() if item_id == value), key=f"home_supply_item_select_{profile['id']}")
            selected_item = inventory_item_lookup(profile).get(selected_item_id)
            if selected_item:
                render_item_detail(profile, selected_item, "Home Supplies")

        elif current_section == "Expiry":
            urgency_groups = {"Use today": [], "Use in next 7 days": [], "Watch list": []}
            for item in filtered_items:
                nearest = None
                for lot in active_lots(item):
                    expiry_value = item_expiry_date(profile, item, lot)
                    days = days_to_expiry(expiry_value)
                    if days is None:
                        continue
                    nearest = (days, expiry_value) if nearest is None or days < nearest[0] else nearest
                if not nearest:
                    continue
                days, expiry_value = nearest
                row = {"Item": item["name"], "Category": category_name(profile, item.get("category_id", "")), "Expiry": expiry_value, "Days left": days}
                if days <= 0:
                    urgency_groups["Use today"].append(row)
                elif days <= 7:
                    urgency_groups["Use in next 7 days"].append(row)
                else:
                    urgency_groups["Watch list"].append(row)
            for group_name, rows in urgency_groups.items():
                with st.expander(group_name, expanded=group_name != "Watch list"):
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.write("No items in this group.")

        elif current_section == "Adjustments":
            with st.container(border=True):
                st.markdown("**Adjust Home Supplies**")
                render_adjustment_form_for_items(profile, filtered_items, key_prefix=f"home_supply_adjust_{profile['id']}", allow_expired=False)
            st.markdown("**Adjustment history**")
            transactions = [
                item
                for item in profile.get("inventory_transactions", [])
                if inventory_item_lookup(profile).get(item.get("item_id", "")) and is_home_supply_item(profile, inventory_item_lookup(profile).get(item.get("item_id", "")))
            ]
            if transactions:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Date/time": item.get("created_at", "").replace("T", " "),
                                "Item": item.get("item_name", ""),
                                "Change": quantity_delta_text(item.get("change_value", 0.0), item.get("unit", "")),
                                "Reason": item.get("reason", ""),
                                "Notes": item.get("notes", ""),
                                "Source": item.get("source", "manual"),
                            }
                            for item in transactions
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.write("No adjustments yet.")

        elif current_section == "Storage":
            st.markdown("**Storage locations**")
            location_rows = []
            for location in profile.get("storage_locations", []):
                usage = 0.0
                unit = location.get("capacity_unit", "")
                for item in filtered_items:
                    for lot in active_lots(item):
                        if lot.get("location_id") == location["id"] and (not unit or lot.get("unit", "") == unit):
                            usage += lot.get("quantity", 0.0)
                capacity_value = location.get("capacity_value")
                location_rows.append(
                    {
                        "Location": location["name"],
                        "Capacity": f"{format_number(capacity_value)} {unit}".strip() if capacity_value else "",
                        "Usage": f"{format_number(usage)} {unit}".strip() if usage else "0",
                        "Status": "Over Capacity" if capacity_value and usage > capacity_value else "OK",
                    }
                )
            st.dataframe(pd.DataFrame(location_rows), use_container_width=True, hide_index=True)

        elif current_section == "Analytics":
            rows = inventory_rows_for_items(profile, filtered_items)
            if rows:
                by_category = {}
                by_status = {}
                for row in rows:
                    by_category[row["Category"]] = by_category.get(row["Category"], 0) + 1
                    by_status[row["Status"]] = by_status.get(row["Status"], 0) + 1
                col1, col2 = st.columns(2)
                col1.dataframe(pd.DataFrame([{"Category": key, "Items": value} for key, value in by_category.items()]), use_container_width=True, hide_index=True)
                col2.dataframe(pd.DataFrame([{"Status": key, "Items": value} for key, value in by_status.items()]), use_container_width=True, hide_index=True)
            else:
                st.write("Add home supplies to unlock analytics.")


def build_recipe_dishes(profile):
    recipe_dishes = []
    for dish in all_recipe_dishes():
        if dish["name"] == "Morning Portion Only":
            continue
        recipe_dishes.append(
            {
                "name": dish["name"],
                "summary": dish.get("summary", ""),
                "ingredients": [{"name": item["name"], "qty": item.get("qty", "")} for item in dish.get("ingredients", [])],
                "method": dish.get("method", []),
                "youtube": dish.get("youtube", ""),
                "source": "builtin",
            }
        )
    for recipe in profile.get("recipes", []):
        factor = household_servings(profile) / max(recipe.get("base_servings", 2.0), 0.1)
        recipe_dishes.append(
            {
                "name": recipe["name"],
                "summary": recipe.get("description", ""),
                "ingredients": [scale_recipe_ingredient(item, factor) for item in recipe.get("ingredients", [])],
                "method": recipe.get("instructions", []),
                "youtube": recipe.get("youtube", ""),
                "source": "profile",
            }
        )
    return recipe_dishes


def render_shopping_workspace(profile):
    st.markdown("**Shopping**")
    suggestions = build_shopping_suggestions(profile)
    show_manual_item = st.session_state.pop("shopping_manual_quick_add", False)
    with st.expander("Manual shopping item", expanded=show_manual_item):
        st.markdown("**Manual shopping item**")
        with st.form(f"shopping_manual_item_{profile['id']}"):
            item_name = st.text_input("Item name")
            quantity = st.number_input("Quantity", min_value=0.0, step=0.25, value=1.0)
            unit = st.text_input("Unit", value="unit")
            vendor_names = [item["name"] for item in profile.get("vendors", [])]
            vendor_name = st.selectbox("Vendor", vendor_names, index=vendor_names.index("Other") if "Other" in vendor_names else 0)
            brand = st.text_input("Brand")
            notes = st.text_area("Notes", height=80)
            save_manual = st.form_submit_button("Add Manual Item")
        if save_manual:
            if not item_name.strip():
                st.error("Item name is required.")
            else:
                profile["shopping_manual_items"] = [
                    *profile.get("shopping_manual_items", []),
                    normalize_manual_shopping_item(
                        {
                            "item_name": item_name.strip(),
                            "quantity": quantity or 1.0,
                            "unit": unit.strip() or "unit",
                            "vendor_name": vendor_name,
                            "brand": brand.strip(),
                            "notes": notes.strip(),
                        }
                    ),
                ]
                persist_active_profile(profile)
                st.session_state.pending_workspace = "Shopping"
                st.rerun()

    if not suggestions:
        with st.container(border=True):
            st.info("You are stocked for now. Add a manual shopping item or review inventory.")
            col1, col2, col3 = st.columns(3)
            if col1.button("Add Manual Item", use_container_width=True):
                st.session_state.shopping_manual_quick_add = True
                st.rerun()
            if col2.button("Review Inventory", use_container_width=True):
                st.session_state.pending_workspace = "Inventory"
                st.rerun()
            if col3.button("Add Purchase", use_container_width=True):
                st.session_state.pending_workspace = "Inventory"
                st.session_state.inventory_section = "Items"
                st.session_state.inventory_quick_action = "add_purchase"
                st.rerun()
    else:
        grouped = suggestion_groups_by_vendor(profile)
        summary_cols = st.columns(4)
        summary_cols[0].metric("Suggestions", len(suggestions))
        summary_cols[1].metric("Vendors", len(grouped))
        summary_cols[2].metric("High confidence", sum(1 for item in suggestions if item["confidence"] == "High"))
        total_estimated = sum(item.get("estimated_price") or 0.0 for item in suggestions)
        summary_cols[3].metric("Estimated total", f"Rs {format_number(total_estimated)}" if total_estimated else "")
        for vendor_name, items in grouped.items():
            with st.expander(f"{vendor_name} ({len(items)})", expanded=True):
                for suggestion in items:
                    state = shopping_overrides(profile).get(suggestion["id"], {})
                    st.markdown(f"**{suggestion['item_name']}**")
                    info_cols = st.columns([2, 2, 2, 2])
                    info_cols[0].write(f"Qty: {format_number(suggestion['quantity'])} {suggestion['unit']}".strip())
                    info_cols[1].write(f"Brand: {suggestion.get('brand', '') or 'Any'}")
                    info_cols[2].write(f"Last price: {'Rs ' + format_number(suggestion['last_price']) if suggestion.get('last_price') is not None else 'NA'}")
                    info_cols[3].write(f"Confidence: {suggestion['confidence']}")
                    st.caption(f"Reason: {suggestion['reason_summary']}")
                    if suggestion.get("capacity_warning"):
                        st.warning(suggestion["capacity_warning"])
                    with st.expander("Why?"):
                        for reason in suggestion["reason_details"]:
                            st.write(f"- {reason['label']}: {reason['detail']}")
                        why = suggestion.get("why", {})
                        if why.get("current_quantity") is not None:
                            st.caption(
                                f"Current {format_number(why.get('current_quantity'))} {suggestion.get('base_unit', '')} | Refill {format_number(why.get('refill_level'))} | Capacity {format_number(why.get('storage_capacity'))}"
                            )
                        if why.get("predicted_refill_days") is not None:
                            st.caption(f"Likely refill in about {why['predicted_refill_days']} days.")
                        if why.get("prediction_why"):
                            st.write(why["prediction_why"])
                        if why.get("waste_note"):
                            st.warning(why["waste_note"])
                        if why.get("seasonal_note"):
                            st.info(why["seasonal_note"])
                    with st.form(f"shopping_edit_{suggestion['id']}"):
                        edit_cols = st.columns(3)
                        qty_value = edit_cols[0].number_input("Suggested quantity", min_value=0.0, step=0.25, value=float(suggestion["quantity"]))
                        unit_value = edit_cols[1].text_input("Unit / packet format", value=suggestion["unit"])
                        vendor_options = [item["name"] for item in profile.get("vendors", [])]
                        vendor_index = vendor_options.index(suggestion["vendor_name"]) if suggestion["vendor_name"] in vendor_options else 0
                        vendor_value = edit_cols[2].selectbox("Vendor", vendor_options, index=vendor_index)
                        save_edit = st.form_submit_button("Save suggestion")
                    if save_edit:
                        update_shopping_override(profile, suggestion["id"], quantity_override=qty_value, unit_override=unit_value.strip(), vendor_name=vendor_value)
                        persist_active_profile(profile)
                        st.rerun()
                    action_cols = st.columns(4)
                    if action_cols[0].button("Skip this time", key=f"skip_{suggestion['id']}", use_container_width=True):
                        update_shopping_override(profile, suggestion["id"], skipped_on=today_iso())
                        persist_active_profile(profile)
                        st.rerun()
                    if action_cols[1].button("Snooze 3 days", key=f"snooze_{suggestion['id']}", use_container_width=True):
                        update_shopping_override(profile, suggestion["id"], snooze_until=(date.today() + timedelta(days=3)).isoformat())
                        persist_active_profile(profile)
                        st.rerun()
                    if action_cols[2].button("Remove suggestion", key=f"remove_{suggestion['id']}", use_container_width=True):
                        if suggestion["source"] == "manual":
                            for manual_item in profile.get("shopping_manual_items", []):
                                if manual_item["id"] == suggestion["manual_id"]:
                                    manual_item["status"] = "removed"
                        else:
                            update_shopping_override(profile, suggestion["id"], removed=True)
                        persist_active_profile(profile)
                        st.rerun()
                    if action_cols[3].button("Reset", key=f"reset_{suggestion['id']}", use_container_width=True):
                        clear_shopping_override(profile, suggestion["id"], "quantity_override", "unit_override", "vendor_name", "skipped_on", "snooze_until", "removed")
                        persist_active_profile(profile)
                        st.rerun()
                    with st.form(f"shopping_buy_{suggestion['id']}"):
                        st.markdown("**Mark purchased**")
                        buy_cols = st.columns(3)
                        actual_quantity = buy_cols[0].number_input("Actual quantity bought", min_value=0.0, step=0.25, value=float(suggestion["quantity"]))
                        packet_format = buy_cols[1].text_input("Packet format / unit", value=suggestion["unit"])
                        lot_status = buy_cols[2].selectbox("Lot status", ["sealed", "opened"], index=0)
                        buy_cols2 = st.columns(4)
                        vendor_choice = buy_cols2[0].selectbox("Vendor", [item["name"] for item in profile.get("vendors", [])], index=vendor_options.index(suggestion["vendor_name"]) if suggestion["vendor_name"] in vendor_options else 0, key=f"buy_vendor_{suggestion['id']}")
                        brand_choice = buy_cols2[1].text_input("Brand", value=suggestion.get("brand", ""), key=f"buy_brand_{suggestion['id']}")
                        price_value = buy_cols2[2].number_input("Price", min_value=0.0, step=1.0, value=float(suggestion.get("estimated_price") or suggestion.get("last_price") or 0.0), key=f"buy_price_{suggestion['id']}")
                        purchase_date = buy_cols2[3].text_input("Purchase date", value=today_iso(), key=f"buy_date_{suggestion['id']}")
                        notes_value = st.text_area("Notes", value=state.get("notes", ""), height=70, key=f"buy_notes_{suggestion['id']}")
                        buy_submit = st.form_submit_button("Buy / mark purchased")
                    if buy_submit:
                        mark_suggestion_purchased(
                            profile,
                            suggestion,
                            actual_quantity,
                            packet_format.strip() or suggestion["unit"],
                            vendor_choice,
                            brand_choice.strip(),
                            price_value or None,
                            purchase_date.strip() or today_iso(),
                            lot_status,
                            notes_value.strip(),
                        )
                        persist_active_profile(profile)
                        st.session_state.pending_workspace = "Inventory"
                        st.session_state.inventory_section = "Items"
                        st.session_state.inventory_flash = f"Purchased {suggestion['item_name']}."
                        st.rerun()
                    st.divider()

    st.divider()
    vendor_col, detail_col = st.columns([1, 2], gap="large")
    with vendor_col:
        st.markdown("**Vendor records**")
        vendor_rows = [
            {
                "Name": vendor["name"],
                "Type": vendor.get("vendor_type", ""),
                "Categories": ", ".join(vendor.get("preferred_categories", [])),
            }
            for vendor in profile.get("vendors", [])
        ]
        st.dataframe(pd.DataFrame(vendor_rows), use_container_width=True, hide_index=True)
        vendor_options = {"Add vendor": ""}
        for vendor in profile.get("vendors", []):
            vendor_options[vendor["name"]] = vendor["id"]
        selected_vendor_id = st.selectbox(
            "Vendor detail",
            list(vendor_options.values()),
            format_func=lambda value: next(label for label, vendor_id in vendor_options.items() if vendor_id == value),
            key=f"vendor_select_{profile['id']}",
        )
        selected_vendor = next((item for item in profile.get("vendors", []) if item["id"] == selected_vendor_id), None)
        with st.form(f"vendor_form_{profile['id']}"):
            vendor_name = st.text_input("Vendor name", value=selected_vendor.get("name", "") if selected_vendor else "")
            vendor_type = st.selectbox("Vendor type", ["Grocery app", "Local vegetable vendor", "Kirana", "Pharmacy", "Marketplace", "Dairy", "Other"], index=["Grocery app", "Local vegetable vendor", "Kirana", "Pharmacy", "Marketplace", "Dairy", "Other"].index(selected_vendor.get("vendor_type", "Other") if selected_vendor else "Other"))
            preferred_categories = st.multiselect("Preferred categories", [item["name"] for item in profile.get("inventory_categories", [])], default=selected_vendor.get("preferred_categories", []) if selected_vendor else [])
            notes = st.text_area("Notes", value=selected_vendor.get("notes", "") if selected_vendor else "", height=80)
            purchase_pattern = st.text_input("Average delivery / purchase pattern", value=selected_vendor.get("purchase_pattern", "") if selected_vendor else "")
            trend_summary = st.text_input("Price trend summary", value=selected_vendor.get("price_trend_summary", "") if selected_vendor else "")
            save_vendor = st.form_submit_button("Save vendor")
        if save_vendor and vendor_name.strip():
            vendor = normalize_vendor_record(
                {
                    "id": selected_vendor["id"] if selected_vendor else uuid4().hex,
                    "name": vendor_name.strip(),
                    "vendor_type": vendor_type,
                    "preferred_categories": preferred_categories,
                    "notes": notes.strip(),
                    "purchase_pattern": purchase_pattern.strip(),
                    "price_trend_summary": trend_summary.strip(),
                }
            )
            profile["vendors"] = [item for item in profile.get("vendors", []) if item["id"] != vendor["id"]] + [vendor]
            persist_active_profile(profile)
            st.rerun()
    with detail_col:
        active_vendor_name = selected_vendor.get("name") if selected_vendor else "BigBasket"
        render_vendor_detail(profile, active_vendor_name)


def render_insights_workspace(profile):
    st.markdown("**Insights**")
    total_signals = len(profile.get("inventory_transactions", [])) + sum(len(item.get("lots", [])) for item in profile.get("inventory", []))
    if total_signals < 6:
        with st.container(border=True):
            st.info("Insights will improve as you add purchases, deductions, and adjustments.")
            col1, col2, col3 = st.columns(3)
            if col1.button("Add Purchase", use_container_width=True, key=f"insights_add_purchase_{profile['id']}"):
                st.session_state.pending_workspace = "Inventory"
                st.session_state.inventory_section = "Items"
                st.session_state.inventory_quick_action = "add_purchase"
                st.rerun()
            if col2.button("Review Inventory", use_container_width=True, key=f"insights_inventory_{profile['id']}"):
                st.session_state.pending_workspace = "Inventory"
                st.rerun()
            if col3.button("Open Shopping", use_container_width=True, key=f"insights_shopping_{profile['id']}"):
                st.session_state.pending_workspace = "Shopping"
                st.rerun()

    weather_col, season_col = st.columns([1, 2])
    weather_options = ["Hot / Humid", "Normal", "Cool"]
    current_weather = profile.get("preferences", {}).get("weather_mode", "Normal")
    weather_mode = weather_col.selectbox("Perishability condition", weather_options, index=weather_options.index(current_weather) if current_weather in weather_options else 1, key=f"weather_mode_{profile['id']}")
    if weather_mode != current_weather:
        profile["preferences"]["weather_mode"] = weather_mode
        persist_active_profile(profile)
        st.rerun()
    season_col.caption(f"Current seasonal context: **{current_season_label()}**")

    consumption_tab, price_tab, vendor_tab, waste_tab, storage_tab, seasonal_tab, predictions_tab = st.tabs(
        ["Consumption", "Price Analysis", "Vendor Comparison", "Waste / Spoilage", "Storage", "Seasonal", "Predictions"]
    )

    with consumption_tab:
        rows = []
        for item in profile.get("inventory", []):
            metrics = average_usage_metrics(profile, item)
            interval = average_purchase_interval_days(item)
            if metrics["weekly"] is None and interval is None:
                continue
            rows.append(
                {
                    "Item": item["name"],
                    "Category": category_name(profile, item.get("category_id", "")),
                    "Avg / week": format_number(metrics["weekly"]),
                    "Avg / month": format_number(metrics["monthly"]),
                    "Avg purchase interval": interval,
                    "Avg consumed / event": format_number(metrics["avg_event_quantity"]),
                    "Trend": metrics["trend"],
                    "Confidence": metrics["confidence"],
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("Not enough usage data yet.")

    with price_tab:
        rows = []
        for item in profile.get("inventory", []):
            summary = price_summary_for_item(item)
            best_vendor = None
            best_price = None
            for row in purchase_history_for_item(item):
                if row.get("price_per_unit") is None:
                    continue
                if best_price is None or row["price_per_unit"] < best_price:
                    best_price = row["price_per_unit"]
                    best_vendor = row.get("vendor", "") or item.get("preferred_vendor", "")
            if summary.get("last_price") is None and summary.get("average_price") is None:
                continue
            rows.append(
                {
                    "Item": item["name"],
                    "Last price": format_number(summary.get("last_price")),
                    "Avg price/unit": format_number(summary.get("average_price")),
                    "Lowest": format_number(summary.get("lowest_price")),
                    "Highest": format_number(summary.get("highest_price")),
                    "Trend": summary.get("trend", "usual"),
                    "Best vendor": best_vendor or "",
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("No price history yet.")

    with vendor_tab:
        rows = vendor_comparison_rows(profile)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("Vendor comparison will appear after more purchases.")

    with waste_tab:
        rows = waste_insight_rows(profile)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("No waste or spoilage patterns recorded yet.")

    with storage_tab:
        rows = storage_insight_rows(profile)
        if rows:
            overall_usage = sum(try_float(row["Usage"]) or 0.0 for row in rows)
            over_capacity = sum(1 for row in rows if row["Status"] == "Over Capacity")
            card1, card2 = st.columns(2)
            card1.metric("Tracked location usage", format_number(overall_usage))
            card2.metric("Over-capacity locations", over_capacity)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("No storage data yet.")

    with seasonal_tab:
        rows = seasonal_insight_rows(profile)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("Seasonal suggestions will appear as relevant items and history accumulate.")

    with predictions_tab:
        rows = prediction_rows(profile)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("Predictions need a little more purchase and usage history.")


def render_planner_workspace(active_profile):
    brunch_options, brunch_label_map = build_planner_options(active_profile)
    dinner_options = [planner_option_id("special", "Morning Portion Only")] + brunch_options
    dinner_label_map = {planner_option_id("special", "Morning Portion Only"): "Morning Portion Only", **brunch_label_map}
    fixed_item_meta = build_fixed_item_meta(active_profile)
    primary_member, secondary_member = planner_members(active_profile)
    primary_label = fixed_item_meta["primary_name"]
    secondary_label = fixed_item_meta["secondary_name"]
    routine_sections = build_routine_sections(active_profile)

    default_plan = DAY_PLANS["Today"]
    default_brunch_id = planner_option_id("builtin", default_plan["brunch"])
    default_dinner_id = default_dinner_option(active_profile)

    if "brunch_option_id" not in st.session_state or st.session_state.brunch_option_id not in brunch_options:
        st.session_state.brunch_option_id = default_brunch_id if default_brunch_id in brunch_options else brunch_options[0]
    if "dinner_option_id" not in st.session_state or st.session_state.dinner_option_id not in dinner_options:
        st.session_state.dinner_option_id = default_dinner_id if default_dinner_id in dinner_options else dinner_options[0]
    if "portion_you" not in st.session_state:
        st.session_state.portion_you = ""
    if "portion_varshit" not in st.session_state:
        st.session_state.portion_varshit = ""
    if "dinner_portion_you" not in st.session_state:
        st.session_state.dinner_portion_you = ""
    if "dinner_portion_varshit" not in st.session_state:
        st.session_state.dinner_portion_varshit = ""
    if "portion_you_suggestion" not in st.session_state:
        sync_portions_from_selection(active_profile)

    with st.container(border=True):
        st.markdown("<div id='planner-section'></div>", unsafe_allow_html=True)
        st.markdown("**Plan for your meal here**")
        action_left, action_right = st.columns(2)
        if action_left.button("Khane Mein Kya Khaye?", use_container_width=True):
            choose_random_meals(active_profile, brunch_options, dinner_options)
            st.rerun()
        if action_right.button("Note what I ate today", use_container_width=True):
            brunch_dish = option_to_dish(active_profile, st.session_state.brunch_option_id)
            planned_servings = portion_factor(st.session_state.get("portion_you", "")) + portion_factor(st.session_state.get("portion_varshit", ""))
            active_profile = logMeal(
                active_profile,
                brunch_dish["name"],
                st.session_state.get("portion_you", ""),
                st.session_state.get("portion_varshit", ""),
                planned_servings,
                planned_servings,
                brunch_dish.get("recipe_ref", ""),
            )
            st.session_state.mealLog = active_profile["meal_log"]
            active_profile["grocery_data"]["missing_items"] = dict(st.session_state.get("grocery_list", {}))
            persist_active_profile(active_profile)
            st.session_state.meal_log_flash = f"Logged {brunch_dish['name']}."
            st.rerun()
        if st.session_state.get("meal_log_flash"):
            st.success(st.session_state.meal_log_flash)
            st.session_state.meal_log_flash = ""

        row1, row2 = st.columns(2)
        row1.selectbox(
            "Brunch",
            brunch_options,
            index=brunch_options.index(st.session_state.brunch_option_id),
            format_func=lambda item: brunch_label_map[item],
            key="brunch_option_id",
            on_change=sync_portions_from_selection,
            args=(active_profile,),
        )
        row2.selectbox(
            "Dinner",
            dinner_options,
            index=dinner_options.index(st.session_state.dinner_option_id),
            format_func=lambda item: dinner_label_map[item],
            key="dinner_option_id",
            on_change=sync_portions_from_selection,
            args=(active_profile,),
        )

        st.markdown(f"**{primary_label} plan**")
        row4, row5 = st.columns(2)
        portion_you = row4.text_input(f"{primary_label} Brunch Portion", key="portion_you", placeholder=st.session_state.get("portion_you_suggestion", ""))
        dinner_portion_you = row5.text_input(f"{primary_label} Dinner Portion", key="dinner_portion_you", placeholder=st.session_state.get("dinner_portion_you_suggestion", ""))
        selected_you = []
        with st.expander(f"{primary_label} fixed add-ons", expanded=False):
            if fixed_item_meta["primary"]:
                checks = st.columns(4)
                for i, item in enumerate(fixed_item_meta["primary"]):
                    if checks[i % 4].checkbox(item, value=True, key=f"you_{item}"):
                        selected_you.append(item)
                    else:
                        for name, qty in fixed_item_meta["primary"][item]["ingredients"]:
                            st.session_state.grocery_list[name] = qty
            else:
                st.write("No routine add-ons set up yet.")

        selected_varshit = []
        portion_varshit = ""
        dinner_portion_varshit = ""
        if secondary_member:
            st.markdown(f"**{secondary_label} plan**")
            row6, row7 = st.columns(2)
            portion_varshit = row6.text_input(f"{secondary_label} Brunch Portion", key="portion_varshit", placeholder=st.session_state.get("portion_varshit_suggestion", ""))
            dinner_portion_varshit = row7.text_input(f"{secondary_label} Dinner Portion", key="dinner_portion_varshit", placeholder=st.session_state.get("dinner_portion_varshit_suggestion", ""))
            with st.expander(f"{secondary_label} fixed add-ons", expanded=False):
                if fixed_item_meta["secondary"]:
                    checks = st.columns(3)
                    for i, item in enumerate(fixed_item_meta["secondary"]):
                        if checks[i % 3].checkbox(item, value=True, key=f"varshit_{item}"):
                            selected_varshit.append(item)
                        else:
                            for name, qty in fixed_item_meta["secondary"][item]["ingredients"]:
                                st.session_state.grocery_list[name] = qty
                else:
                    st.write("No routine add-ons set up yet.")

    brunch = option_to_dish(active_profile, st.session_state.brunch_option_id)
    dinner = option_to_dish(active_profile, st.session_state.dinner_option_id, brunch)
    shreya_brunch_factor = portion_factor(portion_you)
    shreya_dinner_factor = portion_factor(dinner_portion_you)
    varshit_brunch_factor = portion_factor(portion_varshit)
    varshit_dinner_factor = portion_factor(dinner_portion_varshit)
    dinner_calorie_source = brunch if dinner["name"] == "Morning Portion Only" else dinner
    totals = {"you": {"calories": 0.0, "protein": 0.0}, "varshit": {"calories": 0.0, "protein": 0.0}}
    totals["you"]["calories"] += nutrition_for(brunch["name"])["you"]["calories"] * shreya_brunch_factor
    totals["you"]["protein"] += nutrition_for(brunch["name"])["you"]["protein"] * shreya_brunch_factor
    totals["you"]["calories"] += nutrition_for(dinner_calorie_source["name"])["you"]["calories"] * shreya_dinner_factor
    totals["you"]["protein"] += nutrition_for(dinner_calorie_source["name"])["you"]["protein"] * shreya_dinner_factor
    totals["varshit"]["calories"] += nutrition_for(brunch["name"])["varshit"]["calories"] * varshit_brunch_factor
    totals["varshit"]["protein"] += nutrition_for(brunch["name"])["varshit"]["protein"] * varshit_brunch_factor
    totals["varshit"]["calories"] += nutrition_for(dinner_calorie_source["name"])["varshit"]["calories"] * varshit_dinner_factor
    totals["varshit"]["protein"] += nutrition_for(dinner_calorie_source["name"])["varshit"]["protein"] * varshit_dinner_factor
    for item in selected_you:
        totals["you"]["calories"] += fixed_item_meta["primary"][item]["calories"]
        totals["you"]["protein"] += fixed_item_meta["primary"][item]["protein"]
    for item in selected_varshit:
        totals["varshit"]["calories"] += fixed_item_meta["secondary"][item]["calories"]
        totals["varshit"]["protein"] += fixed_item_meta["secondary"][item]["protein"]

    fixed_you = ", ".join(selected_you) if selected_you else "None selected"
    fixed_varshit = ", ".join(selected_varshit) if selected_varshit else "None selected"
    burn = {}
    member_pairs = [("you", primary_member)]
    if secondary_member:
        member_pairs.append(("varshit", secondary_member))
    for key, member in member_pairs:
        ratio = try_float(member.get("portion_ratio")) or 1.0
        resting_burn = round(1500 * ratio * goal_multiplier(active_profile))
        routine_burn = round(250 * ratio * activity_multiplier(active_profile))
        walking_burn = round((120 if member.get("walks_regularly") == "Yes" else 0) * ratio)
        gym_burn = round((160 if member.get("goes_to_gym") == "Yes" else 0) * ratio)
        total_spent = resting_burn + routine_burn + walking_burn + gym_burn
        burn[key] = {"total_spent": total_spent, "deficit_value": round(total_spent - totals[key]["calories"])}
    table = [
        {"Section": "Brunch", "Choice": brunch["name"], f"{primary_label} Portion": f"{portion_you} | Fixed: {fixed_you}", f"{primary_label} Calories": round(nutrition_for(brunch["name"])["you"]["calories"] * shreya_brunch_factor)},
        {"Section": "Dinner", "Choice": dinner["name"], f"{primary_label} Portion": dinner_portion_you, f"{primary_label} Calories": round(nutrition_for(dinner_calorie_source["name"])["you"]["calories"] * shreya_dinner_factor)},
        {"Section": "Add-ons", "Choice": "Selected fixed daily add-ons", f"{primary_label} Portion": fixed_you, f"{primary_label} Calories": sum(fixed_item_meta["primary"][item]["calories"] for item in selected_you)},
        {"Section": "Calories Intake", "Choice": "", f"{primary_label} Portion": "", f"{primary_label} Calories": round(totals["you"]["calories"])},
        {"Section": "Calories Spent", "Choice": "Resting burn + daily routine + walking + gym context", f"{primary_label} Portion": "", f"{primary_label} Calories": burn["you"]["total_spent"]},
        {"Section": "Deficit / Surplus", "Choice": "", f"{primary_label} Portion": "", f"{primary_label} Calories": burn["you"]["deficit_value"]},
    ]
    if secondary_member:
        table[0][f"{secondary_label} Portion"] = f"{portion_varshit} | Fixed: {fixed_varshit}"
        table[0][f"{secondary_label} Calories"] = round(nutrition_for(brunch["name"])["varshit"]["calories"] * varshit_brunch_factor)
        table[1][f"{secondary_label} Portion"] = dinner_portion_varshit
        table[1][f"{secondary_label} Calories"] = round(nutrition_for(dinner_calorie_source["name"])["varshit"]["calories"] * varshit_dinner_factor)
        table[2][f"{secondary_label} Portion"] = fixed_varshit
        table[2][f"{secondary_label} Calories"] = sum(fixed_item_meta["secondary"][item]["calories"] for item in selected_varshit)
        table[3][f"{secondary_label} Portion"] = ""
        table[3][f"{secondary_label} Calories"] = round(totals["varshit"]["calories"])
        table[4][f"{secondary_label} Portion"] = ""
        table[4][f"{secondary_label} Calories"] = burn["varshit"]["total_spent"]
        table[5][f"{secondary_label} Portion"] = ""
        table[5][f"{secondary_label} Calories"] = burn["varshit"]["deficit_value"]
    df = pd.DataFrame(table)

    def style_deficit_row(row):
        if row["Section"] != "Deficit / Surplus":
            return [""] * len(row)
        styles = [""] * len(row)
        styles[list(df.columns).index(f"{primary_label} Calories")] = "background-color: #d1fae5; color: #065f46;" if row[f"{primary_label} Calories"] >= 0 else "background-color: #fee2e2; color: #991b1b;"
        if secondary_member:
            styles[list(df.columns).index(f"{secondary_label} Calories")] = "background-color: #d1fae5; color: #065f46;" if row[f"{secondary_label} Calories"] >= 0 else "background-color: #fee2e2; color: #991b1b;"
        return styles

    ingredients_tab, calories_tab, meal_log_tab = st.tabs(["Ingredients & Recipe", "Calories", "Meal Log"])
    with ingredients_tab:
        with st.container(border=True):
            st.markdown("<div id='ingredients-section'></div>", unsafe_allow_html=True)
            all_ingredients = collect_ingredients([brunch, dinner])
            main_ingredients = collect_ingredients([brunch, dinner])
            addon_ingredients = OrderedDict()
            for item in selected_you:
                for name, qty in fixed_item_meta["primary"][item]["ingredients"]:
                    all_ingredients[name] = qty
                    addon_ingredients[name] = qty
            for item in selected_varshit:
                for name, qty in fixed_item_meta["secondary"][item]["ingredients"]:
                    all_ingredients[name] = qty
                    addon_ingredients[name] = qty
            st.markdown("**Ingredients**")
            ingredient_cols = st.columns(2)
            missing = OrderedDict()
            for i, (name, qty) in enumerate(main_ingredients.items()):
                label = f"{name}: {qty}" if qty else name
                available = ingredient_cols[i % 2].checkbox(label, value=True, key=f"ingredient_{name}")
                if not available:
                    missing[name] = qty
                    st.session_state.grocery_list[name] = qty
            with st.expander("Add-on Ingredients", expanded=False):
                addon_cols = st.columns(2)
                for i, (name, qty) in enumerate(addon_ingredients.items()):
                    label = f"{name}: {qty}" if qty else name
                    available = addon_cols[i % 2].checkbox(label, value=True, key=f"addon_ingredient_{name}")
                    if not available:
                        missing[name] = qty
                        st.session_state.grocery_list[name] = qty
            st.markdown("**Next Grocery Buy List**")
            if st.session_state.grocery_list:
                buy_cols = st.columns(2)
                bought_now = []
                for i, (name, qty) in enumerate(st.session_state.grocery_list.items()):
                    label = f"{name}: {qty}" if qty else name
                    if buy_cols[i % 2].checkbox(f"Bought - {label}", value=False, key=f"bought_{name}"):
                        bought_now.append(name)
                if bought_now:
                    for name in bought_now:
                        st.session_state.grocery_list.pop(name, None)
                        if f"ingredient_{name}" in st.session_state:
                            st.session_state[f"ingredient_{name}"] = True
                        if f"addon_ingredient_{name}" in st.session_state:
                            st.session_state[f"addon_ingredient_{name}"] = True
                        st.session_state[f"bought_{name}"] = False
                    active_profile["grocery_data"]["missing_items"] = dict(st.session_state.grocery_list)
                    persist_active_profile(active_profile)
                    st.rerun()
            else:
                st.write("All selected ingredients are available.")
            if brunch.get("has_recipe"):
                brunch_link_col, brunch_text_col = st.columns([1, 4])
                if brunch_link_col.button("Open", key=f"open_recipe_brunch_{recipe_slug(brunch['name'])}", use_container_width=True):
                    open_recipe(brunch["name"])
                    active_profile["recent_recipes"] = add_recent_entry(active_profile.get("recent_recipes", []), brunch["name"], brunch.get("recipe_ref", ""))
                    persist_active_profile(active_profile)
                    st.rerun()
                brunch_text_col.markdown(f"Brunch recipe: **{brunch['name']}**")
            if dinner.get("has_recipe"):
                dinner_link_col, dinner_text_col = st.columns([1, 4])
                if dinner_link_col.button("Open", key=f"open_recipe_dinner_{recipe_slug(dinner['name'])}", use_container_width=True):
                    open_recipe(dinner["name"])
                    active_profile["recent_recipes"] = add_recent_entry(active_profile.get("recent_recipes", []), dinner["name"], dinner.get("recipe_ref", ""))
                    persist_active_profile(active_profile)
                    st.rerun()
                dinner_text_col.markdown(f"Dinner recipe: **{dinner['name']}**")
            with st.expander("Before Didi Arrives", expanded=False):
                st.markdown("- " + "\n- ".join(routine_sections["night_prep"]))
            with st.expander("Morning Routine", expanded=False):
                st.markdown("- " + "\n- ".join(routine_sections["morning_start"]))
    with calories_tab:
        with st.container(border=True):
            st.dataframe(df.style.apply(style_deficit_row, axis=1), use_container_width=True, hide_index=True)
    with meal_log_tab:
        with st.container(border=True):
            MealLogTab(active_profile)


def render_recipes_workspace(active_profile):
    recipe_dishes = build_recipe_dishes(active_profile)
    recipe_slugs = {recipe_slug(dish["name"]) for dish in recipe_dishes}
    selected_recipe_slug = st.session_state.get("selected_recipe_slug", "")
    if selected_recipe_slug not in recipe_slugs:
        st.session_state.selected_recipe_slug = ""
        selected_recipe_slug = ""
    with st.container(border=True):
        render_recipe_manager(active_profile, favorites_only=False)
    st.divider()
    section_intro("recipes-section", "Recipe View")
    with st.container(border=True):
        if st.session_state.get("recipe_flash"):
            st.success(st.session_state.recipe_flash)
            st.session_state.recipe_flash = ""
        with st.expander("Add Recipe", expanded=False):
            with st.form(f"quick_recipe_form_{active_profile['id']}"):
                quick_recipe_name = st.text_input("Recipe name")
                quick_recipe_description = st.text_area("Description", height=80)
                quick_base_servings = st.number_input("Base serving count", min_value=1.0, max_value=12.0, step=0.5, value=2.0)
                quick_recipe_ingredients = st.text_area("Ingredients (one per line: name | quantity | unit | notes)", height=150)
                quick_cooking_style = st.text_input("Cooking style or method")
                quick_recipe_instructions = st.text_area("Instructions (one step per line)", height=150)
                quick_recipe_youtube = st.text_input("Optional YouTube link")
                quick_save_recipe = st.form_submit_button("Save recipe")
            if quick_save_recipe:
                if not quick_recipe_name.strip():
                    st.error("Recipe name is required.")
                else:
                    instructions = [line.strip() for line in quick_recipe_instructions.splitlines() if line.strip()]
                    if quick_cooking_style.strip():
                        instructions = [f"Cooking style: {quick_cooking_style.strip()}"] + instructions
                    quick_recipe = normalize_recipe({"id": uuid4().hex, "name": quick_recipe_name.strip(), "description": quick_recipe_description.strip(), "base_servings": quick_base_servings, "ingredients": parse_ingredient_lines(quick_recipe_ingredients), "instructions": instructions, "youtube": quick_recipe_youtube.strip(), "favorite": False})
                    active_profile["recipes"] = [item for item in active_profile.get("recipes", []) if item["name"].strip().lower() != quick_recipe["name"].strip().lower()] + [quick_recipe]
                    persist_active_profile(active_profile)
                    st.session_state.recipe_flash = f"Saved recipe {quick_recipe['name']}."
                    st.rerun()
        for dish in recipe_dishes:
            st.markdown(f"<div id='{recipe_anchor_id(dish['name'])}' class='recipe-anchor'></div>", unsafe_allow_html=True)
            with st.expander(dish["name"], expanded=recipe_slug(dish["name"]) == selected_recipe_slug):
                st.write(dish["summary"])
                st.markdown("**Ingredients**")
                st.markdown("- " + "\n- ".join(f"{item['name']}: {item.get('qty', '')}".rstrip(": ") for item in dish["ingredients"]))
                st.markdown("**Method**")
                st.markdown("- " + "\n- ".join(dish["method"]))
                if dish.get("youtube"):
                    st.markdown(f"**YouTube:** [Open recipe video]({dish['youtube']})")
                    st.video(dish["youtube"])
    if selected_recipe_slug:
        components.html(
            f"""
            <script>
            const anchorId = {json.dumps(recipe_anchor_id(selected_recipe_slug))};
            const scrollToRecipe = () => {{
              const doc = window.parent.document;
              const target = doc.getElementById(anchorId);
              if (!target) return;
              target.scrollIntoView({{ behavior: "smooth", block: "start" }});
            }};
            requestAnimationFrame(() => setTimeout(scrollToRecipe, 80));
            </script>
            """,
            height=0,
        )
st.set_page_config(page_title="Main Meal Planner Varhshree", page_icon="🥗", layout="wide")
inject_ui_styles()

if not st.session_state.get("planner_user_id"):
    remembered_user_id = load_remembered_user_id()
    if remembered_user_id:
        st.session_state.planner_user_id = remembered_user_id

if not st.session_state.get("planner_user_id"):
    render_user_gate()

profile_store = load_profile_store(user_profile_store_path(st.session_state["planner_user_id"]))
active_profile = get_active_profile(profile_store)

if st.session_state.get("active_profile_loaded") != active_profile["id"]:
    st.session_state.active_profile_loaded = active_profile["id"]
    st.session_state.grocery_list = OrderedDict(active_profile.get("grocery_data", {}).get("missing_items", {}))
    st.session_state.mealLog = list(active_profile.get("meal_log", []))
    st.session_state.selected_recipe_slug = ""
    set_active_workspace("Planner")
    st.session_state.mobile_more_workspace = MOBILE_MORE_WORKSPACES[0]
    st.session_state.pending_workspace = ""
    st.session_state.purchase_review_items = []
    st.session_state.purchase_review_error = ""
    st.session_state.purchase_review_source = ""
    for key in ["portion_you", "portion_varshit", "dinner_portion_you", "dinner_portion_varshit"]:
        st.session_state[key] = ""

st.title("Main Meal Planner Varhshree")
user_bar_left, user_bar_right = st.columns([3, 2])
user_bar_left.caption(f"Using User ID: `{st.session_state.get('planner_user_id', '')}`")
user_actions = user_bar_right.columns(2)
if user_actions[0].button("Switch User", use_container_width=True):
    st.session_state.pop("planner_user_id", None)
    reset_user_session_state()
    st.rerun()
if user_actions[1].button("Forget This Device", use_container_width=True):
    clear_remembered_user_id()
    st.session_state.pop("planner_user_id", None)
    reset_user_session_state()
    st.rerun()
pending_workspace = st.session_state.pop("pending_workspace", "")
if pending_workspace in DESKTOP_WORKSPACE_TABS:
    set_active_workspace(pending_workspace)
if st.session_state.get("active_workspace") not in DESKTOP_WORKSPACE_TABS:
    set_active_workspace("Planner")
current_workspace = st.radio(
    "Workspace",
    DESKTOP_WORKSPACE_TABS,
    index=DESKTOP_WORKSPACE_TABS.index(st.session_state.get("active_workspace", "Planner")),
    horizontal=True,
    label_visibility="collapsed",
)
if current_workspace != st.session_state.get("active_workspace"):
    set_active_workspace(current_workspace)
if current_workspace == "Planner":
    render_planner_workspace(active_profile)
elif current_workspace == "Recipes":
    render_recipes_workspace(active_profile)
elif current_workspace == "Inventory":
    render_inventory_workspace(active_profile)
elif current_workspace == "Home Supplies":
    render_home_supplies_workspace(active_profile)
elif current_workspace == "Shopping":
    render_shopping_workspace(active_profile)
elif current_workspace == "Insights":
    render_insights_workspace(active_profile)
else:
    render_setup_workspace(active_profile)

pending_anchor = st.session_state.pop("jump_anchor", "")
if pending_anchor:
    components.html(
        f"""
        <script>
        const anchorId = {json.dumps(pending_anchor)};
        const scrollToSection = () => {{
          const doc = window.parent.document;
          const target = doc.getElementById(anchorId);
          if (!target) return;
          const top = target.getBoundingClientRect().top + window.parent.scrollY - 72;
          window.parent.scrollTo({{ top, behavior: "smooth" }});
        }};
        requestAnimationFrame(() => setTimeout(scrollToSection, 60));
        </script>
        """,
        height=0,
    )

if sync_profile_state(active_profile):
    persist_active_profile(active_profile)
