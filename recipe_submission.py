from copy import deepcopy
from uuid import uuid4


RECIPE_FORM_DEFAULTS = {
    "name": "",
    "description": "",
    "base_servings": 2.0,
    "ingredients": "",
    "cooking_style": "",
    "instructions": "",
    "youtube": "",
}


def recipe_form_field_key(profile_id, field):
    return f"recipe_form_{profile_id}_{field}"


def recipe_form_values_from_state(session_state, profile_id):
    values = {}
    for field, default in RECIPE_FORM_DEFAULTS.items():
        values[field] = session_state.get(recipe_form_field_key(profile_id, field), default)
    return values


def clear_recipe_form_state(session_state, profile_id):
    for field, default in RECIPE_FORM_DEFAULTS.items():
        session_state[recipe_form_field_key(profile_id, field)] = default


def sanitize_recipe_submission(values):
    ingredient_lines = [line.strip() for line in str(values.get("ingredients", "")).splitlines() if line.strip()]
    instruction_lines = [line.strip() for line in str(values.get("instructions", "")).splitlines() if line.strip()]
    return {
        "name": str(values.get("name", "")).strip(),
        "description_length": len(str(values.get("description", "")).strip()),
        "base_servings": values.get("base_servings"),
        "ingredient_lines": len(ingredient_lines),
        "instruction_lines": len(instruction_lines),
        "cooking_style_present": bool(str(values.get("cooking_style", "")).strip()),
        "youtube_present": bool(str(values.get("youtube", "")).strip()),
    }


def validate_recipe_submission(values):
    errors = []
    if not str(values.get("name", "")).strip():
        errors.append("Recipe name is required.")
    return errors


def build_recipe_payload(values, parse_ingredient_lines):
    instructions = [line.strip() for line in str(values.get("instructions", "")).splitlines() if line.strip()]
    cooking_style = str(values.get("cooking_style", "")).strip()
    if cooking_style:
        instructions = [f"Cooking style: {cooking_style}"] + instructions
    return {
        "id": uuid4().hex,
        "name": str(values.get("name", "")).strip(),
        "description": str(values.get("description", "")).strip(),
        "base_servings": values.get("base_servings", 2.0),
        "ingredients": parse_ingredient_lines(str(values.get("ingredients", ""))),
        "instructions": instructions,
        "youtube": str(values.get("youtube", "")).strip(),
        "favorite": False,
    }


def upsert_recipe(recipes, recipe_payload, normalize_recipe):
    normalized_name = recipe_payload["name"].strip().lower()
    existing = next((item for item in recipes if item.get("name", "").strip().lower() == normalized_name), None)
    payload = dict(recipe_payload)
    if existing:
        payload["id"] = existing.get("id", payload["id"])
        payload["favorite"] = bool(existing.get("favorite", payload.get("favorite", False)))
    normalized_recipe = normalize_recipe(payload)
    updated_recipes = [item for item in recipes if item.get("name", "").strip().lower() != normalized_name]
    updated_recipes.append(normalized_recipe)
    return updated_recipes, normalized_recipe, "updated" if existing else "created"


def save_recipe_submission(
    profile,
    values,
    *,
    normalize_recipe,
    parse_ingredient_lines,
    persist_profile,
    reload_profile,
):
    errors = validate_recipe_submission(values)
    if errors:
        return {"ok": False, "message": errors[0], "errors": errors}

    recipe_payload = build_recipe_payload(values, parse_ingredient_lines)
    updated_profile = deepcopy(profile)
    updated_profile["recipes"], normalized_recipe, action = upsert_recipe(
        updated_profile.get("recipes", []),
        recipe_payload,
        normalize_recipe,
    )
    persist_profile(updated_profile)
    reloaded_profile = reload_profile()
    saved_recipe = next(
        (
            item
            for item in reloaded_profile.get("recipes", [])
            if item.get("id") == normalized_recipe["id"]
            or item.get("name", "").strip().lower() == normalized_recipe["name"].strip().lower()
        ),
        None,
    )
    if not saved_recipe:
        raise ValueError("Recipe save could not be confirmed after reload.")
    return {
        "ok": True,
        "profile": reloaded_profile,
        "recipe": saved_recipe,
        "action": action,
    }
