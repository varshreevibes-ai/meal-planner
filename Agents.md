# Agents.md

## Source Of Truth

- Treat [instructions.md](/Users/dusadv/Documents/meal-planner/instructions.md) as the canonical project brief for product behavior, household rules, UI expectations, and planning logic.
- Before changing the planner, align with `instructions.md` first and keep the page behavior consistent with it.

## Python Defaults

- Use the project virtual environment at `.venv`.
- This venv must be created with Python 3.13 and treated as the default Python for project work.
- Run Python with `.venv/bin/python`.
- Run pip with `.venv/bin/pip`.
- If the venv is missing, recreate it with `/usr/local/bin/python3.13 -m venv .venv`.

## Product Rules

- This is a daily planner, not a weekly grid.
- The planner must support two parts of the day:
  - prep before the cook arrives at around 10 AM
  - the cook-facing plan for brunch, add-ons, and dinner
- The page must clearly show:
  - night prep
  - morning start
  - what the cook must make
  - fixed daily items
  - ingredients needed on the right
  - grocery mode guidance
  - body-specific or goal-specific suggestions
- Keep the app centered on Indian vegetarian home meals, while remaining friendly to lighter or more vegan-leaning choices when possible.

## GUI Rules

- For any GUI or interactive app work, use only Streamlit.
- Do not use Tkinter.
- Do not use PyQt, wxPython, Kivy, or any desktop GUI toolkit.
- Do not build desktop-native apps for this project.
- Prefer simple Streamlit layouts and minimal state.
- Optimize the layout for execution clarity over decoration.

## Data Rules

- Keep meal definitions, ingredient lists, methods, routine notes, and grocery logic in local project data files such as `meal_data.yaml`.
- Do not scatter household rules across the code when they belong in structured local data.
- Prefer storing meal metadata like cook summary, approximate protein, calories, and relevant notes close to the meal definitions.

## Code Style

- Prefer fewer lines of code.
- Choose the simplest working solution.
- Avoid over-engineering, deep abstraction, and premature optimization.
- Keep files small and functions focused.
- Use the standard library first unless a dependency clearly saves substantial code.

## Workflow

- Activate the environment with `source .venv/bin/activate` when needed.
- Prefer commands that target the venv directly to avoid shell ambiguity.
- Add small, readable scripts over complex frameworks.
- Write concise docstrings and comments only where they add real clarity.
- When adding dependencies, keep the list short and justify each one by reduced code or clearer behavior.
- When updating the page, prefer improving the existing data-driven structure instead of adding one-off UI logic.

## Testing

- Add lightweight tests when logic is non-trivial.
- Prefer fast unit tests over heavy integration setup.
- Keep test code as small and direct as production code.
- At minimum, keep `app.py` passing `py_compile` after edits.
