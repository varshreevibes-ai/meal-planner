from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
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
MAX_PROFILE_MEMBERS = 5
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


def normalize_inventory_item(item):
    return {
        "id": item.get("id", uuid4().hex),
        "name": item.get("name", "Ingredient"),
        "quantity": item.get("quantity", ""),
        "unit": item.get("unit", ""),
        "notes": item.get("notes", ""),
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
    return {
        "id": uuid4().hex,
        "name": name,
        "household_members": [],
        "meal_templates": [],
        "recipes": [],
        "inventory": [],
        "grocery_data": {"missing_items": {}},
        "preferences": {
            "favorites_only": False,
            "activity_level": "Moderately active",
            "meal_mode": "Normal eating",
            "before_didi_arrives": "",
            "morning_routine": "",
            "setup_complete": False,
        },
        "recent_meals": [],
        "recent_recipes": [],
        "meal_log": [],
        "leftovers": [],
        "planner_preferences": {},
    }


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
    normalized["inventory"] = [normalize_inventory_item(item) for item in profile.get("inventory", [])]
    normalized["grocery_data"] = {"missing_items": dict(profile.get("grocery_data", {}).get("missing_items", {}))}
    normalized["preferences"] = {
        "favorites_only": bool(profile.get("preferences", {}).get("favorites_only", False)),
        "activity_level": profile.get("preferences", {}).get("activity_level", "Moderately active"),
        "meal_mode": profile.get("preferences", {}).get("meal_mode", "Normal eating"),
        "before_didi_arrives": profile.get("preferences", {}).get("before_didi_arrives", ""),
        "morning_routine": profile.get("preferences", {}).get("morning_routine", ""),
        "setup_complete": bool(profile.get("preferences", {}).get("setup_complete", False)),
    }
    normalized["recent_meals"] = list(profile.get("recent_meals", []))[:8]
    normalized["recent_recipes"] = list(profile.get("recent_recipes", []))[:8]
    normalized["meal_log"] = [normalize_meal_log_entry(entry) for entry in profile.get("meal_log", [])]
    normalized["leftovers"] = list(profile.get("leftovers", []))
    normalized["planner_preferences"] = dict(profile.get("planner_preferences", {}))
    return normalized


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
    st.session_state.selected_recipe_slug = recipe_slug(name)


def jump_to_anchor(anchor, force_setup_open=False):
    st.session_state.jump_anchor = anchor
    if force_setup_open:
        st.session_state.force_open_setup = True


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
        }
        .stApp .stTabs button[aria-selected="true"] {
            color: var(--text-color);
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
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1.5rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_user_gate():
    st.title("Meal Planner")
    st.write("Enter your user ID to open your planner.")
    with st.form("user_gate_form"):
        raw_user_id = st.text_input("User ID")
        open_planner = st.form_submit_button("Open planner")
    if open_planner:
        normalized = normalize_user_id(raw_user_id)
        if not normalized:
            st.error("Enter a valid user ID using letters, numbers, hyphens, or underscores.")
        else:
            st.session_state.planner_user_id = normalized
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
        st.info("No recipes yet. Add recipes to power recipe links and the planner.")
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


def render_inventory_manager(profile):
    st.markdown("**Inventory**")
    inventory = profile.get("inventory", [])
    if inventory:
        st.dataframe(
            pd.DataFrame(
                [{"Name": item["name"], "Quantity": item.get("quantity", ""), "Unit": item.get("unit", ""), "Notes": item.get("notes", "")} for item in inventory]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No inventory items yet.")

    inventory_options = {"Add new item": ""}
    for item in inventory:
        inventory_options[f"Edit {item['name']}"] = item["id"]
    selected_inventory_id = st.selectbox("Inventory item", list(inventory_options.values()), format_func=lambda item: next(label for label, value in inventory_options.items() if value == item), key=f"inventory_editor_{profile['id']}")
    selected_inventory = next((item for item in inventory if item["id"] == selected_inventory_id), None)
    with st.form(f"inventory_form_{profile['id']}"):
        inventory_name = st.text_input("Ingredient name", value=selected_inventory.get("name", "") if selected_inventory else "")
        inventory_quantity = st.text_input("Quantity", value=selected_inventory.get("quantity", "") if selected_inventory else "")
        inventory_unit = st.text_input("Unit", value=selected_inventory.get("unit", "") if selected_inventory else "")
        inventory_notes = st.text_input("Notes", value=selected_inventory.get("notes", "") if selected_inventory else "")
        save_inventory = st.form_submit_button("Save inventory item")
        delete_inventory = st.form_submit_button("Delete inventory item") if selected_inventory else False
    if save_inventory:
        if not inventory_name.strip():
            st.error("Ingredient name is required.")
        else:
            item = normalize_inventory_item(
                {
                    "id": selected_inventory["id"] if selected_inventory else uuid4().hex,
                    "name": inventory_name.strip(),
                    "quantity": inventory_quantity.strip(),
                    "unit": inventory_unit.strip(),
                    "notes": inventory_notes.strip(),
                }
            )
            profile["inventory"] = [entry for entry in inventory if entry["id"] != item["id"]] + [item]
            persist_active_profile(profile)
            st.rerun()
    if delete_inventory and selected_inventory:
        profile["inventory"] = [entry for entry in inventory if entry["id"] != selected_inventory["id"]]
        persist_active_profile(profile)
        st.rerun()

    if profile.get("leftovers"):
        st.markdown("**Leftovers**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Recipe": item.get("recipe_name", ""),
                        "Remaining Servings": format_number(item.get("remaining_servings", 0)),
                        "Date": item.get("created_at", "")[:10],
                    }
                    for item in profile["leftovers"][:10]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_setup_panel(profile):
    setup_complete = profile.get("preferences", {}).get("setup_complete", False)
    expanded = st.session_state.pop("force_open_setup", False) or not setup_complete
    st.markdown("<div id='setup-section'></div>", unsafe_allow_html=True)
    with st.expander("Add members", expanded=expanded):
        render_household_manager(profile, key_scope="setup")
        with st.form(f"setup_preferences_{profile['id']}"):
            save_setup = st.form_submit_button("Save household setup")
        if save_setup:
            if not profile.get("household_members"):
                st.error("Add at least one household member before completing setup.")
            else:
                profile["preferences"]["setup_complete"] = True
                persist_active_profile(profile)
                st.rerun()


st.set_page_config(page_title="Meal Planner", page_icon="🥗", layout="wide")
inject_ui_styles()

if not st.session_state.get("planner_user_id"):
    render_user_gate()

profile_store = load_profile_store(user_profile_store_path(st.session_state["planner_user_id"]))
active_profile = get_active_profile(profile_store)

if st.session_state.get("active_profile_loaded") != active_profile["id"]:
    st.session_state.active_profile_loaded = active_profile["id"]
    st.session_state.grocery_list = OrderedDict(active_profile.get("grocery_data", {}).get("missing_items", {}))
    st.session_state.mealLog = list(active_profile.get("meal_log", []))
    st.session_state.selected_recipe_slug = ""
    for key in ["portion_you", "portion_varshit", "dinner_portion_you", "dinner_portion_varshit"]:
        st.session_state[key] = ""

brunch_options, brunch_label_map = build_planner_options(active_profile)
dinner_options = [planner_option_id("special", "Morning Portion Only")] + brunch_options
dinner_label_map = {planner_option_id("special", "Morning Portion Only"): "Morning Portion Only", **brunch_label_map}
fixed_item_meta = build_fixed_item_meta(active_profile)
primary_member, secondary_member = planner_members(active_profile)
primary_label = fixed_item_meta["primary_name"]
secondary_label = fixed_item_meta["secondary_name"]
routine_sections = build_routine_sections(active_profile)

st.title("Meal Planner")
render_setup_panel(active_profile)

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

    if action_right.button("Log what I ate", use_container_width=True):
        brunch_dish = option_to_dish(active_profile, st.session_state.brunch_option_id)
        planned_servings = portion_factor(st.session_state.get("portion_you", "")) + portion_factor(st.session_state.get("portion_varshit", ""))
        actual_servings = planned_servings
        active_profile = logMeal(
            active_profile,
            brunch_dish["name"],
            st.session_state.get("portion_you", ""),
            st.session_state.get("portion_varshit", ""),
            planned_servings,
            actual_servings,
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
    brunch_option_id = row1.selectbox(
        "Brunch",
        brunch_options,
        index=brunch_options.index(st.session_state.brunch_option_id),
        format_func=lambda item: brunch_label_map[item],
        key="brunch_option_id",
        on_change=sync_portions_from_selection,
        args=(active_profile,),
    )
    dinner_option_id = row2.selectbox(
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
    portion_you = row4.text_input(
        f"{primary_label} Brunch Portion",
        key="portion_you",
        placeholder=st.session_state.get("portion_you_suggestion", ""),
    )
    dinner_portion_you = row5.text_input(
        f"{primary_label} Dinner Portion",
        key="dinner_portion_you",
        placeholder=st.session_state.get("dinner_portion_you_suggestion", ""),
    )
    selected_you = []
    with st.expander(f"{primary_label} fixed add-ons", expanded=False):
        if fixed_item_meta["primary"]:
            your_checks = st.columns(4)
            for i, item in enumerate(fixed_item_meta["primary"]):
                if your_checks[i % 4].checkbox(item, value=True, key=f"you_{item}"):
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
        portion_varshit = row6.text_input(
            f"{secondary_label} Brunch Portion",
            key="portion_varshit",
            placeholder=st.session_state.get("portion_varshit_suggestion", ""),
        )
        dinner_portion_varshit = row7.text_input(
            f"{secondary_label} Dinner Portion",
            key="dinner_portion_varshit",
            placeholder=st.session_state.get("dinner_portion_varshit_suggestion", ""),
        )
        with st.expander(f"{secondary_label} fixed add-ons", expanded=False):
            if fixed_item_meta["secondary"]:
                varshit_checks = st.columns(3)
                for i, item in enumerate(fixed_item_meta["secondary"]):
                    if varshit_checks[i % 3].checkbox(item, value=True, key=f"varshit_{item}"):
                        selected_varshit.append(item)
                    else:
                        for name, qty in fixed_item_meta["secondary"][item]["ingredients"]:
                            st.session_state.grocery_list[name] = qty
            else:
                st.write("No routine add-ons set up yet.")

brunch = option_to_dish(active_profile, st.session_state.brunch_option_id)
dinner = option_to_dish(active_profile, st.session_state.dinner_option_id, brunch)
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
for recipe in active_profile.get("recipes", []):
    factor = household_servings(active_profile) / max(recipe.get("base_servings", 2.0), 0.1)
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
recipe_slugs = {recipe_slug(dish["name"]) for dish in recipe_dishes}
selected_recipe_slug = st.session_state.get("selected_recipe_slug", "")
if selected_recipe_slug not in recipe_slugs:
    st.session_state.selected_recipe_slug = ""
    selected_recipe_slug = ""

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
    burn[key] = {
        "resting": resting_burn,
        "routine": routine_burn,
        "walking": walking_burn,
        "gym": gym_burn,
        "total_spent": total_spent,
        "deficit_value": round(total_spent - totals[key]["calories"]),
    }

table = [
    {
        "Section": "Brunch",
        "Choice": brunch["name"],
        f"{primary_label} Portion": f"{portion_you} | Fixed: {fixed_you}",
        f"{primary_label} Calories": round(nutrition_for(brunch["name"])["you"]["calories"] * shreya_brunch_factor),
    },
    {
        "Section": "Dinner",
        "Choice": dinner["name"],
        f"{primary_label} Portion": dinner_portion_you,
        f"{primary_label} Calories": round(nutrition_for(dinner_calorie_source["name"])["you"]["calories"] * shreya_dinner_factor),
    },
    {
        "Section": "Add-ons",
        "Choice": "Selected fixed daily add-ons",
        f"{primary_label} Portion": fixed_you,
        f"{primary_label} Calories": sum(fixed_item_meta["primary"][item]["calories"] for item in selected_you),
    },
    {
        "Section": "Calories Intake",
        "Choice": "",
        f"{primary_label} Portion": "",
        f"{primary_label} Calories": round(totals["you"]["calories"]),
    },
    {
        "Section": "Calories Spent",
        "Choice": "Resting burn + daily routine + walking + gym context",
        f"{primary_label} Portion": "",
        f"{primary_label} Calories": burn["you"]["total_spent"],
    },
    {
        "Section": "Deficit / Surplus",
        "Choice": "",
        f"{primary_label} Portion": "",
        f"{primary_label} Calories": burn["you"]["deficit_value"],
    },
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
    primary_idx = list(df.columns).index(f"{primary_label} Calories")
    styles[primary_idx] = "background-color: #d1fae5; color: #065f46;" if row[f"{primary_label} Calories"] >= 0 else "background-color: #fee2e2; color: #991b1b;"
    if secondary_member:
        secondary_idx = list(df.columns).index(f"{secondary_label} Calories")
        styles[secondary_idx] = "background-color: #d1fae5; color: #065f46;" if row[f"{secondary_label} Calories"] >= 0 else "background-color: #fee2e2; color: #991b1b;"
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

        st.markdown("**Selected recipe links**")
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
            before_title_col, before_button_col = st.columns([5, 1])
            before_title_col.markdown("**Before Didi Arrives**")
            if before_button_col.button("Edit", key=f"edit_before_didi_{active_profile['id']}", use_container_width=True):
                toggle_state(f"editing_before_didi_{active_profile['id']}")
                st.rerun()
            st.markdown("- " + "\n- ".join(routine_sections["night_prep"]))
            if st.session_state.get(f"editing_before_didi_{active_profile['id']}", False):
                with st.form(f"before_didi_form_{active_profile['id']}"):
                    before_didi_text = st.text_area(
                        "Before Didi Arrives",
                        value=active_profile.get("preferences", {}).get("before_didi_arrives", ""),
                        height=120,
                    )
                    save_col, cancel_col = st.columns(2)
                    save_before_didi = save_col.form_submit_button("Save")
                    cancel_before_didi = cancel_col.form_submit_button("Cancel")
                if save_before_didi:
                    active_profile["preferences"]["before_didi_arrives"] = before_didi_text.strip()
                    st.session_state[f"editing_before_didi_{active_profile['id']}"] = False
                    persist_active_profile(active_profile)
                    st.rerun()
                if cancel_before_didi:
                    st.session_state[f"editing_before_didi_{active_profile['id']}"] = False
                    st.rerun()
        with st.expander("Morning Routine", expanded=False):
            morning_title_col, morning_button_col = st.columns([5, 1])
            morning_title_col.markdown("**Morning Routine**")
            if morning_button_col.button("Edit", key=f"edit_morning_routine_{active_profile['id']}", use_container_width=True):
                toggle_state(f"editing_morning_routine_{active_profile['id']}")
                st.rerun()
            st.markdown("- " + "\n- ".join(routine_sections["morning_start"]))
            if st.session_state.get(f"editing_morning_routine_{active_profile['id']}", False):
                with st.form(f"morning_routine_form_{active_profile['id']}"):
                    morning_routine_text = st.text_area(
                        "Morning Routine",
                        value=active_profile.get("preferences", {}).get("morning_routine", ""),
                        height=120,
                    )
                    save_col, cancel_col = st.columns(2)
                    save_morning_routine = save_col.form_submit_button("Save")
                    cancel_morning_routine = cancel_col.form_submit_button("Cancel")
                if save_morning_routine:
                    active_profile["preferences"]["morning_routine"] = morning_routine_text.strip()
                    st.session_state[f"editing_morning_routine_{active_profile['id']}"] = False
                    persist_active_profile(active_profile)
                    st.rerun()
                if cancel_morning_routine:
                    st.session_state[f"editing_morning_routine_{active_profile['id']}"] = False
                    st.rerun()

with calories_tab:
    with st.container(border=True):
        st.markdown("<div id='calories-section'></div>", unsafe_allow_html=True)
        st.dataframe(df.style.apply(style_deficit_row, axis=1), use_container_width=True, hide_index=True)

with meal_log_tab:
    with st.container(border=True):
        st.markdown("<div id='meal-log-section'></div>", unsafe_allow_html=True)
        MealLogTab(active_profile)

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
                quick_recipe = normalize_recipe(
                    {
                        "id": uuid4().hex,
                        "name": quick_recipe_name.strip(),
                        "description": quick_recipe_description.strip(),
                        "base_servings": quick_base_servings,
                        "ingredients": parse_ingredient_lines(quick_recipe_ingredients),
                        "instructions": instructions,
                        "youtube": quick_recipe_youtube.strip(),
                        "favorite": False,
                    }
                )
                active_profile["recipes"] = [item for item in active_profile.get("recipes", []) if item["name"].strip().lower() != quick_recipe["name"].strip().lower()] + [quick_recipe]
                persist_active_profile(active_profile)
                st.session_state.recipe_flash = f"Saved recipe {quick_recipe['name']}."
                st.rerun()

    for dish in recipe_dishes:
        dish_slug = recipe_slug(dish["name"])
        st.markdown(f"<div id='{recipe_anchor_id(dish['name'])}' class='recipe-anchor'></div>", unsafe_allow_html=True)
        with st.expander(dish["name"], expanded=dish_slug == selected_recipe_slug):
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
          const expander = target.nextElementSibling;
          if (expander) {{
            expander.setAttribute("tabindex", "-1");
            expander.focus({{ preventScroll: true }});
          }}
        }};
        requestAnimationFrame(() => setTimeout(scrollToRecipe, 80));
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
