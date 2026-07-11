import base64
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


def asset_data_uri(path):
    asset_path = Path(path)
    if not asset_path.exists():
        return "none"
    encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
    suffix = asset_path.suffix.lower().lstrip(".") or "png"
    mime = "image/png" if suffix == "png" else f"image/{suffix}"
    return f"data:{mime};base64,{encoded}"


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
        "purchase_log_rows": [],
        "kitchen_inventory_rows": [],
        "household_inventory_rows": [],
        "shopping_manual_rows": [],
        "simple_item_memory": {"categories": {}, "vendors": {}},
        "simple_shopping_overrides": {},
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
    normalized["purchase_log_rows"] = list(profile.get("purchase_log_rows", []))
    normalized["kitchen_inventory_rows"] = list(profile.get("kitchen_inventory_rows", []))
    normalized["household_inventory_rows"] = list(profile.get("household_inventory_rows", []))
    normalized["shopping_manual_rows"] = list(profile.get("shopping_manual_rows", []))
    memory = profile.get("simple_item_memory", {})
    normalized["simple_item_memory"] = {
        "categories": dict(memory.get("categories", {})),
        "vendors": dict(memory.get("vendors", {})),
    }
    normalized["simple_shopping_overrides"] = dict(profile.get("simple_shopping_overrides", {}))
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
    normalized["purchase_log_rows"] = [simple_normalize_purchase_row(item) for item in normalized.get("purchase_log_rows", [])]
    normalized["kitchen_inventory_rows"] = [simple_normalize_inventory_row(item) for item in normalized.get("kitchen_inventory_rows", [])]
    normalized["household_inventory_rows"] = [simple_normalize_inventory_row(item) for item in normalized.get("household_inventory_rows", [])]
    normalized["shopping_manual_rows"] = [simple_normalize_shopping_manual_row(item) for item in normalized.get("shopping_manual_rows", [])]
    if not normalized["purchase_log_rows"] and normalized["inventory"]:
        normalized["purchase_log_rows"] = simple_seed_purchase_rows(normalized)
    if not normalized["kitchen_inventory_rows"] and normalized["inventory"]:
        normalized["kitchen_inventory_rows"] = simple_seed_inventory_rows(normalized, household=False)
    if not normalized["household_inventory_rows"] and normalized["inventory"]:
        normalized["household_inventory_rows"] = simple_seed_inventory_rows(normalized, household=True)
    simple_refresh_item_memory(normalized)
    simple_sync_rows_from_memory(normalized)
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


DESKTOP_WORKSPACE_TABS = ["Planner", "Recipes", "Purchase Log", "Inventory", "Shopping", "Insights"]
WORKSPACE_LABELS = {
    "Planner": "Meal planner",
    "Recipes": "Recipes",
    "Purchase Log": "Purchase Log",
    "Inventory": "Inventory",
    "Shopping": "Shopping List",
    "Insights": "Insights",
}
PLANNER_NAV_WORKSPACES = ["Planner", "Recipes", "Purchase Log", "Inventory", "Shopping", "Insights"]
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


def render_sidebar_nav_button(workspace):
    label = WORKSPACE_LABELS.get(workspace, workspace)
    if st.session_state.get("active_workspace") == workspace:
        st.markdown(f"<div class='sidebar-nav-active'>{label}</div>", unsafe_allow_html=True)
        return False
    return st.button(label, use_container_width=True, key=f"nav_{workspace}")


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
    page_background = asset_data_uri("assets/pichwai-page-bg-optimized.jpg")
    sidebar_background = asset_data_uri("assets/pichwai-sidebar-bg-optimized.jpg")
    header_background = asset_data_uri("assets/mandala-ribbon.jpg")
    button_background = asset_data_uri("assets/mandala-button.jpg")
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
            --color-bg: #121821;
            --color-bg-soft: #171F2B;
            --color-surface: #202837;
            --color-panel: #182130;
            --color-elevated: #273142;
            --color-primary: #C0644F;
            --color-primary-hover: #D17660;
            --color-secondary: #7F9CC4;
            --color-accent-brass: #C49A5A;
            --color-sandstone: #A96F56;
            --color-red-sandstone: #C0644F;
            --color-banana-leaf: #9DAF7A;
            --color-banana-leaf-strong: #6F8756;
            --color-leaf-soft: #7F8F68;
            --color-deep-leaf-shadow: #2E3F34;
            --color-lotus-muted: #D09A9A;
            --color-peacock-teal: #5FA4A5;
            --color-diya-flame: #D49A59;
            --color-text-primary: #F3EBDD;
            --color-text-secondary: #B9AB99;
            --color-border: #3A332B;
            --soft-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
            --page-overlay: rgba(18, 24, 33, 0.76);
            --sidebar-overlay: rgba(24, 33, 48, 0.76);
            --header-overlay: rgba(18, 24, 33, 0.72);
            --motif-page: none;
            --motif-sidebar: none;
            --motif-card: none;
            --motif-empty: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='280' height='280' viewBox='0 0 280 280'%3E%3Cg fill='none' stroke='%235FA4A5' stroke-opacity='.12' stroke-width='1.2'%3E%3Cpath d='M140 38c18 28 28 56 28 82 0 34-18 68-28 86-10-18-28-52-28-86 0-26 10-54 28-82Z'/%3E%3Cpath d='M140 58c26 8 48 26 64 54'/%3E%3C/g%3E%3Cg fill='none' stroke='%23D49A59' stroke-opacity='.12' stroke-width='1'%3E%3Cpath d='M76 210c18-14 38-22 64-22s46 8 64 22'/%3E%3C/g%3E%3C/svg%3E");
            --button-mandala: none;
            --button-inset: inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.08);
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --color-bg: #121821;
                --color-bg-soft: #171F2B;
                --color-surface: #202837;
                --color-panel: #182130;
                --color-elevated: #273142;
                --color-primary: #C0644F;
                --color-primary-hover: #D17660;
                --color-secondary: #7F9CC4;
                --color-accent-brass: #C49A5A;
                --color-sandstone: #A96F56;
                --color-red-sandstone: #C0644F;
                --color-banana-leaf: #9DAF7A;
                --color-banana-leaf-strong: #6F8756;
                --color-leaf-soft: #7F8F68;
                --color-deep-leaf-shadow: #2E3F34;
                --color-lotus-muted: #D09A9A;
                --color-peacock-teal: #5FA4A5;
                --color-diya-flame: #D49A59;
                --color-text-primary: #F3EBDD;
                --color-text-secondary: #B9AB99;
                --color-border: #3A332B;
                --soft-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
                --page-overlay: rgba(18, 24, 33, 0.76);
                --sidebar-overlay: rgba(24, 33, 48, 0.76);
                --header-overlay: rgba(18, 24, 33, 0.72);
                --motif-page: none;
                --motif-sidebar: none;
                --motif-card: none;
                --motif-empty: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='280' height='280' viewBox='0 0 280 280'%3E%3Cg fill='none' stroke='%235FA4A5' stroke-opacity='.12' stroke-width='1.2'%3E%3Cpath d='M140 38c18 28 28 56 28 82 0 34-18 68-28 86-10-18-28-52-28-86 0-26 10-54 28-82Z'/%3E%3Cpath d='M140 58c26 8 48 26 64 54'/%3E%3C/g%3E%3Cg fill='none' stroke='%23D49A59' stroke-opacity='.12' stroke-width='1'%3E%3Cpath d='M76 210c18-14 38-22 64-22s46 8 64 22'/%3E%3C/g%3E%3C/svg%3E");
                --button-mandala: none;
                --button-inset: inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.08);
            }
        }
        html {
            scroll-behavior: smooth;
        }
        [data-testid="stHeader"] {
            background: transparent;
            border-bottom: 1px solid rgba(184, 138, 68, 0.24);
            overflow: hidden;
        }
        [data-testid="stHeader"]::before {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            box-shadow: inset 0 -16px 24px rgba(0, 0, 0, 0.06);
        }
        [data-testid="stDecoration"] {
            display: none;
        }
        [data-testid="stToolbar"] {
            background: transparent;
        }
        .stApp {
            color: var(--color-text-primary);
            background-color: var(--color-bg);
            background-image: linear-gradient(var(--page-overlay), var(--page-overlay)), var(--motif-page);
            background-repeat: no-repeat;
            background-size: cover;
            background-position: center top;
            background-attachment: fixed;
        }
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2.3rem;
            max-width: 1480px;
        }
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-bottom: 2rem;
            }
        }
        .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--color-text-primary);
            margin: 1rem 0 0.55rem;
        }
        .library-note {
            padding: 0.7rem 0.9rem;
            border-radius: 12px;
            background: var(--color-surface);
            border: 1px solid var(--color-border);
        }
        .recipe-anchor {
            display: block;
            scroll-margin-top: 5rem;
        }
        .inventory-anchor {
            display: block;
            scroll-margin-top: 5.2rem;
        }
        [data-testid="stSidebar"] {
            background-color: var(--color-panel);
            background-image: linear-gradient(var(--sidebar-overlay), var(--sidebar-overlay)), var(--motif-sidebar);
            background-repeat: no-repeat;
            background-position: center top;
            background-size: cover;
            border-right: 1px solid var(--color-border);
        }
        [data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1.1rem;
            padding-bottom: 1.2rem;
        }
        [data-testid="stSidebar"] .stButton button {
            width: 100%;
            justify-content: flex-start;
            background: transparent;
            color: var(--color-text-secondary);
            border: 1px solid rgba(0, 0, 0, 0);
            border-radius: 14px;
            box-shadow: none;
            padding: 0.78rem 0.95rem 0.78rem 1rem;
            font-weight: 500;
            letter-spacing: 0.01em;
            position: relative;
        }
        [data-testid="stSidebar"] .stButton button::before {
            content: "";
            position: absolute;
            left: 0.9rem;
            right: 0.9rem;
            top: 0.3rem;
            height: 1px;
            background: rgba(184, 138, 68, 0.16);
            opacity: 0.7;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background: color-mix(in srgb, var(--color-surface) 62%, transparent 38%);
            color: var(--color-text-primary);
            border-color: rgba(184, 138, 68, 0.14);
            transform: none;
        }
        [data-testid="stSidebar"] .stExpander {
            background: transparent;
            border: none;
            box-shadow: none;
        }
        [data-testid="stSidebar"] .stExpander summary {
            border-radius: 14px;
            padding: 0.2rem 0;
        }
        .sidebar-brand {
            padding: 0.55rem 0.35rem 1rem;
            border-bottom: 1px solid rgba(184, 138, 68, 0.32);
            margin-bottom: 1rem;
            background: color-mix(in srgb, var(--color-surface) 70%, transparent 30%);
            border-radius: 18px;
            box-shadow: inset 0 0 0 1px rgba(184, 138, 68, 0.08);
        }
        .sidebar-brand .brand-art {
            display: block;
            width: 100%;
            height: auto;
            border-radius: 14px;
        }
        .gate-title-wrap {
            display: flex;
            justify-content: center;
            margin-bottom: 0.5rem;
        }
        .gate-title-art {
            width: min(100%, 760px);
            height: auto;
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(77, 54, 37, 0.08);
        }
        .sidebar-user-frame {
            margin-top: 1rem;
            padding: 0.95rem;
            border: 1px solid var(--color-border);
            border-radius: 20px;
            background-color: var(--color-surface);
            box-shadow: var(--soft-shadow);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: 20px;
            box-shadow: var(--soft-shadow);
            padding: 0.22rem;
            margin-bottom: 1rem;
        }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp p, .stApp li, .stApp label, .stApp div, .stApp span,
        .stApp [data-baseweb="select"] *, .stApp [data-baseweb="tab"] * {
            color: var(--color-text-primary);
        }
        .stApp a {
            color: var(--color-secondary);
            text-decoration-color: var(--color-secondary);
        }
        .stApp .stTabs button[role="tab"] {
            color: var(--color-text-secondary);
            background: transparent;
            font-weight: 600;
            border-radius: 999px;
            padding-inline: 0.8rem;
        }
        .stApp .stTabs button[aria-selected="true"] {
            color: var(--color-primary);
            background: var(--color-elevated);
            box-shadow: inset 0 0 0 1px rgba(184, 138, 68, 0.2);
        }
        .stApp .stButton button {
            font-weight: 600;
            color: var(--color-surface) !important;
            background-color: var(--color-primary) !important;
            background-image: linear-gradient(rgba(192, 100, 79, 0.96), rgba(192, 100, 79, 0.96)), var(--button-mandala) !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-size: cover !important;
            border: 1px solid var(--color-primary) !important;
            border-radius: 15px;
            box-shadow: var(--button-inset), 0 4px 10px rgba(192, 100, 79, 0.14);
            transition: transform 0.18s ease, background-color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
            clip-path: polygon(0 7%, 6% 0, 94% 0, 100% 7%, 100% 100%, 0 100%);
        }
        .stApp .stButton button:hover {
            background-color: var(--color-primary-hover) !important;
            background-image: linear-gradient(rgba(209, 118, 96, 0.97), rgba(209, 118, 96, 0.97)), var(--button-mandala) !important;
            border-color: var(--color-primary-hover) !important;
            color: var(--color-surface) !important;
            transform: translateY(-1px);
            box-shadow: var(--button-inset), 0 6px 12px rgba(192, 100, 79, 0.18);
        }
        .stApp .stButton button[kind="secondary"] {
            background-color: var(--color-banana-leaf-strong) !important;
            background-image: linear-gradient(rgba(78, 100, 55, 0.95), rgba(78, 100, 55, 0.95)), var(--button-mandala) !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-size: cover !important;
            color: var(--color-surface) !important;
            border: 1px solid color-mix(in srgb, var(--color-banana-leaf-strong) 72%, black 28%) !important;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
        }
        .stApp .stButton button[kind="secondary"]:hover {
            background-color: color-mix(in srgb, var(--color-banana-leaf-strong) 88%, black 12%) !important;
            background-image: linear-gradient(rgba(63, 84, 44, 0.97), rgba(63, 84, 44, 0.97)), var(--button-mandala) !important;
            border-color: color-mix(in srgb, var(--color-banana-leaf-strong) 60%, black 40%) !important;
            color: var(--color-surface) !important;
        }
        .stApp [data-baseweb="select"] > div,
        .stApp [data-baseweb="base-input"] > div,
        .stApp .stTextInput input,
        .stApp .stNumberInput input,
        .stApp .stDateInput input,
        .stApp textarea,
        .stApp [data-testid="stTextArea"] textarea {
            color: var(--color-text-primary);
            background: var(--color-elevated) !important;
            border-color: var(--color-border) !important;
            box-shadow: none !important;
        }
        .stApp [data-baseweb="base-input"] > div,
        .stApp [data-baseweb="select"] > div {
            background-color: var(--color-elevated) !important;
            border-color: var(--color-border) !important;
        }
        .stApp [data-baseweb="select"] svg,
        .stApp .stExpander svg {
            fill: var(--color-text-secondary);
        }
        .stApp [data-testid="stForm"] {
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: 18px;
            padding: 0.5rem 0.65rem 0.2rem;
        }
        .stApp [data-testid="stDataEditor"],
        .stApp [data-testid="stDataFrame"] {
            background: var(--color-surface) !important;
            border: 1px solid var(--color-border) !important;
            border-radius: 18px !important;
            box-shadow: var(--soft-shadow);
        }
        .stApp [data-testid="stDataEditor"] [role="grid"],
        .stApp [data-testid="stDataFrame"] [role="grid"] {
            background: var(--color-surface) !important;
            color: var(--color-text-primary) !important;
        }
        .stApp [data-testid="stDataEditor"] input,
        .stApp [data-testid="stDataEditor"] textarea,
        .stApp [data-testid="stDataEditor"] select,
        .stApp [data-testid="stDataEditor"] [contenteditable="true"] {
            background: var(--color-elevated) !important;
            color: var(--color-text-primary) !important;
            border-color: var(--color-border) !important;
        }
        .stApp [data-testid="stDataEditor"] button,
        .stApp [data-testid="stDataFrame"] button {
            color: var(--color-text-primary) !important;
        }
        .stApp [data-testid="stDataEditor"] div,
        .stApp [data-testid="stDataFrame"] div {
            border-color: color-mix(in srgb, var(--color-border) 78%, transparent 22%) !important;
        }
        .stApp .stExpander {
            border: 1px solid var(--color-border);
            border-radius: 16px;
            background: var(--color-elevated);
        }
        .stApp .stExpander summary,
        .stApp .stExpander summary p {
            color: var(--color-text-primary);
            font-weight: 600;
        }
        .stApp [data-testid="stDataFrame"],
        .stApp [data-testid="stDataFrame"] * {
            color: var(--color-text-primary);
        }
        .stApp .stAlert,
        .stApp .stAlert * {
            color: var(--color-text-primary);
        }
        .sidebar-nav-active {
            width: 100%;
            padding: 0.76rem 0.95rem;
            margin: 0.15rem 0 0.35rem;
            border-radius: 14px;
            background: color-mix(in srgb, var(--color-surface) 88%, var(--color-panel) 12%);
            color: var(--color-primary);
            font-weight: 700;
            border: 1px solid rgba(184, 138, 68, 0.14);
            border-left: 4px solid var(--color-primary);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
        }
        .sidebar-nav-active::before {
            content: "";
            display: block;
            height: 1px;
            margin-bottom: 0.25rem;
            background: rgba(184, 138, 68, 0.18);
        }
        .today-hero-copy {
            margin-bottom: 1rem;
            padding: 0.2rem 0 0.35rem;
        }
        .today-hero-copy .hero-title {
            font-size: 1.55rem;
            font-weight: 700;
            color: var(--color-text-primary);
            margin-bottom: 0.25rem;
        }
        .today-hero-copy .hero-kicker {
            font-size: 1rem;
            line-height: 1.45;
            color: var(--color-primary);
            margin-bottom: 0.22rem;
        }
        .today-hero-copy .hero-subtitle {
            color: var(--color-text-secondary);
            line-height: 1.55;
            max-width: 40rem;
        }
        .today-planner-shell {
            position: relative;
            padding: 0.25rem;
        }
        .today-planner-shell::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 22px;
            background: linear-gradient(rgba(255, 249, 239, 0.78), rgba(255, 249, 239, 0.78));
            opacity: 0.16;
            pointer-events: none;
        }
        .today-planner-shell > * {
            position: relative;
            z-index: 1;
        }
        .stApp [data-testid="stAlertContainer"] > div {
            background-image: var(--motif-empty);
            background-repeat: no-repeat;
            background-position: right -30px center;
            background-size: 140px 140px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <style>
        :root {{
            --motif-page: url("{page_background}");
            --motif-sidebar: url("{sidebar_background}");
            --header-ribbon: url("{header_background}");
            --button-mandala: url("{button_background}");
        }}
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
    title_art = asset_data_uri("assets/griha-prabandh-title.webp")
    st.markdown(
        f"""
        <div class="gate-title-wrap">
          <img class="gate-title-art" src="{title_art}" alt="गृह प्रबंध" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("Enter your user ID to open गृह प्रबंध.")
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


def render_planner_intro():
    st.markdown(
        """
        <div class="today-hero-copy">
          <div class="hero-kicker">घर, भोजन और आवश्यकताओं का प्रबंध</div>
          <div class="hero-title">Meal planner</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
                    "category": simple_category_for_item(profile, item["name"], category_name(profile, item.get("category_id", ""))),
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
    rows = []
    for item in profile.get("inventory", []):
        lowered = item.get("name", "").lower()
        matched_season = next((label for label, names in SEASONAL_ITEMS.items() if any(name in lowered for name in names)), "")
        if not matched_season:
            continue
        waste_rows = waste_transactions_for_item(profile, item)
        reason = "Relevant from purchase history."
        if waste_rows:
            reason += " Past waste suggests buying a little less."
        rows.append(
            {
                "Item": item["name"],
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
    st.markdown("## Preferences")
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


SIMPLE_PURCHASE_COLUMNS = OrderedDict(
    [
        ("in_stock", "In Stock"),
        ("date_time", "Date/Time"),
        ("vendor", "Vendor"),
        ("item", "Item"),
        ("quantity", "Quantity"),
        ("price", "Price"),
        ("note", "Note"),
        ("category", "Category"),
    ]
)
SIMPLE_PURCHASE_REVIEW_COLUMNS = OrderedDict(
    [
        ("item", "Item"),
        ("vendor", "Vendor"),
        ("quantity", "Quantity"),
        ("price", "Price"),
        ("note", "Note"),
        ("category", "Category"),
    ]
)
SIMPLE_INVENTORY_COLUMNS = OrderedDict(
    [
        ("in_stock", "In Stock"),
        ("item", "Item"),
        ("quantity", "Quantity"),
        ("vendor", "Vendor"),
        ("note", "Note"),
        ("category", "Category"),
    ]
)
SIMPLE_SHOPPING_COLUMNS = OrderedDict(
    [
        ("purchased", "Purchased"),
        ("vendor", "Vendor"),
        ("item", "Item"),
        ("quantity", "Quantity & Unit"),
        ("category", "Category"),
        ("note", "Note"),
        ("source", "Source"),
    ]
)


def simple_memory_key(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower()).strip()


def simple_clean_text(value):
    return str(value or "").strip()


def simple_clean_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value in {1, "1", "true", "True", "yes", "Yes"}:
        return True
    if value in {0, "0", "false", "False", "no", "No"}:
        return False
    return default


def simple_vendor_pool(profile):
    values = []
    for key in ["purchase_log_rows", "kitchen_inventory_rows", "household_inventory_rows", "shopping_manual_rows"]:
        for row in profile.get(key, []):
            values.append(row.get("vendor", ""))
    values.extend(profile.get("simple_item_memory", {}).get("vendors", {}).values())
    dedup = []
    seen = set()
    for value in values:
        canonical = simple_memory_key(value).replace(" ", "")
        cleaned = simple_clean_text(value)
        if not cleaned or not canonical or canonical in seen:
            continue
        seen.add(canonical)
        dedup.append(cleaned)
    return dedup


def simple_canonical_vendor(profile, vendor_name):
    cleaned = simple_clean_text(vendor_name)
    if not cleaned:
        return ""
    vendor_key = simple_memory_key(cleaned).replace(" ", "")
    for existing in simple_vendor_pool(profile):
        if simple_memory_key(existing).replace(" ", "") == vendor_key:
            return existing
    return cleaned


def simple_remembered_category(profile, item_name):
    return profile.get("simple_item_memory", {}).get("categories", {}).get(simple_memory_key(item_name), "")


def simple_remembered_vendor(profile, item_name):
    return profile.get("simple_item_memory", {}).get("vendors", {}).get(simple_memory_key(item_name), "")


def simple_category_for_item(profile, item_name, fallback=""):
    return simple_remembered_category(profile, item_name) or simple_clean_text(fallback)


def simple_apply_memory(profile, row):
    updated = dict(row)
    item_name = updated.get("item", "")
    if item_name and not updated.get("category"):
        updated["category"] = simple_remembered_category(profile, item_name)
    if item_name and not updated.get("vendor"):
        updated["vendor"] = simple_remembered_vendor(profile, item_name)
    if updated.get("vendor"):
        updated["vendor"] = simple_canonical_vendor(profile, updated["vendor"])
    return updated


def simple_refresh_item_memory(profile):
    memory = profile.setdefault("simple_item_memory", {"categories": {}, "vendors": {}})
    categories = {}
    vendors = {}
    for key in ["purchase_log_rows", "kitchen_inventory_rows", "household_inventory_rows", "shopping_manual_rows"]:
        for row in profile.get(key, []):
            item_name = simple_clean_text(row.get("item", ""))
            if not item_name:
                continue
            item_key = simple_memory_key(item_name)
            category = simple_clean_text(row.get("category", ""))
            vendor = simple_clean_text(row.get("vendor", ""))
            if category:
                categories[item_key] = category
            if vendor:
                vendors[item_key] = simple_canonical_vendor(profile, vendor)
    memory["categories"] = categories
    memory["vendors"] = vendors


def simple_sync_rows_from_memory(profile):
    for key in ["purchase_log_rows", "kitchen_inventory_rows", "household_inventory_rows", "shopping_manual_rows"]:
        synced_rows = []
        for row in profile.get(key, []):
            synced_rows.append(simple_apply_memory(profile, row))
        profile[key] = synced_rows


def simple_normalize_purchase_row(row):
    row = dict(row) if isinstance(row, dict) else {}
    return {
        "id": row.get("id", uuid4().hex),
        "in_stock": simple_clean_bool(row.get("in_stock"), True),
        "date_time": simple_clean_text(row.get("date_time")) or datetime.now().isoformat(timespec="minutes").replace("T", " "),
        "vendor": simple_clean_text(row.get("vendor")),
        "item": simple_clean_text(row.get("item")),
        "quantity": simple_clean_text(row.get("quantity")),
        "price": simple_clean_text(row.get("price")),
        "note": simple_clean_text(row.get("note")),
        "category": simple_clean_text(row.get("category")),
    }


def simple_normalize_inventory_row(row):
    row = dict(row) if isinstance(row, dict) else {}
    return {
        "id": row.get("id", uuid4().hex),
        "in_stock": simple_clean_bool(row.get("in_stock"), True),
        "item": simple_clean_text(row.get("item")),
        "quantity": simple_clean_text(row.get("quantity")),
        "vendor": simple_clean_text(row.get("vendor")),
        "note": simple_clean_text(row.get("note")),
        "category": simple_clean_text(row.get("category")),
    }


def simple_normalize_shopping_manual_row(row):
    row = dict(row) if isinstance(row, dict) else {}
    return {
        "id": row.get("id", uuid4().hex),
        "vendor": simple_clean_text(row.get("vendor")),
        "item": simple_clean_text(row.get("item")),
        "quantity": simple_clean_text(row.get("quantity")),
        "category": simple_clean_text(row.get("category")),
        "note": simple_clean_text(row.get("note")),
    }


def simple_seed_inventory_rows(profile, household=False):
    rows = []
    for item in profile.get("inventory", []):
        if is_home_supply_item(profile, item) != household:
            continue
        quantity_text = " ".join(part for part in [format_number(inventory_total_quantity(item)), item.get("unit", "")] if part).strip()
        rows.append(
            simple_normalize_inventory_row(
                {
                    "item": item.get("name", ""),
                    "quantity": quantity_text,
                    "vendor": item.get("preferred_vendor", ""),
                    "note": item.get("notes", ""),
                    "category": category_name(profile, item.get("category_id", "")),
                    "in_stock": inventory_total_quantity(item) > 0,
                }
            )
        )
    return rows


def simple_seed_purchase_rows(profile):
    rows = []
    for item in profile.get("inventory", []):
        category = category_name(profile, item.get("category_id", ""))
        for lot in item.get("lots", []):
            purchase_date = simple_clean_text(lot.get("purchase_date", "")) or simple_clean_text(item.get("purchase_date", ""))
            if not purchase_date and lot.get("price") in {None, ""}:
                continue
            rows.append(
                simple_normalize_purchase_row(
                    {
                        "date_time": purchase_date,
                        "vendor": lot.get("vendor", "") or item.get("preferred_vendor", ""),
                        "item": item.get("name", ""),
                        "quantity": " ".join(part for part in [format_number(lot.get("quantity")), lot.get("unit", "")] if part).strip(),
                        "price": format_number(lot.get("price")),
                        "note": lot.get("notes", ""),
                        "category": category,
                        "in_stock": lot.get("status", "sealed") not in {"finished", "expired"},
                    }
                )
            )
    rows.sort(key=lambda row: row.get("date_time", ""), reverse=True)
    return rows


def simple_blank_row(columns):
    row = {"id": uuid4().hex}
    for key in columns:
        row[key] = False if key in {"in_stock", "purchased"} else ""
    return row


def simple_is_meaningful_row(row, kind):
    groups = {
        "purchase": ["item", "vendor", "quantity", "price", "note", "category"],
        "inventory": ["item", "quantity", "vendor", "note", "category"],
        "shopping": ["item", "vendor", "quantity", "category", "note"],
    }
    return any(simple_clean_text(row.get(key, "")) for key in groups[kind])


def simple_sort_value(value):
    text = simple_clean_text(value)
    try:
        return float(text)
    except ValueError:
        return text.lower()


def simple_filter_and_sort_rows(rows, search, vendor_filter, category_filter, sort_key, descending, visible_keys):
    filtered = []
    search_text = simple_clean_text(search).lower()
    for row in rows:
        vendor = simple_clean_text(row.get("vendor", ""))
        category = simple_clean_text(row.get("category", ""))
        if vendor_filter and vendor not in vendor_filter:
            continue
        if category_filter and category not in category_filter:
            continue
        if search_text:
            haystack = " ".join(simple_clean_text(row.get(key, "")) for key in visible_keys).lower()
            if search_text not in haystack:
                continue
        filtered.append(row)
    filtered.sort(key=lambda row: simple_sort_value(row.get(sort_key, "")), reverse=descending)
    return filtered


def simple_table_controls(rows, prefix, visible_keys, default_sort_key):
    vendors = sorted({simple_clean_text(row.get("vendor", "")) for row in rows if simple_clean_text(row.get("vendor", ""))})
    categories = sorted({simple_clean_text(row.get("category", "")) for row in rows if simple_clean_text(row.get("category", ""))})
    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([2.2, 1.2, 1.2, 1, 1])
    search = ctrl1.text_input("Search", key=f"{prefix}_search")
    vendor_filter = ctrl2.multiselect("Vendor", vendors, key=f"{prefix}_vendors")
    category_filter = ctrl3.multiselect("Category", categories, key=f"{prefix}_categories")
    sort_key = ctrl4.selectbox(
        "Sort by",
        visible_keys,
        index=visible_keys.index(default_sort_key) if default_sort_key in visible_keys else 0,
        format_func=lambda value: value.replace("_", " ").title(),
        key=f"{prefix}_sort",
    )
    descending = ctrl5.selectbox("Order", ["A-Z", "Z-A"], key=f"{prefix}_order") == "Z-A"
    return search, vendor_filter, category_filter, sort_key, descending


def simple_editor_frame(rows, column_map):
    records = []
    for row in rows:
        record = {"_id": row.get("id", "")}
        for key, label in column_map.items():
            record[label] = row.get(key, False if key in {"in_stock", "purchased"} else "")
        records.append(record)
    return pd.DataFrame(records)


def simple_column_config(column_map):
    config = {"_id": None}
    for key, label in column_map.items():
        if key in {"in_stock", "purchased"}:
            config[label] = st.column_config.CheckboxColumn(label)
        else:
            config[label] = st.column_config.TextColumn(label)
    return config


def simple_merge_editor_rows(profile, all_rows, filtered_ids, edited_df, column_map, normalize_fn, row_kind):
    edited_rows = []
    for record in edited_df.to_dict("records"):
        raw = {"id": record.get("_id") or uuid4().hex}
        for key, label in column_map.items():
            raw[key] = record.get(label)
        normalized = simple_apply_memory(profile, normalize_fn(raw))
        if simple_is_meaningful_row(normalized, row_kind):
            edited_rows.append(normalized)
    untouched = [normalize_fn(row) for row in all_rows if row.get("id") not in filtered_ids]
    return untouched + edited_rows


def simple_render_editable_table(profile, rows_key, column_map, normalize_fn, row_kind, prefix, default_sort_key="item"):
    rows = [simple_apply_memory(profile, normalize_fn(row)) for row in profile.get(rows_key, [])]
    visible_keys = [key for key in column_map if key not in {"in_stock", "purchased"}]
    search, vendor_filter, category_filter, sort_key, descending = simple_table_controls(rows, prefix, visible_keys, default_sort_key)
    filtered_rows = simple_filter_and_sort_rows(rows, search, vendor_filter, category_filter, sort_key, descending, visible_keys)
    if not filtered_rows:
        filtered_rows = [simple_blank_row(column_map.keys())]
    editor_df = simple_editor_frame(filtered_rows, column_map)
    edited_df = st.data_editor(
        editor_df,
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        column_config=simple_column_config(column_map),
        key=f"{prefix}_editor",
    )
    merged_rows = simple_merge_editor_rows(profile, rows, {row.get("id") for row in filtered_rows if row.get("id")}, edited_df, column_map, normalize_fn, row_kind)
    if json.dumps(rows, sort_keys=True) != json.dumps(merged_rows, sort_keys=True):
        profile[rows_key] = merged_rows
        simple_refresh_item_memory(profile)
        simple_sync_rows_from_memory(profile)
        persist_active_profile(profile)
        st.rerun()
    return merged_rows


def simple_parse_purchase_line(profile, raw_text):
    text = simple_clean_text(raw_text)
    if not text:
        return []
    vendor = ""
    body = text
    if ":" in text:
        vendor, body = [part.strip() for part in text.split(":", 1)]
    else:
        match = re.match(r"(.+?)\s+se\s+(.+)", text, flags=re.IGNORECASE)
        if match:
            vendor = match.group(1).strip()
            body = match.group(2).strip()
    vendor = simple_canonical_vendor(profile, vendor)
    rows = []
    for part in [chunk.strip(" .") for chunk in re.split(r",|\n", body) if chunk.strip()]:
        item = simple_clean_text(part)
        quantity = ""
        price = ""
        match = re.match(
            r"(?P<item>.+?)\s+(?P<qty>\d+(?:\.\d+)?(?:\s*x\s*\d+(?:\.\d+)?)?\s*(?:kg|g|gm|gram|grams|litre|liter|l|ml|pack|packs|packet|packets|pc|pcs|piece|pieces|bottle|bottles|box|boxes)?)\s+(?P<price>\d+(?:\.\d+)?)$",
            part,
            flags=re.IGNORECASE,
        )
        if match:
            item = simple_clean_text(match.group("item"))
            quantity = simple_clean_text(match.group("qty"))
            price = simple_clean_text(match.group("price"))
        else:
            price_match = re.search(r"(\d+(?:\.\d+)?)$", part)
            if price_match:
                price = simple_clean_text(price_match.group(1))
                item = simple_clean_text(part[: price_match.start()])
            qty_match = re.search(
                r"(\d+(?:\.\d+)?(?:\s*x\s*\d+(?:\.\d+)?)?\s*(?:kg|g|gm|gram|grams|litre|liter|l|ml|pack|packs|packet|packets|pc|pcs|piece|pieces|bottle|bottles|box|boxes)?)",
                item,
                flags=re.IGNORECASE,
            )
            if qty_match:
                quantity = simple_clean_text(qty_match.group(1))
                item = simple_clean_text(item.replace(qty_match.group(1), "", 1))
        rows.append(
            {
                "item": item,
                "vendor": vendor,
                "quantity": quantity,
                "price": price,
                "note": "",
                "category": simple_remembered_category(profile, item),
            }
        )
    return [row for row in rows if row.get("item")]


def simple_meal_planner_rows(profile):
    rows = []
    for item_name, quantity in profile.get("grocery_data", {}).get("missing_items", {}).items():
        source_id = f"meal::{item_name}"
        state = profile.get("simple_shopping_overrides", {}).get(source_id, {})
        rows.append(
            {
                "id": source_id,
                "purchased": False,
                "vendor": state.get("vendor", ""),
                "item": item_name,
                "quantity": state.get("quantity", simple_clean_text(quantity)),
                "category": state.get("category", simple_remembered_category(profile, item_name)),
                "note": state.get("note", ""),
                "source": "Meal Planner",
            }
        )
    return rows


def simple_build_shopping_rows(profile):
    rows = []
    for bucket, label in [
        ("kitchen_inventory_rows", "Kitchen Inventory"),
        ("household_inventory_rows", "Household Items"),
        ("purchase_log_rows", "Purchase Log"),
    ]:
        for row in profile.get(bucket, []):
            if row.get("in_stock", True):
                continue
            rows.append(
                {
                    "id": f"{bucket}::{row['id']}",
                    "purchased": False,
                    "vendor": row.get("vendor", ""),
                    "item": row.get("item", ""),
                    "quantity": row.get("quantity", ""),
                    "category": row.get("category", ""),
                    "note": row.get("note", ""),
                    "source": label,
                }
            )
    for row in profile.get("shopping_manual_rows", []):
        rows.append({"id": f"manual::{row['id']}", "purchased": False, "vendor": row.get("vendor", ""), "item": row.get("item", ""), "quantity": row.get("quantity", ""), "category": row.get("category", ""), "note": row.get("note", ""), "source": "Manual"})
    rows.extend(simple_meal_planner_rows(profile))
    return [simple_apply_memory(profile, row) for row in rows if row.get("item")]


def simple_apply_shopping_row_change(profile, row):
    source_id = row.get("id", "")
    if source_id.startswith("kitchen_inventory_rows::"):
        target_id = source_id.split("::", 1)[1]
        for entry in profile.get("kitchen_inventory_rows", []):
            if entry["id"] == target_id:
                entry.update(simple_normalize_inventory_row({**entry, "item": row["item"], "quantity": row["quantity"], "vendor": row["vendor"], "note": row["note"], "category": row["category"], "in_stock": not row.get("purchased", False)}))
                return
    if source_id.startswith("household_inventory_rows::"):
        target_id = source_id.split("::", 1)[1]
        for entry in profile.get("household_inventory_rows", []):
            if entry["id"] == target_id:
                entry.update(simple_normalize_inventory_row({**entry, "item": row["item"], "quantity": row["quantity"], "vendor": row["vendor"], "note": row["note"], "category": row["category"], "in_stock": not row.get("purchased", False)}))
                return
    if source_id.startswith("purchase_log_rows::"):
        target_id = source_id.split("::", 1)[1]
        for entry in profile.get("purchase_log_rows", []):
            if entry["id"] == target_id:
                entry.update(simple_normalize_purchase_row({**entry, "item": row["item"], "quantity": row["quantity"], "vendor": row["vendor"], "note": row["note"], "category": row["category"], "in_stock": not row.get("purchased", False)}))
                return
    if source_id.startswith("manual::"):
        target_id = source_id.split("::", 1)[1]
        if row.get("purchased", False):
            profile["shopping_manual_rows"] = [entry for entry in profile.get("shopping_manual_rows", []) if entry["id"] != target_id]
        else:
            for entry in profile.get("shopping_manual_rows", []):
                if entry["id"] == target_id:
                    entry.update(simple_normalize_shopping_manual_row({**entry, "item": row["item"], "quantity": row["quantity"], "vendor": row["vendor"], "note": row["note"], "category": row["category"]}))
                    return
        return
    if source_id.startswith("meal::"):
        item_name = source_id.split("::", 1)[1]
        if row.get("purchased", False):
            profile.get("grocery_data", {}).get("missing_items", {}).pop(item_name, None)
            st.session_state.get("grocery_list", OrderedDict()).pop(item_name, None)
        else:
            profile.setdefault("simple_shopping_overrides", {})[source_id] = {
                "vendor": row.get("vendor", ""),
                "quantity": row.get("quantity", ""),
                "category": row.get("category", ""),
                "note": row.get("note", ""),
            }


def simple_table_header(title, jump_label="", jump_anchor=""):
    col1, col2 = st.columns([3.5, 1.9])
    col1.markdown(f"### {title}")
    if jump_label and jump_anchor:
        button_id = f"jump-{jump_anchor}-{recipe_slug(title)}"
        mandala_background = asset_data_uri("assets/mandala-button.jpg")
        with col2:
            components.html(
                f"""
                <div style="padding-top:0.15rem;">
                  <button
                    id="{button_id}"
                    style="
                      width:100%;
                      min-height:48px;
                      padding:0.62rem 0.9rem;
                      border-radius:15px;
                      border:1px solid rgba(59, 78, 39, 0.92);
                      background-image:linear-gradient(rgba(78, 100, 55, 0.95), rgba(78, 100, 55, 0.95)), url('{mandala_background}');
                      background-repeat:no-repeat;
                      background-position:center center;
                      background-size:cover;
                      color:#FFF9EF;
                      font-weight:600;
                      font-size:0.9rem;
                      line-height:1.2;
                      white-space:normal;
                      text-wrap:balance;
                      cursor:pointer;
                      box-shadow:inset 0 0 0 1px rgba(255,255,255,0.08), 0 4px 10px rgba(78, 100, 55, 0.12);
                      clip-path:polygon(0 7%, 6% 0, 94% 0, 100% 7%, 100% 100%, 0 100%);
                    "
                    onmouseover="this.style.transform='translateY(-1px)'; this.style.backgroundImage='linear-gradient(rgba(63, 84, 44, 0.97), rgba(63, 84, 44, 0.97)), url({json.dumps(mandala_background)})'; this.style.borderColor='rgba(47, 62, 33, 0.96)'; this.style.boxShadow='inset 0 0 0 1px rgba(255,255,255,0.08), 0 6px 12px rgba(78, 100, 55, 0.15)';"
                    onmouseout="this.style.transform='translateY(0)'; this.style.backgroundImage='linear-gradient(rgba(78, 100, 55, 0.95), rgba(78, 100, 55, 0.95)), url({json.dumps(mandala_background)})'; this.style.borderColor='rgba(59, 78, 39, 0.92)'; this.style.boxShadow='inset 0 0 0 1px rgba(255,255,255,0.08), 0 4px 10px rgba(78, 100, 55, 0.12)';"
                  >
                    {jump_label}
                  </button>
                </div>
                <script>
                  const btn = document.getElementById({json.dumps(button_id)});
                  if (btn) {{
                    btn.addEventListener("click", () => {{
                      const doc = window.parent.document;
                      const target = doc.getElementById({json.dumps(jump_anchor)});
                      if (!target) return;
                      target.scrollIntoView({{ behavior: "smooth", block: "start" }});
                      try {{
                        window.parent.history.replaceState(null, "", "#" + {json.dumps(jump_anchor)});
                      }} catch (e) {{}}
                    }});
                  }}
                </script>
                """,
                height=62,
            )


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
    st.markdown("## Inventory")
    st.markdown("<div id='kitchen-inventory' class='inventory-anchor'></div>", unsafe_allow_html=True)
    simple_table_header("Kitchen Inventory", "Go to Household Items", "household-items")
    simple_render_editable_table(
        profile,
        "kitchen_inventory_rows",
        SIMPLE_INVENTORY_COLUMNS,
        simple_normalize_inventory_row,
        "inventory",
        "kitchen_inventory",
    )
    st.divider()
    st.markdown("<div id='household-items' class='inventory-anchor'></div>", unsafe_allow_html=True)
    simple_table_header("Household Items", "Go to Kitchen Inventory", "kitchen-inventory")
    simple_render_editable_table(
        profile,
        "household_inventory_rows",
        SIMPLE_INVENTORY_COLUMNS,
        simple_normalize_inventory_row,
        "inventory",
        "household_inventory",
    )
    st.markdown("<div style='height: 45vh;'></div>", unsafe_allow_html=True)


def render_home_supplies_workspace(profile):
    render_inventory_workspace(profile)


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


def render_purchase_log_workspace(profile):
    st.markdown("## Purchase Log")
    st.markdown("**Log what I just bought**")
    st.text_area(
        "Log what I just bought",
        value=st.session_state.get("purchase_log_input_text", ""),
        height=120,
        label_visibility="collapsed",
        placeholder="Blinkit se doodh 2 litre 120, chawal 5kg 450, harpic 1 litre 180",
        key="purchase_log_input_text",
    )
    if st.button("Parse and review", type="primary", use_container_width=True):
        parsed_rows = []
        for line in [chunk for chunk in re.split(r"\n+", st.session_state.get("purchase_log_input_text", "")) if chunk.strip()]:
            parsed_rows.extend(simple_parse_purchase_line(profile, line))
        st.session_state.purchase_log_review_rows = parsed_rows or [simple_blank_row(SIMPLE_PURCHASE_REVIEW_COLUMNS.keys())]
        st.rerun()

    review_rows = st.session_state.get("purchase_log_review_rows", [])
    if review_rows:
        st.markdown("**Review before saving**")
        review_df = simple_editor_frame([{"id": row.get("id", uuid4().hex), **row} for row in review_rows], SIMPLE_PURCHASE_REVIEW_COLUMNS)
        edited_review = st.data_editor(
            review_df,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            column_config=simple_column_config(SIMPLE_PURCHASE_REVIEW_COLUMNS),
            key="purchase_log_review_editor",
        )
        updated_review = []
        for record in edited_review.to_dict("records"):
            raw = {"id": record.get("_id") or uuid4().hex}
            for key, label in SIMPLE_PURCHASE_REVIEW_COLUMNS.items():
                raw[key] = record.get(label)
            normalized = simple_apply_memory(profile, simple_normalize_purchase_row(raw))
            if simple_is_meaningful_row(normalized, "purchase"):
                updated_review.append(normalized)
        st.session_state.purchase_log_review_rows = updated_review
        if st.button("Save to purchase history", use_container_width=True):
            timestamp = datetime.now().isoformat(timespec="minutes").replace("T", " ")
            saved_rows = [simple_normalize_purchase_row({**row, "date_time": timestamp, "in_stock": True}) for row in updated_review]
            if saved_rows:
                profile["purchase_log_rows"] = saved_rows + profile.get("purchase_log_rows", [])
                simple_refresh_item_memory(profile)
                simple_sync_rows_from_memory(profile)
                persist_active_profile(profile)
                st.session_state.purchase_log_review_rows = []
                st.session_state.purchase_log_flash = f"Saved {len(saved_rows)} purchase entr{'y' if len(saved_rows) == 1 else 'ies'}."
                st.rerun()

    if st.session_state.get("purchase_log_flash"):
        st.success(st.session_state.pop("purchase_log_flash"))

    st.divider()
    simple_table_header("Purchase History")
    simple_render_editable_table(
        profile,
        "purchase_log_rows",
        SIMPLE_PURCHASE_COLUMNS,
        simple_normalize_purchase_row,
        "purchase",
        "purchase_history",
        default_sort_key="date_time",
    )


def render_shopping_workspace(profile):
    st.markdown("## Shopping List")
    before_state = json.dumps(
        {
            "purchase_log_rows": profile.get("purchase_log_rows", []),
            "kitchen_inventory_rows": profile.get("kitchen_inventory_rows", []),
            "household_inventory_rows": profile.get("household_inventory_rows", []),
            "shopping_manual_rows": profile.get("shopping_manual_rows", []),
            "simple_shopping_overrides": profile.get("simple_shopping_overrides", {}),
            "grocery_data": profile.get("grocery_data", {}),
        },
        sort_keys=True,
    )
    rows = simple_build_shopping_rows(profile)
    search, vendor_filter, category_filter, sort_key, descending = simple_table_controls(rows, "shopping_list", ["vendor", "item", "quantity", "category", "note", "source"], "vendor")
    filtered_rows = simple_filter_and_sort_rows(rows, search, vendor_filter, category_filter, sort_key, descending, ["vendor", "item", "quantity", "category", "note", "source"])
    if not filtered_rows:
        filtered_rows = [simple_blank_row(SIMPLE_SHOPPING_COLUMNS.keys())]
    editor_df = simple_editor_frame(filtered_rows, SIMPLE_SHOPPING_COLUMNS)
    edited_df = st.data_editor(
        editor_df,
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        column_config=simple_column_config(SIMPLE_SHOPPING_COLUMNS),
        disabled=["Source"],
        key="shopping_list_editor",
    )
    manual_filtered_ids = {row["id"].split("::", 1)[1] for row in filtered_rows if str(row.get("id", "")).startswith("manual::")}
    kept_manual_ids = set()
    purchased_count = 0
    for record in edited_df.to_dict("records"):
        row = {"id": record.get("_id") or f"manual::{uuid4().hex}"}
        for key, label in SIMPLE_SHOPPING_COLUMNS.items():
            row[key] = record.get(label)
        if not simple_is_meaningful_row(row, "shopping"):
            continue
        row["vendor"] = simple_canonical_vendor(profile, row.get("vendor", ""))
        row["category"] = row.get("category", "") or simple_remembered_category(profile, row.get("item", ""))
        if row["id"].startswith("manual::"):
            kept_manual_ids.add(row["id"].split("::", 1)[1])
            if not any(item["id"] == row["id"].split("::", 1)[1] for item in profile.get("shopping_manual_rows", [])):
                profile.setdefault("shopping_manual_rows", []).append(
                    simple_normalize_shopping_manual_row(
                        {
                            "id": row["id"].split("::", 1)[1],
                            "vendor": row.get("vendor", ""),
                            "item": row.get("item", ""),
                            "quantity": row.get("quantity", ""),
                            "category": row.get("category", ""),
                            "note": row.get("note", ""),
                        }
                    )
                )
        simple_apply_shopping_row_change(profile, row)
        if row.get("purchased", False):
            purchased_count += 1
    profile["shopping_manual_rows"] = [
        row for row in profile.get("shopping_manual_rows", []) if row["id"] not in (manual_filtered_ids - kept_manual_ids)
    ]
    simple_refresh_item_memory(profile)
    simple_sync_rows_from_memory(profile)
    after_state = json.dumps(
        {
            "purchase_log_rows": profile.get("purchase_log_rows", []),
            "kitchen_inventory_rows": profile.get("kitchen_inventory_rows", []),
            "household_inventory_rows": profile.get("household_inventory_rows", []),
            "shopping_manual_rows": profile.get("shopping_manual_rows", []),
            "simple_shopping_overrides": profile.get("simple_shopping_overrides", {}),
            "grocery_data": profile.get("grocery_data", {}),
        },
        sort_keys=True,
    )
    if before_state != after_state:
        persist_active_profile(profile)
    if purchased_count:
        st.success(f"Marked {purchased_count} item(s) purchased.")
        st.rerun()


def render_insights_workspace(profile):
    st.markdown("## Insights")
    total_signals = len(profile.get("inventory_transactions", [])) + sum(len(item.get("lots", [])) for item in profile.get("inventory", []))
    if total_signals < 6:
        with st.container(border=True):
            st.info("Insights will improve as you add purchases, deductions, and adjustments.")
            col1, col2, col3 = st.columns(3)
            if col1.button("Add Purchase", use_container_width=True, key=f"insights_add_purchase_{profile['id']}"):
                st.session_state.pending_workspace = "Purchase Log"
                st.rerun()
            if col2.button("Review Inventory", use_container_width=True, key=f"insights_inventory_{profile['id']}"):
                st.session_state.pending_workspace = "Inventory"
                st.rerun()
            if col3.button("Open Shopping", use_container_width=True, key=f"insights_shopping_{profile['id']}"):
                st.session_state.pending_workspace = "Shopping"
                st.rerun()

    consumption_tab, price_tab, vendor_tab, predictions_tab = st.tabs(
        ["Consumption", "Price Analysis", "Vendor Comparison", "Predictions"]
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
                    "Category": simple_category_for_item(profile, item["name"], category_name(profile, item.get("category_id", ""))),
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

    render_planner_intro()
    with st.container(border=True):
        st.markdown("<div id='planner-section'></div>", unsafe_allow_html=True)
        st.markdown("<div class='today-planner-shell'>", unsafe_allow_html=True)
        st.markdown("**Plan for your meal here**")
        action_left, action_right = st.columns(2)
        if action_left.button("Khane Mein Kya Khaye?", use_container_width=True, type="primary"):
            choose_random_meals(active_profile, brunch_options, dinner_options)
            st.rerun()
        if action_right.button("Note what I ate today", use_container_width=True, type="secondary"):
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
        st.markdown("</div>", unsafe_allow_html=True)

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
    show_add_recipe = st.session_state.pop("recipe_show_add", False)
    if selected_recipe_slug not in recipe_slugs:
        st.session_state.selected_recipe_slug = ""
        selected_recipe_slug = ""
    st.markdown("## Recipes")
    with st.container(border=True):
        render_recipe_manager(active_profile, favorites_only=False)
    add_recipe_cols = st.columns([1, 4])
    if add_recipe_cols[0].button("Add Recipe", use_container_width=True, key=f"recipes_add_button_{active_profile['id']}"):
        show_add_recipe = True
    st.markdown("<div id='recipes-section'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        if st.session_state.get("recipe_flash"):
            st.success(st.session_state.recipe_flash)
            st.session_state.recipe_flash = ""
        if show_add_recipe:
            with st.expander("Add Recipe", expanded=True):
                with st.form(f"quick_recipe_form_{active_profile['id']}"):
                    quick_recipe_name = st.text_input("Recipe name")
                    quick_recipe_description = st.text_area("Description", height=56)
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
st.set_page_config(page_title="गृह प्रबंध", page_icon="🥗", layout="wide", initial_sidebar_state="collapsed")
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
    st.session_state.pending_workspace = ""
    st.session_state.purchase_review_items = []
    st.session_state.purchase_review_error = ""
    st.session_state.purchase_review_source = ""
    for key in ["portion_you", "portion_varshit", "dinner_portion_you", "dinner_portion_varshit"]:
        st.session_state[key] = ""

pending_workspace = st.session_state.pop("pending_workspace", "")
if pending_workspace == "Home Supplies":
    pending_workspace = "Inventory"
if pending_workspace == "Setup":
    pending_workspace = "Planner"
if pending_workspace in DESKTOP_WORKSPACE_TABS:
    set_active_workspace(pending_workspace)
if st.session_state.get("active_workspace") == "Home Supplies":
    set_active_workspace("Inventory")
if st.session_state.get("active_workspace") == "Setup":
    set_active_workspace("Planner")
if st.session_state.get("active_workspace") not in DESKTOP_WORKSPACE_TABS:
    set_active_workspace("Planner")
with st.sidebar:
    nav_workspaces = list(PLANNER_NAV_WORKSPACES)
    for workspace in nav_workspaces:
        if render_sidebar_nav_button(workspace):
            set_active_workspace(workspace)
            st.rerun()

    st.divider()
    st.markdown(f"<div class='sidebar-user-frame'><div style='color: var(--color-text-secondary); margin-bottom: 0.35rem;'>User: {st.session_state.get('planner_user_id', '')}</div>", unsafe_allow_html=True)
    with st.expander("Manage User", expanded=False):
        st.caption(f"Current User ID: {st.session_state.get('planner_user_id', '')}")
        if st.button("Switch User", use_container_width=True, key="sidebar_switch_user"):
            st.session_state.pop("planner_user_id", None)
            reset_user_session_state()
            st.rerun()
        if st.button("Forget ID", use_container_width=True, key="sidebar_forget_id"):
            clear_remembered_user_id()
            st.session_state.pop("planner_user_id", None)
            reset_user_session_state()
            st.rerun()
        if st.button("Forget this device", use_container_width=True, key="sidebar_forget_device"):
            clear_remembered_user_id()
            st.info("This device will ask for a User ID next time.")
    st.markdown("</div>", unsafe_allow_html=True)

current_workspace = st.session_state.get("active_workspace", "Planner")
if current_workspace == "Planner":
    render_planner_workspace(active_profile)
elif current_workspace == "Recipes":
    render_recipes_workspace(active_profile)
elif current_workspace == "Purchase Log":
    render_purchase_log_workspace(active_profile)
elif current_workspace == "Inventory":
    render_inventory_workspace(active_profile)
elif current_workspace == "Shopping":
    render_shopping_workspace(active_profile)
elif current_workspace == "Insights":
    render_insights_workspace(active_profile)
else:
    render_planner_workspace(active_profile)

components.html(
    f"""
    <script>
    const doc = window.parent.document;
    const header = doc.querySelector('[data-testid="stHeader"]');
    const updateHeaderDecor = () => {{
      const activeHeader = doc.querySelector('[data-testid="stHeader"]');
      if (!activeHeader) return;
      const leftOffset = Math.max(0, Math.round(activeHeader.getBoundingClientRect().left));
      activeHeader.style.setProperty('--header-crop-offset', `${{leftOffset}}px`);
      let titleNode = doc.getElementById('griha-prabandh-header-title');
      if (!titleNode) {{
        titleNode = doc.createElement('div');
        titleNode.id = 'griha-prabandh-header-title';
        titleNode.textContent = 'गृह प्रबंध';
        Object.assign(titleNode.style, {{
          position: 'absolute',
          left: '3.6rem',
          top: '0.56rem',
          fontSize: '1.55rem',
          fontWeight: '700',
          color: 'var(--color-text-primary)',
          letterSpacing: '0.01em',
          zIndex: '1000',
          pointerEvents: 'none',
          textShadow: '0 1px 0 rgba(255,255,255,0.18)'
        }});
        activeHeader.appendChild(titleNode);
      }}
      titleNode.style.display = 'block';
    }};
    updateHeaderDecor();
    if (!window.parent.__grihaPrabandhHeaderObserver) {{
      const headerObserver = new window.parent.ResizeObserver(() => updateHeaderDecor());
      const sidebar = doc.querySelector('[data-testid="stSidebar"]');
      const activeHeader = doc.querySelector('[data-testid="stHeader"]');
      if (activeHeader) headerObserver.observe(activeHeader);
      if (sidebar) headerObserver.observe(sidebar);
      window.parent.addEventListener('resize', updateHeaderDecor);
      window.parent.__grihaPrabandhHeaderObserver = headerObserver;
    }}
    </script>
    """,
    height=0,
)

pending_anchor = st.session_state.pop("jump_anchor", "")
if pending_anchor:
    components.html(
        f"""
        <script>
        const anchorId = {json.dumps(pending_anchor)};
        let attempts = 0;
        const scrollToSection = () => {{
          const doc = window.parent.document;
          const target = doc.getElementById(anchorId);
          if (!target) {{
            attempts += 1;
            if (attempts < 20) {{
              window.parent.setTimeout(scrollToSection, 120);
            }}
            return;
          }}
          const top = target.getBoundingClientRect().top + window.parent.scrollY - 72;
          window.parent.history.replaceState(null, "", `#${{anchorId}}`);
          window.parent.scrollTo({{ top, behavior: "smooth" }});
        }};
        requestAnimationFrame(() => window.parent.setTimeout(scrollToSection, 120));
        </script>
        """,
        height=0,
    )

if sync_profile_state(active_profile):
    persist_active_profile(active_profile)
