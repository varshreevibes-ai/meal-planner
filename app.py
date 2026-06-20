from collections import OrderedDict
from pathlib import Path
import re
import random

import pandas as pd
import streamlit as st
import yaml

DATA = yaml.safe_load(Path("meal_data.yaml").read_text())
NUTRITION = {
    "routine": {"you": {"calories": 260, "protein": 18}, "varshit": {"calories": 480, "protein": 24}},
    "Avocado Toast": {"you": {"calories": 240, "protein": 6}, "varshit": {"calories": 320, "protein": 9}},
    "Avocado Salad": {"you": {"calories": 220, "protein": 8}, "varshit": {"calories": 300, "protein": 12}},
    "Chickpea Tacos": {"you": {"calories": 330, "protein": 10}, "varshit": {"calories": 430, "protein": 14}},
    "Matra": {"you": {"calories": 280, "protein": 10}, "varshit": {"calories": 360, "protein": 14}},
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
    "Matra": {"you": "1 bowl", "varshit": "1.5 bowls"},
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


st.set_page_config(page_title="Meal Planner", page_icon="🥗", layout="wide")
st.title("Meal Planner")
st.caption("Plan meals, portions, fixed add-ons, calories, and deficit clearly for each person.")

if "grocery_list" not in st.session_state:
    st.session_state.grocery_list = OrderedDict()

top_left, top_right = st.columns([2, 1])
day = top_left.selectbox("Plan for", DATA["days"])
top_right.write("")

if st.session_state.get("selected_day") != day:
    st.session_state.selected_day = day
    defaults = DAY_PLANS.get(day, DAY_PLANS["Today"])
    st.session_state.brunch_name = defaults["brunch"]
    st.session_state.dinner_name = defaults["dinner"]

if st.button("Khane Mein Kya Khaye?"):
    st.session_state.brunch_name = random.choice(dish_names("brunch"))
    st.session_state.dinner_name = random.choice(["Morning Portion Only"] + dish_names("brunch"))

row1, row2 = st.columns(2)
brunch_name = row1.selectbox("Brunch", dish_names("brunch"), key="brunch_name")
dinner_name = row2.selectbox("Dinner", ["Morning Portion Only"] + dish_names("brunch"), key="dinner_name")

st.markdown("**Shreya plan**")
row4, row5 = st.columns(2)
portion_you = row4.text_input("Shreya Brunch Portion", value=PORTIONS[brunch_name]["you"])
dinner_portion_you = row5.text_input("Shreya Dinner Portion", value=PORTIONS[dinner_name]["you"] if dinner_name in PORTIONS else PORTIONS[brunch_name]["you"])
st.markdown("**Shreya fixed add-ons**")
your_checks = st.columns(4)
selected_you = []
for i, item in enumerate(FIXED_ITEM_META["you"]):
    if your_checks[i % 4].checkbox(item, value=True, key=f"you_{item}"):
        selected_you.append(item)
    else:
        for name, qty in FIXED_ITEM_META["you"][item]["ingredients"]:
            st.session_state.grocery_list[name] = qty

st.markdown("**Varshit plan**")
row6, row7 = st.columns(2)
portion_varshit = row6.text_input("Varshit Brunch Portion", value=PORTIONS[brunch_name]["varshit"])
dinner_portion_varshit = row7.text_input("Varshit Dinner Portion", value=PORTIONS[dinner_name]["varshit"] if dinner_name in PORTIONS else PORTIONS[brunch_name]["varshit"])
st.markdown("**Varshit fixed add-ons**")
varshit_checks = st.columns(3)
selected_varshit = []
for i, item in enumerate(FIXED_ITEM_META["varshit"]):
    if varshit_checks[i % 3].checkbox(item, value=True, key=f"varshit_{item}"):
        selected_varshit.append(item)
    else:
        for name, qty in FIXED_ITEM_META["varshit"][item]["ingredients"]:
            st.session_state.grocery_list[name] = qty

brunch = get_dish("brunch", brunch_name)
dinner = dinner_dish(dinner_name)
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

home_tab, calories_tab = st.tabs(["Home", "Calories"])

with home_tab:
    st.subheader("Ingredients Needed")
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
    st.markdown("**Main Ingredients**")
    st.caption("Untick anything not available at home. Missing items will appear in a grocery-reference list below.")
    ingredient_cols = st.columns(2)
    missing = OrderedDict()
    for i, (name, qty) in enumerate(main_ingredients.items()):
        label = f"{name}: {qty}" if qty else name
        available = ingredient_cols[i % 2].checkbox(label, value=True, key=f"ingredient_{name}")
        if not available:
            missing[name] = qty
            st.session_state.grocery_list[name] = qty
    st.markdown("**Add-on Ingredients**")
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
    st.markdown(f"- Brunch: [View {brunch['name']}](#{recipe_slug(brunch['name'])})")
    st.markdown(f"- Dinner: [View {dinner['name']}](#{recipe_slug(dinner['name'])})")

    st.markdown("**Before Didi arrives**")
    st.markdown("- " + "\n- ".join(DATA["daily_routine"]["night_prep"]))
    st.markdown("**Morning routine**")
    st.markdown("- " + "\n- ".join(DATA["daily_routine"]["morning_start"]))

with calories_tab:
    st.dataframe(df.style.apply(style_deficit_row, axis=1), use_container_width=True, hide_index=True)
    you_steps = max(0, round((round(totals["you"]["calories"]) - burn["you"]["total_spent"]) / DATA["people"]["you"]["kcal_per_step"]))
    varshit_steps = max(0, round((round(totals["varshit"]["calories"]) - burn["varshit"]["total_spent"]) / DATA["people"]["varshit"]["kcal_per_step"]))
    st.caption(
        "Walk-step note for weight loss support: "
        f"You may need about {you_steps} extra steps if in surplus. "
        f"Varshit may need about {varshit_steps} extra steps if in surplus."
    )
    st.caption(
        "Calories spent formula used here: resting burn estimated as 22 x body weight (kg), "
        "plus 500 kcal sitting/working, plus calisthenics burn, plus current 2k-step burn."
    )

st.divider()
st.subheader("Recipe View")
for dish in all_recipe_dishes():
    st.markdown(f"<div id='{recipe_slug(dish['name'])}'></div>", unsafe_allow_html=True)
    with st.expander(dish["name"]):
        st.write(dish["summary"])
        st.markdown("**Ingredients**")
        st.markdown("- " + "\n- ".join(f"{item['name']}: {item.get('qty', '')}".rstrip(": ") for item in dish["ingredients"]))
        st.markdown("**Method**")
        st.markdown("- " + "\n- ".join(dish["method"]))
        if dish.get("youtube"):
            st.markdown(f"**YouTube:** [Open recipe video]({dish['youtube']})")
            st.video(dish["youtube"])
