# instructions.md

## Purpose

This project is a daily Indian vegetarian (trying to be vegan) meal-planning tool for a two-person household. The planner is not a generic diet app. It must reflect the real household routine, cooking flow, food preferences, body types, digestion needs, protein needs, work-from-home lifestyle, travel breaks, summer food safety, and grocery management patterns shared by the user.

The goal is to help plan a practical day that a cook can execute clearly, with low complexity, low waste, and a gentle daily calorie deficit. It has two components what the couple has to action as prep before the cook comes at around 10 am (soaking, sourcing, deciding) and then cooks part. 

## Core Product Rules

- Build Python work only inside the project virtual environment at `.venv`.
- Use Python 3.13 for the project venv.
- For any GUI or interactive page, use only Streamlit.
- Do not use Tkinter or any desktop GUI toolkit.
- Prefer fewer lines of code and the simplest working implementation.
- Keep data and content stored locally in project files wherever possible.
- Store meal options, ingredients, and cooking methods in YAML or similar local data files rather than hardcoding everything inside the app.

## Planner Scope

The planner is for daily planning, not weekly meal-grid planning. It should contain daily ingredients To the right panel of the page. 
The app should help answer:

- What must be soaked the previous night?
- What must be eaten first thing in the morning?
- What must be cooked in the morning for the whole day?
- What is planned for brunch?
- What are the fixed daily add-ons?
- What is planned for dinner?
- What ingredients are needed for the selected day?
- What should be bought, finished, or avoided depending on whether the household is at home, going on vacation, or returning from travel?
- what can be brought collectively to save economies, also kitchen supplies and other needs restocking. Portion size guide and nutritional value esp. protein intake each person each day. 

## Household Structure

This planner is for two people:

### You

- Constitution: Vata-Pitta
- Goal: gentle calorie deficit, skin glow and proper digestion
- Lifestyle: work from home, little exercise outside 1 hour morning calisthenics
- Preferences:
  - warm cooked meals
  - mango
  - anar
- Digestion guidance:
  - avoid very dry meals
  - avoid very spicy food
  - favor soft, warm, easy-to-digest meals
- Routine:
  - start the day with warm water and ghee
  - protein shake is taken around 3 PM with warm water

### Varshit

- Constitution: Kapha-Pitta
- Goal: gentle calorie deficit with better satiety
- Lifestyle: work from home, little exercise outside 1 hour morning calisthenics
- Preferences:
  - savory meals
  - anar
  - filling brunches
- Digestion and body guidance:
  - keep oil low
  - keep dinner lighter than brunch
  - avoid heavy repeat carbs
  - increase protein before increasing roti or rice
- Routine:
  - has a drink with soya milk and a banana around morning calisthenics
  - should get 3 cucumbers daily as salad
Has. Sattu drinks whole day in summer and tomato soap in winter

## Daily Meal Pattern

The planner should assume this base structure:

- Main cooking happens once in the morning.
- Brunch is the main daytime meal.
- Dinner is at around 7 PM.
- Dinner should usually be either:
  - a lighter, smaller meal, or
  - a measured portion of the morning meal saved for later
- The overall day should aim for a calorie deficit, while keeping digestion manageable and food complexity low.

## Fixed Daily Items

These are not optional extras. They are part of the normal daily plan and should be visible prominently in the planner.

- Daily sattu drink Varshit mainly
- Daily anar
  - one bowl each
- Soaked dates Shreya
- Soaked almonds Shreya
- Soaked pumpkin seeds Shreya
- Soaked kali kishmish Shreya
- Digestion aids:Shreya and varshit
  - cumin
  - coriander
  - fennel
- Daily protein support
  - Varshit: soya milk plus banana around morning calisthenics
  - You: protein shake around 3 PM with warm water
3 cucumber as salad for varshit each day

## Night Prep Requirements

The app and instructions must clearly show what needs to be prepared the previous night.

Night prep should include:

- Soak dates, almonds, pumpkin seeds, and kali kishmish for the next morning.
- Check that all required ingredients for next day brunch, daily add-ons, and dinner are already available in the kitchen.
- Soak rajma overnight if `Rajma Chawal` is planned.
- Soak chhole overnight if a chhole or chane-based meal is planned.
- Wash and keep cucumbers ready for Varshit’s daily salad.
- Check whether sattu, protein powder, and soya milk are running low and refill or restock if needed.
- If a meal needs batter, legumes, or advance prep, this should be visible in the top planning section.

## Morning Routine Requirements

The top planning section must clearly show the morning routine, especially for the cook and household execution.

Morning routine should include:

- You start with warm water and ghee.
- Serve soaked dates, almonds, pumpkin seeds, and kali kishmish.
- Varshit has soya milk plus banana around morning calisthenics.
- Prepare anar bowls for both.
- Keep digestion aids ready for the day.
- Start the main cooking for brunch and dinner.

## Cooking Workflow Requirements

The application should reflect a cook-friendly operational flow:

- The top section must clearly say what needs what needs to be cooked with soaking, what is eaten in the morning, as note under the table for the food selected
- The table at the top must be usable by Didi.
- It should not be vague.
- It should explicitly call out:
  - night prep
  - morning start
  - brunch item
  - daily add-ons
  - dinner item
- Summer-sensitive items should be portioned and refrigerated early.

## Meals To Include

The brunch meal list should include the user’s real meals, not generic filler meals.

Brunch options should include:

- Avocado Toast
- Chhole Tikki Rolls
- Idli Sambar
- Bhaji Roti
- Chane Sabji Roti
- Tofu Tikka Roll
- Daal Chawal
- Rajma Chawal
- bharta began
- uttapam for Varshit and Ghee podi dosa for shreya
- 

Dinner should stay lighter in spirit and may include:

Something from the brunch list only

The planner may include more meals later, but new meals should still follow:

- Indian vegetarian household style
- low or manageable complexity
- digestion-aware portions
- calorie deficit compatibility
- realistic cook-once household routine

## Fruits And Add-On Logic

The fruit/add-on section should support daily routines, not random fruit picking.

Base add-on logic:

- anar is daily and fixed
- soaked dry fruits and seeds are daily first thing morning 
- sattu is daily during the afternoon til evening
- digestion aids are daily after evening meal

Optional fruit additions can include:

- mango for you
- papaya as a lighter digestion-friendly fruit option good suggestion
Machine bhune air fried, chane

Guidance:

- Mango should usually be a smaller separate portion.
- Mango should not be treated as a default heavy dessert after a large meal.
- Papaya is useful on hotter days or lighter digestion days.

## Body-Specific Guidance

Suggestions shown in the app can be personalized, but should follow the rules below.

### For You

- Prefer warm, moist, cooked meals.
- Favor soft textures over dry, crunchy, or overly toasted meals.
- Keep spice moderate.
- Keep digestion easy.
- Mango can be included but in a modest amount.
- Warm water-based routines are preferred.

### For Varshit

- Favor higher satiety through protein first.
- If hunger is still high, increase protein before adding more grains.
- Keep dinner small and lighter.
- Support salad intake with 3 cucumbers daily.
- Keep oily and overly heavy foods low.

## Protein Guidance

The planner does not need exact medical nutrition logic, but it should respect the user’s stated need for differentiated protein support.

Approach:

- Use paneer, chana, chhole, rajma, dal, moong chilla, curd, sattu, and shakes strategically.
- For Varshit, increase protein before increasing breads or rice.
- For you, keep protein support digestion-friendly and not overly heavy.
- Highlight protein notes in meal descriptions where useful.

## Digestion Guidance

The planner should consistently respect digestion complexity.

Principles:

- Keep dinner lighter than brunch.
- Prefer easier digestion on hot days or when meals are already heavy at brunch.
- Use cumin, coriander, and fennel regularly as digestion aids.
- Avoid overly oily, dry, or very spicy patterns.
- Moist, warm, simply cooked meals are better aligned for the user.
- Heavy brunch meals like rolls or rajma chawal should be balanced with a lighter dinner.

## Grocery Management Requirements

The planner must support grocery states, not just recipe selection. 
- Home maintain regular supplies based on average consumption estimates
- have to leave for Vacation = lower grocery sourcing and finish off current things
- Return - source all the daily needs and tomorrow and day after to have economies of scale

### Home Mode

Should emphasize:

- keeping daily essentials stocked
- buying shorter-cycle produce in summer
- carrying enough ingredients for fixed daily items
- buying only 2 to 3 days of paneer at a time

### Vacation Mode

Should emphasize:

- reducing perishables
- buying only short-window fruit
- avoiding bulk vegetables
- avoiding waste in dairy and cooked food
- buying only enough sattu, protein powder, and soya milk for the remaining trip window

### Return Mode

Should emphasize:

- restarting with minimum groceries
- using easy meals first
- buying basics only for the first 1 to 2 days
- rebuilding inventory slowly

## Summer Handling Requirements

Summer makes the storage window shorter, so the planner must account for that.

Summer rules:

- Refrigerate dinner portions early.
- Keep cut fruit fresh and not stored too long.
- Keep curd and chopped salad separate until serving.
- Soak only the quantity of dry fruits and seeds needed for the next day.
- Prefer shorter grocery cycles during hotter weeks.
- Avoid overstocking perishables before travel.

## UI Requirements

The Streamlit page should be designed around execution clarity.

The page should include:

- a top planning table
- brunch dropdown
- daily add-ons - fixed portion and optional additional
- option to rearrange the meal plan to be consumed duringng the day logically to finish it in the day itself and avoid over stuffing
- dinner dropdown
- a right-side ingredient list for all selected items
- nutritional value in total for the day in calories and protein and other nutrients.
- keep daily spent calories content calculated as: usual day to day + calisthenics session and display net deficit on the right top corner
- grocery mode guidance
- storage/summer notes

The top table should be especially clear because it is intended for the household cook.


For each relevant row, top table for the cook should show:

- selected item or routine label
- what to do
- cooking or prep time where relevant

Followed by a similar tape for next day. And have option to account for left overs from previous day

## Ingredient List Requirements

The ingredient list on the right should show everything needed for the chosen day.

It should combine:

- ingredients from brunch
- ingredients from daily add-ons
- ingredients from dinner
- daily routine items

It is acceptable to improve this later by summing repeated ingredients more intelligently.

## Data Storage Requirements

Meal data and planner logic should be stored locally in project files.

Recommended structure:

- `meal_data.yaml` for:
  - people
  - daily routine
  - fixed daily items
  - meal sections
  - grocery modes
  - storage notes
- `app.py` for Streamlit rendering logic
- `instructions.md` for the full planning and product requirements

Each meal definition should ideally include:

- name
- summary
- cook summary
- cook time
- complexity
- protein note
- suggestions for you
- suggestions for Varshit
- ingredients
- method

## Quality Bar

Any future work on this project should preserve the following:

- low complexity
- low waste
- strong execution clarity
- realistic Indian veg household context
- daily routine visibility
- cook-friendly instructions
- digestion awareness
- calorie deficit direction
- separate needs for you and Varshit

## What Not To Do

- Do not turn this into a generic calorie-tracker-first product.
- Do not switch to desktop GUI frameworks.
- Do not hide key routine instructions deep in the page.
- Do not ignore soaking or night prep needs.
- Do not design only around recipes while forgetting household operations.
- Do not recommend heavy dinner defaults.
- Do not overcomplicate the codebase when a simple Streamlit plus YAML approach works.
