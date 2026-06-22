from collections import OrderedDict
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
    "Daily Fixed Add-ons": {"you": {"calories": 210, "protein": 8}, "varshit": {"calories": 260, "protein": 10}},
    "Daily Add-ons plus Mango": {"you": {"calories": 300, "protein": 8}, "varshit": {"calories": 260, "protein": 10}},
    "Daily Add-ons plus Papaya": {"you": {"calories": 250, "protein": 8}, "varshit": {"calories": 260, "protein": 10}},
    "Daily Add-ons plus Air-Fried Chana": {"you": {"calories": 280, "protein": 12}, "varshit": {"calories": 330, "protein": 16}},
    "Morning Portion Only": {"you": {"calories": 180, "protein": 6}, "varshit": {"calories": 240, "protein": 9}},
    "Light Soup or Salad Plate": {"you": {"calories": 110, "protein": 3}, "varshit": {"calories": 150, "protein": 4}},
    "Moong Chilla Light Dinner": {"you": {"calories": 210, "protein": 10}, "varshit": {"calories": 280, "protein": 13}},
    "Soup Light Dinner": {"you": {"calories": 140, "protein": 4}, "varshit": {"calories": 190, "protein": 6}},
}
FIXED_ITEM_META = {
    "you": {
        "Warm water + ghee": {"calories": 45, "protein": 0, "ingredients": [("ghee", "2 tsp"), ("warm water", "as needed")]},
        "Soaked dates": {"calories": 45, "protein": 0, "ingredients": [("dates", "2 to 4")]},
        "Soaked almonds": {"calories": 70, "protein": 3, "ingredients": [("almonds", "10 to 12")]},
        "Pumpkin seeds": {"calories": 55, "protein": 3, "ingredients": [("pumpkin seeds", "2 tbsp")]},
        "Kali kishmish": {"calories": 35, "protein": 0, "ingredients": [("kali kishmish", "2 tbsp")]},
        "Anar": {"calories": 70, "protein": 1, "ingredients": [("anar", "1 bowl")]},
        "Sattu": {"calories": 80, "protein": 4, "ingredients": [("sattu", "1 serving")]},
        "Avvatar Matka Kulfi shake": {"calories": 125, "protein": 24, "ingredients": [("Avvatar Matka Kulfi whey", "1 scoop"), ("warm water", "as needed"), ("sonth powder", "a pinch")]},
    },
    "varshit": {
        "ON Alphonso Mango shake": {"calories": 250, "protein": 31, "ingredients": [("ON Alphonso Mango whey", "2 spoons"), ("soya milk", "1 glass"), ("banana", "1 small or bites")]},
        "Anar": {"calories": 70, "protein": 1, "ingredients": [("anar", "1 bowl")]},
        "3 cucumber salad": {"calories": 45, "protein": 2, "ingredients": [("cucumber", "3")]},
        "Sattu": {"calories": 80, "protein": 4, "ingredients": [("sattu", "1 serving")]},
        "Banana bites": {"calories": 45, "protein": 0, "ingredients": [("banana", "extra bites if needed")]},
    },
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
    "Daily Fixed Add-ons": {"you": "anar + soaked items + sattu", "varshit": "anar + sattu"},
    "Daily Add-ons plus Mango": {"you": "fixed add-ons + Amrapali or Kesar ripe mango", "varshit": "fixed add-ons"},
    "Daily Add-ons plus Papaya": {"you": "fixed add-ons + papaya", "varshit": "fixed add-ons + papaya"},
    "Daily Add-ons plus Air-Fried Chana": {"you": "fixed add-ons + small chana", "varshit": "fixed add-ons + chana"},
    "Morning Portion Only": {"you": "1 small leftover bowl", "varshit": "1 medium leftover bowl"},
    "Light Soup or Salad Plate": {"you": "1 soup bowl", "varshit": "1 soup bowl + cucumber salad"},
    "Moong Chilla Light Dinner": {"you": "1 to 2 soft chilla", "varshit": "2 chilla"},
    "Soup Light Dinner": {"you": "1 soup bowl", "varshit": "1 larger soup bowl"},
}


def dish_names(section):
    return [dish["name"] for dish in DATA["sections"][section]]


def get_dish(section, name):
    return next(dish for dish in DATA["sections"][section] if dish["name"] == name)


def dinner_dish(name):
    return get_dish("dinner", name) if name == "Morning Portion Only" else get_dish("brunch", name)


def nutrition_for(name):
    return NUTRITION.get(name, {"you": {"calories": 0, "protein": 0}, "varshit": {"calories": 0, "protein": 0}})


def portion_factor(text, default=1.0):
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    if not nums:
        return default
    if "to" in text and len(nums) >= 2:
        return sum(nums[:2]) / 2
    return nums[0]


def collect_ingredients(dishes):
    items = OrderedDict()
    for dish in dishes:
        for item in dish["ingredients"]:
            items[item["name"]] = item.get("qty", "")
    return items


def ingredient_lines(items):
    return "\n".join(f"- {name}: {qty}" if qty else f"- {name}" for name, qty in items.items())


def recipe_slug(name):
    return name.lower().replace(" ", "-")


def all_recipe_dishes():
    dishes = []
    for section in DATA["sections"].values():
        dishes.extend(section)
    dedup = {}
    for dish in dishes:
        dedup[dish["name"]] = dish
    return list(dedup.values())


def sedentary_tdee_from_weight(weight_kg):
    return round(22 * weight_kg)


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
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }
        .section-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-color);
            margin: 1rem 0 0.55rem;
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
        .stApp .stButton button[kind="secondary"] {
            background: var(--secondary-background-color);
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
        .stApp .stCheckbox label p,
        .stApp .stRadio label p,
        .stApp .stMarkdown p {
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


def section_intro(anchor, title):
    st.markdown(
        f"""
        <div id="{anchor}"></div>
        <div class="section-title">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def has_dinner_recipe_link(dish):
    return bool(dish.get("ingredients") or dish.get("youtube"))


def recipe_anchor_id(name):
    return f"recipe-{recipe_slug(name)}"


def open_recipe(name):
    st.session_state.selected_recipe_slug = recipe_slug(name)


def load_meal_log():
    if not MEAL_LOG_PATH.exists():
        return []
    try:
        data = json.loads(MEAL_LOG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    return [normalize_meal_log_entry(entry) for entry in data] if isinstance(data, list) else []


def save_meal_log(mealLog):
    MEAL_LOG_PATH.write_text(json.dumps(mealLog, indent=2))


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
    return {
        "id": entry.get("id", uuid4().hex),
        "meal_name": entry.get("meal_name", "Unknown meal"),
        "shreya_quantity": entry.get("shreya_quantity", shreya_quantity),
        "varshit_quantity": entry.get("varshit_quantity", varshit_quantity),
        "logged_at": logged_at,
        "date": entry.get("date", format_logged_at(logged_at).strftime("%Y-%m-%d") if format_logged_at(logged_at) != datetime.min else ""),
        "time": entry.get("time", format_logged_at(logged_at).strftime("%I:%M %p") if format_logged_at(logged_at) != datetime.min else ""),
        "shreya_calories": entry.get("shreya_calories", nutrition["you"]["calories"]),
        "shreya_protein": entry.get("shreya_protein", nutrition["you"]["protein"]),
        "varshit_calories": entry.get("varshit_calories", nutrition["varshit"]["calories"]),
        "varshit_protein": entry.get("varshit_protein", nutrition["varshit"]["protein"]),
    }


def logMeal(mealLog, meal_name, shreya_quantity, varshit_quantity):
    logged_at = datetime.now().isoformat(timespec="seconds")
    nutrition = nutrition_for(meal_name)
    entry = {
        "id": uuid4().hex,
        "meal_name": meal_name,
        "shreya_quantity": shreya_quantity,
        "varshit_quantity": varshit_quantity,
        "logged_at": logged_at,
        "date": datetime.fromisoformat(logged_at).strftime("%Y-%m-%d"),
        "time": datetime.fromisoformat(logged_at).strftime("%I:%M %p"),
        "shreya_calories": nutrition["you"]["calories"],
        "shreya_protein": nutrition["you"]["protein"],
        "varshit_calories": nutrition["varshit"]["calories"],
        "varshit_protein": nutrition["varshit"]["protein"],
    }
    updated_log = [entry, *mealLog]
    save_meal_log(updated_log)
    return updated_log


def deleteMealLogEntry(mealLog, entry_id):
    updated_log = [entry for entry in mealLog if entry.get("id") != entry_id]
    save_meal_log(updated_log)
    return updated_log


def format_logged_at(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.min


def sync_portions_from_selection():
    brunch_name = st.session_state.get("brunch_name", dish_names("brunch")[0])
    dinner_name = st.session_state.get("dinner_name", "Morning Portion Only")
    st.session_state.portion_you = PORTIONS[brunch_name]["you"]
    st.session_state.portion_varshit = PORTIONS[brunch_name]["varshit"]
    st.session_state.dinner_portion_you = PORTIONS[dinner_name]["you"] if dinner_name in PORTIONS else PORTIONS[brunch_name]["you"]
    st.session_state.dinner_portion_varshit = PORTIONS[dinner_name]["varshit"] if dinner_name in PORTIONS else PORTIONS[brunch_name]["varshit"]


def choose_random_meals():
    st.session_state.brunch_name = random.choice(dish_names("brunch"))
    st.session_state.dinner_name = random.choice(["Morning Portion Only"] + dish_names("brunch"))
    sync_portions_from_selection()


def log_current_meal():
    meal_name = st.session_state.get("brunch_name")
    if not meal_name:
        return
    st.session_state.mealLog = logMeal(
        st.session_state.mealLog,
        meal_name,
        st.session_state.get("portion_you", ""),
        st.session_state.get("portion_varshit", ""),
    )
    st.session_state.meal_log_flash = f"Logged {meal_name}."


def MealLogTab(mealLog):
    if not mealLog:
        st.info("No meals logged yet.")
        return

    sorted_log = sorted(mealLog, key=lambda item: format_logged_at(item.get("logged_at")), reverse=True)
    meal_log_rows = []
    for entry in sorted_log:
        logged_at = format_logged_at(entry.get("logged_at"))
        meal_log_rows.append(
            {
                "Meal": entry.get("meal_name", "Unknown meal"),
                "Date": logged_at.strftime("%d %b %Y") if logged_at != datetime.min else entry.get("date", ""),
                "Time": logged_at.strftime("%I:%M %p") if logged_at != datetime.min else entry.get("time", ""),
                "Shreya Quantity": entry.get("shreya_quantity", ""),
                "Varshit Quantity": entry.get("varshit_quantity", ""),
                "Shreya Calories": entry.get("shreya_calories", 0),
                "Shreya Protein (g)": entry.get("shreya_protein", 0),
                "Varshit Calories": entry.get("varshit_calories", 0),
                "Varshit Protein (g)": entry.get("varshit_protein", 0),
            }
        )
    st.dataframe(pd.DataFrame(meal_log_rows), use_container_width=True, hide_index=True)

    delete_options = {
        f"{entry.get('meal_name', 'Unknown meal')} | {entry.get('date', '')} {entry.get('time', '')}": entry.get("id")
        for entry in sorted_log
    }
    selected_delete_label = st.selectbox("Remove a logged meal", ["Select a meal to remove"] + list(delete_options.keys()))
    if selected_delete_label != "Select a meal to remove":
        if st.button("Delete selected meal", type="secondary"):
            st.session_state.mealLog = deleteMealLogEntry(st.session_state.mealLog, delete_options[selected_delete_label])
            st.rerun()


st.set_page_config(page_title="Meal Planner", page_icon="🥗", layout="wide")
inject_ui_styles()
st.title("Meal Planner")

if "grocery_list" not in st.session_state:
    st.session_state.grocery_list = OrderedDict()
if "mealLog" not in st.session_state:
    st.session_state.mealLog = load_meal_log()
if "selected_recipe_slug" not in st.session_state:
    st.session_state.selected_recipe_slug = ""

with st.container(border=True):
    st.markdown("<div id='planner-section'></div>", unsafe_allow_html=True)
    top_left, top_right = st.columns([2, 1])
    day = top_left.selectbox("Plan for", DATA["days"])
    top_right.write("")

    if st.session_state.get("selected_day") != day:
        st.session_state.selected_day = day
        defaults = DAY_PLANS.get(day, DAY_PLANS["Today"])
        st.session_state.brunch_name = defaults["brunch"]
        st.session_state.dinner_name = defaults["dinner"]
        sync_portions_from_selection()

    action_left, action_right = st.columns(2)
    action_left.button("Khane Mein Kya Khaye?", on_click=choose_random_meals, use_container_width=True)
    action_right.button(
        "Log what I ate",
        on_click=log_current_meal,
        disabled=not bool(st.session_state.get("brunch_name")),
        use_container_width=True,
    )
    if st.session_state.get("meal_log_flash"):
        st.success(st.session_state.meal_log_flash)
        st.session_state.meal_log_flash = ""

    row1, row2 = st.columns(2)
    brunch_name = row1.selectbox("Brunch", dish_names("brunch"), key="brunch_name", on_change=sync_portions_from_selection)
    dinner_name = row2.selectbox("Dinner", ["Morning Portion Only"] + dish_names("brunch"), key="dinner_name", on_change=sync_portions_from_selection)

    st.markdown("**Shreya plan**")
    row4, row5 = st.columns(2)
    portion_you = row4.text_input("Shreya Brunch Portion", key="portion_you")
    dinner_portion_you = row5.text_input("Shreya Dinner Portion", key="dinner_portion_you")
    selected_you = []
    with st.expander("Shreya fixed add-ons", expanded=False):
        your_checks = st.columns(4)
        for i, item in enumerate(FIXED_ITEM_META["you"]):
            if your_checks[i % 4].checkbox(item, value=True, key=f"you_{item}"):
                selected_you.append(item)
            else:
                for name, qty in FIXED_ITEM_META["you"][item]["ingredients"]:
                    st.session_state.grocery_list[name] = qty

    st.markdown("**Varshit plan**")
    row6, row7 = st.columns(2)
    portion_varshit = row6.text_input("Varshit Brunch Portion", key="portion_varshit")
    dinner_portion_varshit = row7.text_input("Varshit Dinner Portion", key="dinner_portion_varshit")
    selected_varshit = []
    with st.expander("Varshit fixed add-ons", expanded=False):
        varshit_checks = st.columns(3)
        for i, item in enumerate(FIXED_ITEM_META["varshit"]):
            if varshit_checks[i % 3].checkbox(item, value=True, key=f"varshit_{item}"):
                selected_varshit.append(item)
            else:
                for name, qty in FIXED_ITEM_META["varshit"][item]["ingredients"]:
                    st.session_state.grocery_list[name] = qty

brunch = get_dish("brunch", brunch_name)
dinner = dinner_dish(dinner_name)
recipe_dishes = all_recipe_dishes()
recipe_slugs = {recipe_slug(dish["name"]) for dish in recipe_dishes}
selected_recipe_slug = st.session_state.get("selected_recipe_slug", "")
if selected_recipe_slug not in recipe_slugs:
    selected_recipe_slug = ""
    st.session_state.selected_recipe_slug = ""
shreya_brunch_factor = portion_factor(portion_you)
shreya_dinner_factor = portion_factor(dinner_portion_you)
varshit_brunch_factor = portion_factor(portion_varshit)
varshit_dinner_factor = portion_factor(dinner_portion_varshit)
dinner_calorie_source = brunch if dinner_name == "Morning Portion Only" else dinner

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
    totals["you"]["calories"] += FIXED_ITEM_META["you"][item]["calories"]
    totals["you"]["protein"] += FIXED_ITEM_META["you"][item]["protein"]
for item in selected_varshit:
    totals["varshit"]["calories"] += FIXED_ITEM_META["varshit"][item]["calories"]
    totals["varshit"]["protein"] += FIXED_ITEM_META["varshit"][item]["protein"]

fixed_you = ", ".join(selected_you) if selected_you else "None selected"
fixed_varshit = ", ".join(selected_varshit) if selected_varshit else "None selected"
burn = {}
for key in ["you", "varshit"]:
    person = DATA["people"][key]
    resting_burn = sedentary_tdee_from_weight(person["weight_kg"])
    steps_burn = round(person["daily_steps"] * person["kcal_per_step"])
    total_spent = resting_burn + person["desk_work_burn_kcal"] + person["calisthenics_burn_kcal"] + steps_burn
    burn[key] = {
        "resting": resting_burn,
        "desk_work": person["desk_work_burn_kcal"],
        "workout": person["calisthenics_burn_kcal"],
        "steps": steps_burn,
        "total_spent": total_spent,
        "deficit_value": round(total_spent - totals[key]["calories"]),
    }
table = [
    {
        "Section": "Brunch",
        "Choice": brunch["name"],
        "Shreya Portion": f"{portion_you} | Fixed: {fixed_you}",
        "Varshit Portion": f"{portion_varshit} | Fixed: {fixed_varshit}",
        "Shreya Calories": round(nutrition_for(brunch["name"])["you"]["calories"] * shreya_brunch_factor),
        "Varshit Calories": round(nutrition_for(brunch["name"])["varshit"]["calories"] * varshit_brunch_factor),
    },
    {
        "Section": "Dinner",
        "Choice": dinner["name"],
        "Shreya Portion": dinner_portion_you,
        "Varshit Portion": dinner_portion_varshit,
        "Shreya Calories": round(nutrition_for(dinner_calorie_source["name"])["you"]["calories"] * shreya_dinner_factor),
        "Varshit Calories": round(nutrition_for(dinner_calorie_source["name"])["varshit"]["calories"] * varshit_dinner_factor),
    },
    {
        "Section": "Add-ons",
        "Choice": "Selected fixed daily add-ons",
        "Shreya Portion": fixed_you,
        "Varshit Portion": fixed_varshit,
        "Shreya Calories": sum(FIXED_ITEM_META["you"][item]["calories"] for item in selected_you),
        "Varshit Calories": sum(FIXED_ITEM_META["varshit"][item]["calories"] for item in selected_varshit),
    },
    {
        "Section": "Calories Intake",
        "Choice": "",
        "Shreya Portion": "",
        "Varshit Portion": "",
        "Shreya Calories": round(totals["you"]["calories"]),
        "Varshit Calories": round(totals["varshit"]["calories"]),
    },
    {
        "Section": "Calories Spent",
        "Choice": "Resting burn + sitting work + calisthenics + current 2k steps",
        "Shreya Portion": "",
        "Varshit Portion": "",
        "Shreya Calories": burn["you"]["total_spent"],
        "Varshit Calories": burn["varshit"]["total_spent"],
    },
    {
        "Section": "Deficit / Surplus",
        "Choice": "",
        "Shreya Portion": "",
        "Varshit Portion": "",
        "Shreya Calories": burn["you"]["deficit_value"],
        "Varshit Calories": burn["varshit"]["deficit_value"],
    },
]
df = pd.DataFrame(table)


def style_deficit_row(row):
    if row["Section"] != "Deficit / Surplus":
        return [""] * len(row)
    styles = [""] * len(row)
    shreya_idx = list(df.columns).index("Shreya Calories")
    varshit_idx = list(df.columns).index("Varshit Calories")
    styles[shreya_idx] = "background-color: #d1fae5; color: #065f46;" if row["Shreya Calories"] >= 0 else "background-color: #fee2e2; color: #991b1b;"
    styles[varshit_idx] = "background-color: #d1fae5; color: #065f46;" if row["Varshit Calories"] >= 0 else "background-color: #fee2e2; color: #991b1b;"
    return styles

ingredients_tab, calories_tab, meal_log_tab = st.tabs(["Ingredients & Recipe", "Calories", "Meal Log"])

with ingredients_tab:
    with st.container(border=True):
        st.markdown("<div id='ingredients-section'></div>", unsafe_allow_html=True)
        all_ingredients = collect_ingredients([brunch, dinner])
        main_ingredients = collect_ingredients([brunch, dinner])
        addon_ingredients = OrderedDict()
        for item in selected_you:
            for name, qty in FIXED_ITEM_META["you"][item]["ingredients"]:
                all_ingredients[name] = qty
                addon_ingredients[name] = qty
        for item in selected_varshit:
            for name, qty in FIXED_ITEM_META["varshit"][item]["ingredients"]:
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
                st.rerun()
        else:
            st.write("All selected ingredients are available.")

        st.markdown("**Selected recipe links**")
        if recipe_slug(brunch["name"]) in recipe_slugs:
            brunch_link_col, brunch_text_col = st.columns([1, 4])
            if brunch_link_col.button("Open", key=f"open_recipe_{recipe_slug(brunch['name'])}", use_container_width=True):
                open_recipe(brunch["name"])
                st.rerun()
            brunch_text_col.markdown(f"Brunch recipe: **{brunch['name']}**")
        if has_dinner_recipe_link(dinner) and recipe_slug(dinner["name"]) in recipe_slugs:
            dinner_link_col, dinner_text_col = st.columns([1, 4])
            if dinner_link_col.button("Open", key=f"open_recipe_{recipe_slug(dinner['name'])}", use_container_width=True):
                open_recipe(dinner["name"])
                st.rerun()
            dinner_text_col.markdown(f"Dinner recipe: **{dinner['name']}**")

        with st.expander("Before Didi Arrives", expanded=False):
            st.markdown("- " + "\n- ".join(DATA["daily_routine"]["night_prep"]))
        with st.expander("Morning Routine", expanded=False):
            st.markdown("- " + "\n- ".join(DATA["daily_routine"]["morning_start"]))

with calories_tab:
    with st.container(border=True):
        st.markdown("<div id='calories-section'></div>", unsafe_allow_html=True)
        st.dataframe(df.style.apply(style_deficit_row, axis=1), use_container_width=True, hide_index=True)

with meal_log_tab:
    with st.container(border=True):
        st.markdown("<div id='meal-log-section'></div>", unsafe_allow_html=True)
        MealLogTab(st.session_state.mealLog)

st.divider()
section_intro(
    "recipes-section",
    "Recipe View",
)
with st.container(border=True):
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
