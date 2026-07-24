import json
import tempfile
import unittest
from pathlib import Path

from recipe_submission import (
    build_recipe_payload,
    clear_recipe_form_state,
    recipe_form_field_key,
    recipe_form_values_from_state,
    save_recipe_submission,
    sanitize_recipe_submission,
    upsert_recipe,
    validate_recipe_submission,
)


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
                "name": parts[0],
                "quantity": try_float(parts[1]) if len(parts) > 1 else None,
                "unit": parts[2] if len(parts) > 2 else "",
                "notes": parts[3] if len(parts) > 3 else "",
            }
        )
    return ingredients


def normalize_recipe(recipe):
    return {
        "id": recipe["id"],
        "name": recipe["name"],
        "description": recipe.get("description", ""),
        "base_servings": float(recipe.get("base_servings", 2.0)),
        "ingredients": recipe.get("ingredients", []),
        "instructions": list(recipe.get("instructions", [])),
        "youtube": recipe.get("youtube", ""),
        "favorite": bool(recipe.get("favorite", False)),
    }


class RecipeSubmissionTests(unittest.TestCase):
    def test_validation_requires_name(self):
        self.assertEqual(validate_recipe_submission({"name": "   "}), ["Recipe name is required."])

    def test_build_payload_keeps_multiline_and_decimal_ingredients(self):
        payload = build_recipe_payload(
            {
                "name": "Moong Chilla",
                "description": "Light dinner",
                "base_servings": 2.5,
                "ingredients": "Moong dal | 1.5 | cup | soaked\nJeera | 0.25 | tsp",
                "cooking_style": "Tawa",
                "instructions": "Blend the batter\nCook both sides",
                "youtube": "https://example.com",
            },
            parse_ingredient_lines,
        )
        self.assertEqual(payload["instructions"][0], "Cooking style: Tawa")
        self.assertEqual(payload["instructions"][1:], ["Blend the batter", "Cook both sides"])
        self.assertEqual(payload["ingredients"][0]["quantity"], 1.5)
        self.assertEqual(payload["ingredients"][1]["quantity"], 0.25)

    def test_duplicate_name_updates_existing_recipe_and_preserves_id(self):
        recipes, saved_recipe, action = upsert_recipe(
            [{"id": "abc123", "name": "Moong Chilla", "favorite": True}],
            {"id": "newid", "name": "moong chilla", "description": "Updated"},
            normalize_recipe,
        )
        self.assertEqual(action, "updated")
        self.assertEqual(saved_recipe["id"], "abc123")
        self.assertTrue(saved_recipe["favorite"])
        self.assertEqual(len(recipes), 1)

    def test_form_state_helpers_round_trip_and_clear(self):
        session_state = {
            recipe_form_field_key("p1", "name"): "Poha",
            recipe_form_field_key("p1", "ingredients"): "Poha | 1 | cup",
        }
        values = recipe_form_values_from_state(session_state, "p1")
        self.assertEqual(values["name"], "Poha")
        self.assertEqual(values["ingredients"], "Poha | 1 | cup")
        clear_recipe_form_state(session_state, "p1")
        self.assertEqual(recipe_form_values_from_state(session_state, "p1")["name"], "")

    def test_save_recipe_submission_persists_and_reloads(self):
        profile = {"recipes": []}
        values = {
            "name": "Besan Chilla",
            "description": "Quick brunch",
            "base_servings": 2.0,
            "ingredients": "Besan | 1.5 | cup\nOnion | 1 | pc",
            "cooking_style": "",
            "instructions": "Mix\nCook",
            "youtube": "",
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "recipes.json"

            def persist_profile(updated_profile):
                store_path.write_text(json.dumps(updated_profile))

            def reload_profile():
                return json.loads(store_path.read_text())

            result = save_recipe_submission(
                profile,
                values,
                normalize_recipe=normalize_recipe,
                parse_ingredient_lines=parse_ingredient_lines,
                persist_profile=persist_profile,
                reload_profile=reload_profile,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["recipe"]["name"], "Besan Chilla")
        self.assertEqual(len(result["profile"]["recipes"]), 1)

    def test_sanitize_submission_omits_sensitive_free_text(self):
        sanitized = sanitize_recipe_submission(
            {
                "name": "Poha",
                "description": "Comfort meal",
                "base_servings": 2,
                "ingredients": "Poha | 1 | cup\nPeanut | 0.5 | cup",
                "instructions": "Wash\nCook",
                "cooking_style": "Kadhai",
                "youtube": "",
            }
        )
        self.assertEqual(sanitized["name"], "Poha")
        self.assertEqual(sanitized["ingredient_lines"], 2)
        self.assertNotIn("ingredients", sanitized)
        self.assertNotIn("instructions", sanitized)


if __name__ == "__main__":
    unittest.main()
