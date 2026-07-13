# Product Specification

Last updated: 2026-07-13
Canonical brief reference: [instructions.md](/Users/dusadv/Documents/meal-planner/instructions.md)
Primary implementation: [app.py](/Users/dusadv/Documents/meal-planner/app.py), [meal_data.yaml](/Users/dusadv/Documents/meal-planner/meal_data.yaml)

## Status Legend

| Status | Meaning |
| --- | --- |
| Implemented | Verified in current repository code and reachable in the app. |
| Partially implemented | Verified in code, but incomplete, simplified, legacy, dormant, or only partly wired into the main UX. |
| Planned | Requested by product brief, but not yet implemented in verified code. |
| Recommended | Strong default for future implementation; not yet committed in code. |
| Deferred | Intentionally left out of MVP for now. |
| Removed | Older concept exists only as migration/compatibility logic or is no longer exposed as a first-class feature. |

## 1. Product Purpose, Users, Goals, Core Principles

**Purpose**

- `Implemented`: A Streamlit household meal-planning and home-management app centered on Indian vegetarian home meals and daily routine planning.
- `Implemented`: Primary planner flow focuses on one day at a time, not a weekly grid.
- `Implemented`: The app also includes recipes, purchase logging, inventory, shopping, and insights.

**Primary users**

- `Implemented`: A local app user identified by a manually entered user ID at app open.
- `Implemented`: Within each user, one active household profile with one or more household members.
- `Recommended`: Treat the core target household as Shreya + Varshit, but keep the data model generic for up to 5 members.

**Goals**

- `Implemented`: Help plan brunch, dinner, routine add-ons, and ingredient readiness.
- `Implemented`: Help track purchases, current stock, shopping needs, and simple spend/consumption patterns.
- `Planned`: Fully represent the exact cook-facing “before cook arrives around 10 AM” workflow from `instructions.md`.
- `Planned`: Keep stronger digestion-aware, body-specific, and household-rule-specific logic in structured data rather than code constants.

**Core principles**

- `Implemented`: Streamlit only.
- `Implemented`: Local file storage, minimal dependencies.
- `Implemented`: Data-driven built-in meals from YAML.
- `Recommended`: Preserve current behavior unless a requested change explicitly alters it.

## 2. Current Application Structure and Implementation Status

| Area | Status | Verified implementation |
| --- | --- | --- |
| User gate | Implemented | `render_user_gate()` in [app.py](/Users/dusadv/Documents/meal-planner/app.py) |
| Per-user storage | Implemented | `data/<user_id>/profiles_data.json` via `user_profile_store_path()` |
| Device remember-me | Implemented | [data/device_user.json](/Users/dusadv/Documents/meal-planner/data/device_user.json) |
| Daily planner | Implemented | `render_planner_workspace()` |
| Built-in recipes | Implemented | [meal_data.yaml](/Users/dusadv/Documents/meal-planner/meal_data.yaml) |
| Custom recipes | Implemented | Profile-level `recipes`, `render_recipes_workspace()` |
| Meal templates | Partially implemented | Data model + editor code exist, planner uses templates if present, but no first-class workspace for templates |
| Meal log | Implemented | `logMeal()`, `MealLogTab()` |
| Inventory data model | Implemented | `inventory`, `lots`, `inventory_transactions`, categories, vendors, locations |
| Inventory UI | Partially implemented | Simplified table UI is active; richer detailed inventory editors exist in code but are not the main current flow |
| Home supplies | Partially implemented | Concept exists in categorization and setup; current UI is folded into Inventory |
| Shopping list | Implemented | `render_shopping_workspace()` |
| Purchase log | Implemented | `render_purchase_log_workspace()` |
| Insights | Implemented | `render_insights_workspace()` |
| Import review pipeline | Partially implemented | CSV/text/manual review exists; invoice image OCR is stubbed/fallback only |
| Authentication/authorization | Partially implemented | Local user-ID isolation only; no password or server auth |

## 3. Navigation, Tabs, Terminology, Cross-Feature Relationships

**Top-level workspaces**

- `Implemented`: `Planner`
- `Implemented`: `Recipes`
- `Implemented`: `Purchase Log`
- `Implemented`: `Inventory`
- `Implemented`: `Shopping`
- `Implemented`: `Insights`

Verified in `DESKTOP_WORKSPACE_TABS` and `PLANNER_NAV_WORKSPACES` in [app.py](/Users/dusadv/Documents/meal-planner/app.py).

**Planner internal tabs**

- `Implemented`: `Ingredients & Recipe`
- `Implemented`: `Calories`
- `Implemented`: `Meal Log`

**Insights internal tabs**

- `Implemented`: `Consumption`
- `Implemented`: `Price Analysis`
- `Implemented`: `Vendor Comparison`
- `Implemented`: `Predictions`

**Purchase Log internal intake tabs**

- `Implemented in code`: `Manual`, `Text`, `Voice`, `Invoice Image`
- `Partially implemented`: Voice and invoice image do not currently perform robust parsing.

**Terminology rules**

- `Implemented`: “Planner” means daily meal plan selection plus grocery readiness.
- `Implemented`: “Recipe” means built-in YAML recipe or custom profile recipe.
- `Implemented`: “Meal template” means a named planner option that may link to a recipe.
- `Implemented`: “Inventory” includes food inventory and household supplies in the current navigation.
- `Removed`: Separate top-level `Home Supplies` workspace is normalized back to `Inventory`.
- `Removed`: Separate top-level `Setup` workspace is normalized back to `Planner`; setup is embedded in planner-related code but not current main navigation.

**Cross-feature relationships**

- `Implemented`: Planner ingredient availability can populate `grocery_data.missing_items`.
- `Implemented`: Shopping merges planner missing items, manual shopping rows, and rows marked out-of-stock in simple inventory/purchase tables.
- `Implemented`: Purchase Log saves rows and can feed shopping completion and item/vendor memory.
- `Implemented`: Inventory lots and transactions feed Insights.
- `Implemented`: Recipes can be opened from Planner ingredient section.
- `Partially implemented`: Meal templates can drive planner options but are not surfaced as a dedicated main feature.

## 4. User, Household, Household-Member Data Ownership

**Ownership layers**

1. `Implemented`: Device-level preference
   - File: [data/device_user.json](/Users/dusadv/Documents/meal-planner/data/device_user.json)
   - Stores remembered `planner_user_id`
2. `Implemented`: User-level store
   - Path pattern: `data/<normalized_user_id>/profiles_data.json`
   - Created/loaded by `load_profile_store()`
3. `Implemented`: Household profile level
   - `profiles[]` inside the user store
   - Only one `active_profile_id` at a time
4. `Implemented`: Household-member level
   - `household_members[]` within a profile

**Profile owns**

- `Implemented`: Household members
- `Implemented`: Meal templates
- `Implemented`: Custom recipes
- `Implemented`: Inventory items
- `Implemented`: Inventory transactions
- `Implemented`: Vendors
- `Implemented`: Storage locations
- `Implemented`: Shopping manual rows/items
- `Implemented`: Purchase log rows
- `Implemented`: Meal log
- `Implemented`: Leftovers
- `Implemented`: Preferences and planner/shopping state persisted to file

**Member owns**

- `Implemented`: Name
- `Implemented`: Portion ratio
- `Implemented`: Gym/walk flags
- `Implemented`: Intake items free text
- `Partially implemented`: Additional routine-related member fields exist in schema but are not actively edited in current member form

## 5. Strict Household and Member Data-Isolation Rules

**User isolation**

- `Implemented`: A user ID maps to one filesystem subtree under `data/<user_id>/`.
- `Required`: Never read or write another user’s store while a different `planner_user_id` is active.
- `Required`: New features must continue to scope all persistent state to the active user store path.

**Profile isolation**

- `Implemented`: State changes persist only to the active profile within the active user store.
- `Required`: References between recipes, templates, vendors, locations, inventory items, and logs must stay within the same profile.

**Member isolation**

- `Implemented`: Member data is embedded only inside its profile.
- `Required`: Member-specific routines, logs, preferences, and future metrics must never be shared across profiles or users.

**Migration exceptions**

- `Removed / compatibility only`: Root [profiles_data.json](/Users/dusadv/Documents/meal-planner/profiles_data.json) and [meal_log.json](/Users/dusadv/Documents/meal-planner/meal_log.json) are legacy sources.
- `Implemented`: `migrate_legacy_profile_store_for_user()` migrates only for normalized user ID `shreya`.
- `Required`: No new features should use root-level legacy stores as primary persistence.

## 6. Onboarding, Setup, Profile Creation, Editing, Deletion

**Current onboarding**

- `Implemented`: App opens on a user-ID gate.
- `Implemented`: User ID is normalized to lowercase letters/numbers/hyphen/underscore.
- `Implemented`: Missing user store auto-creates a default profile store with one empty profile named `New Household`.

**Profile management**

- `Implemented in data model`: Multiple profiles per user store are supported.
- `Partially implemented`: Current main UI does not expose a full profile switcher/creator/deleter workflow.

**Household setup**

- `Partially implemented`: `render_setup_panel()` supports:
  - used categories
  - members
  - routines
  - goals
  - vendors
  - storage locations
  - inventory defaults
  - home supplies defaults
  - categories
  - item aliases
- `Partially implemented`: This setup panel is not a current top-level workspace, so setup UX is not fully discoverable.

**Member create/edit/delete**

- `Implemented`: Add/edit/delete within `render_household_manager()`
- `Implemented`: Max 5 members
- `Implemented`: First member’s portion ratio is fixed to `1.0`
- `Implemented`: Delete requires confirmation

**Deletion rules**

- `Implemented`: Member deletion removes only that member object.
- `Implemented`: Vendor/location deletion is blocked when linked inventory data exists.
- `Planned`: Profile deletion workflow.

## 7. Planner, Meal Templates, Meal Logging, Portions, Routines

**Planner scope**

- `Implemented`: Daily planner, no weekly planning UI.
- `Implemented`: Brunch and dinner selection.
- `Implemented`: Dinner can be `Morning Portion Only`.

**Planner sources**

- `Implemented`: Built-in brunch choices from `meal_data.yaml`
- `Partially implemented`: Meal templates augment planner choices if present.

**Portions**

- `Implemented`: Suggested portions come from:
  - hardcoded `PORTIONS` for built-ins
  - portion ratios for templates
  - leftover defaults for `Morning Portion Only`
- `Implemented`: User can type free-form portions.
- `Partially implemented`: Portion parsing for calorie math uses first numeric value from text via `portion_factor()`.
- `Recommended`: Future validation should separate display text from numeric servings.

**Routines**

- `Implemented`: Night prep and morning routine sections are shown in Planner.
- `Partially implemented`: Current routine output is built from profile free text plus member intake items, not fully from the richer `instructions.md` structure.

**Meal logging**

- `Implemented`: “Note what I ate today” logs the current brunch selection only.
- `Implemented`: Meal log stores planned/actual servings, leftovers, recipe ref, calories, protein.
- `Partially implemented`: Logging does not separately log dinner consumption or per-add-on consumption.

**Meal templates**

- `Partially implemented`: Templates can store name, description, linked recipe ref, favorite.
- `Partially implemented`: Template editor exists in code, but is not exposed as a dedicated workspace.

## 8. Recipes, Ingredients, Instructions, Links, Recipe Navigation

**Built-in recipes**

- `Implemented`: Stored in [meal_data.yaml](/Users/dusadv/Documents/meal-planner/meal_data.yaml).
- `Implemented`: Include summary, ingredients, method, and optional YouTube link.

**Custom recipes**

- `Implemented`: Profile-scoped recipes can be added from Recipes workspace.
- `Implemented`: Fields include name, description, base servings, ingredients, instructions, optional YouTube URL.
- `Implemented`: Custom recipe ingredients scale to household serving total.

**Recipe navigation**

- `Implemented`: Planner can open linked brunch/dinner recipes.
- `Implemented`: Recipes workspace uses anchor scrolling and expanders.

**Recipe linking**

- `Implemented`: Recipe refs support `builtin::<name>` and `profile::<id>`.
- `Partially implemented`: Templates can link to either built-in or profile recipe.

**Validation**

- `Implemented`: Recipe name required for quick add.
- `Planned`: Prevent duplicate recipe names more explicitly and validate YouTube/URL formats.

## 9. Inventory, Stock Adjustments, Capacity, Refill Levels, Expiry

**Inventory model**

- `Implemented`: `inventory[]` items with:
  - category
  - unit
  - refill level
  - storage capacity
  - shelf life
  - preferred vendor/brand
  - preferred purchase quantity/unit
  - aliases
  - notes
  - `lots[]`
- `Implemented`: `inventory_transactions[]`

**Lot model**

- `Implemented`: Lots store quantity, unit, status, purchase/open/expiry date, location, vendor, brand, price, notes.

**Current inventory UX**

- `Implemented`: Active workspace is simplified editable tables:
  - `Kitchen Inventory`
  - `Household Items`
- `Partially implemented`: Advanced item/lot editors and adjustment forms exist in code but are not the current main UX.

**Capacity/refill/expiry**

- `Implemented in schema`: Item `storage_capacity`, item `refill_level`, location capacity, category shelf life.
- `Partially implemented`: Insights and status helpers can compute low stock/expiring/over-capacity, but these are not the primary active inventory screen today.

**Stock adjustments**

- `Implemented in code`: Add/deduct/set exact/move/mark expired/spoiled/lost/given away/manual correction forms exist.
- `Partially implemented`: These workflows are not the current primary inventory interaction path.

## 10. Home Supplies and Recurring Household Consumables

**Current behavior**

- `Implemented`: Home supplies are represented through categories such as `Cleaning`, `Laundry`, `Paper / Disposables`, `Personal Care`, `Utilities`, `Maintenance`, `Bathroom`, `Kitchen Non-Food`, `Other Supplies`, `Home Supplies`.
- `Implemented`: Name-based heuristics classify many purchase items as home supplies.
- `Removed`: Separate top-level workspace is no longer used.

**Required product rule**

- `Recommended`: Continue treating home supplies as first-class inventory entities with shared shopping and purchase flows, but keep them visually separated from kitchen food items where possible.

## 11. Shopping Lists, Sources, Grouping, Editing, Completion Flows

**Current sources merged into Shopping**

- `Implemented`: Planner missing ingredients
- `Implemented`: Kitchen inventory rows marked not in stock
- `Implemented`: Household inventory rows marked not in stock
- `Implemented`: Purchase log rows marked not in stock
- `Implemented`: Manual shopping rows

**Current behavior**

- `Implemented`: Editable shopping table with vendor/item/quantity/category/note/source.
- `Implemented`: Marking purchased updates the source row or removes manual/planner rows.
- `Implemented`: Planner-origin purchased rows clear `grocery_data.missing_items`.

**Not yet implemented**

- `Planned`: Strong vendor grouping UX
- `Planned`: Dedicated completion history
- `Planned`: Multi-step confirmation for bulk completion

## 12. Purchase Log, Natural-Language Input, Review Tables, Vendors, Prices

**Purchase Log workspace**

- `Implemented`: Free-text “Log what I just bought”.
- `Implemented`: Parser handles `Vendor: item quantity price` style lines and related variants.
- `Implemented`: Review table before saving.
- `Implemented`: Saved rows go into `purchase_log_rows`.

**Natural-language and import support**

- `Implemented in code`: Manual entry
- `Implemented in code`: Plain text parsing
- `Implemented in code`: CSV import parsing helpers
- `Partially implemented`: Voice flow is UI-only, no real speech-to-text pipeline in repo
- `Partially implemented`: Invoice image flow is stubbed unless helper text is supplied

**Vendors and prices**

- `Implemented`: Purchase rows store vendor and price.
- `Implemented`: Item memory learns remembered vendor/category associations.
- `Implemented`: Price summary and vendor comparison derive from saved inventory lots and purchase history.

## 13. Insights, Consumption Estimates, Price Trends, Prediction Limits

**Implemented insight outputs**

- `Consumption`: weekly/monthly averages, average purchase interval, average consumed per event, trend, confidence
- `Price Analysis`: last/average/lowest/highest price, trend, best vendor
- `Vendor Comparison`: aggregated vendor rows
- `Predictions`: item prediction rows

**Prediction limits**

- `Implemented`: Low-data states are explicitly shown.
- `Required`: Predictions must remain advisory only.
- `Recommended`: Never present health, nutrition, waste, or depletion forecasts as precise guarantees.

## 14. Mobile-First and Desktop-Responsive UX Requirements

**Verified current state**

- `Implemented`: Sidebar navigation with collapsed initial state.
- `Implemented`: Streamlit layout is desktop-responsive enough to function on smaller screens.
- `Partially implemented`: Many planner and setup sections still rely on multi-column layouts that may feel dense on mobile.

**Required future requirements**

- `Recommended`: Design mobile-first for all new flows.
- `Recommended`: Keep key actions visible without excessive scrolling.
- `Recommended`: Tables should have a mobile fallback view when columns exceed screen width.

## 15. Loading, Empty, Error, Confirmation, Accessibility States

**Implemented**

- Empty states for members, recipes, meal log, shopping, insights, inventory-related areas
- Success toasts/messages after saves and logs
- Error messages for invalid user ID, blank member name, blank recipe name, parser failures
- Delete confirmations for members, vendors, locations

**Partially implemented**

- Loading states are mostly implicit; no systematic skeleton/loading pattern
- Accessibility is limited by Streamlit defaults and custom CSS

**Required**

- `Recommended`: Every destructive action should require confirmation.
- `Recommended`: All forms should show inline validation near the edited field.
- `Recommended`: Preserve keyboard navigation and readable contrast when editing theme CSS.

## 16. Indian Heritage-Inspired Visual Design System and Theme Tokens

**Current implementation**

- `Implemented`: Dark, heritage-inspired theme injected by `inject_ui_styles()`
- `Implemented`: Asset-backed motifs from:
  - [assets/pichwai-page-bg-optimized.jpg](/Users/dusadv/Documents/meal-planner/assets/pichwai-page-bg-optimized.jpg)
  - [assets/pichwai-sidebar-bg-optimized.jpg](/Users/dusadv/Documents/meal-planner/assets/pichwai-sidebar-bg-optimized.jpg)
  - [assets/mandala-ribbon.jpg](/Users/dusadv/Documents/meal-planner/assets/mandala-ribbon.jpg)
  - [assets/mandala-button.jpg](/Users/dusadv/Documents/meal-planner/assets/mandala-button.jpg)

**Current tokens**

- `Implemented`: `--color-bg`, `--color-surface`, `--color-panel`, `--color-primary`, `--color-secondary`, `--color-accent-brass`, `--color-banana-leaf`, `--color-diya-flame`, `--color-text-primary`, `--color-text-secondary`, `--color-border`, others

**Design rule**

- `Recommended`: Preserve the Indian heritage-inspired direction, but favor legibility and execution clarity over visual decoration.

## 17. Suggested Entities, Fields, Relationships, Indexes, Deletion Rules

**Current entities**

- `Implemented`: User preference record
- `Implemented`: Profile store
- `Implemented`: Profile
- `Implemented`: Household member
- `Implemented`: Meal template
- `Implemented`: Custom recipe
- `Implemented`: Inventory category
- `Implemented`: Storage location
- `Implemented`: Vendor
- `Implemented`: Inventory item
- `Implemented`: Inventory lot
- `Implemented`: Inventory transaction
- `Implemented`: Purchase log row
- `Implemented`: Simple kitchen inventory row
- `Implemented`: Simple household inventory row
- `Implemented`: Simple shopping manual row
- `Implemented`: Meal log entry
- `Implemented`: Leftover record

**Recommended key relationships**

- Profile `1:n` household members
- Profile `1:n` recipes
- Profile `1:n` meal templates
- Template `0..1 -> recipe_ref`
- Profile `1:n` inventory items
- Inventory item `1:n` lots
- Inventory item `1:n` transactions
- Profile `1:n` vendors
- Profile `1:n` storage locations
- Profile `1:n` purchase rows
- Profile `1:n` meal log entries

**Recommended logical indexes for future migrations**

- User store by normalized user ID
- Profile by `id`
- Member by `id`
- Recipe by `id`, name lowercase
- Template by `id`, name lowercase
- Inventory item by `id`, name lowercase
- Lot by `id`
- Transaction by `id`, item_id + created_at
- Vendor by `id`, name lowercase
- Location by `id`, name lowercase
- Meal log by `id`, logged_at

**Deletion rules**

- `Implemented`: Vendor/location deletion blocked when directly linked to inventory data.
- `Recommended`: Recipe deletion should be blocked or warn when referenced by a meal template.
- `Recommended`: Profile deletion should require explicit confirmation and never cascade across users.

## 18. Validation Rules for Quantities, Prices, Dates, Ownership, References

**Current validation in code**

- `Implemented`: Numeric parsing uses `try_float()`
- `Implemented`: Empty/invalid user IDs are rejected
- `Implemented`: Member name and recipe name are required

**Required validation rules**

- Quantities
  - `Recommended`: Must be `>= 0`
  - `Recommended`: Zero quantity lots/items should only be allowed for historical/finished records, not active stock
- Prices
  - `Recommended`: Must be `>= 0`
- Dates
  - `Recommended`: Use ISO `YYYY-MM-DD` for stored date-only fields
  - `Recommended`: Expiry date cannot be before purchase date when both are present
- Ownership
  - `Required`: Referenced IDs must belong to the active profile
- References
  - `Required`: `profile::recipe_id` must resolve only within the same profile
  - `Required`: Unknown refs should fail safe and not crash planner rendering

## 19. Derived Calculations and Inventory Transaction Rules

**Current derived calculations**

- `Implemented`: Household servings = sum of member portion ratios
- `Implemented`: Template recipe scaling = household servings / base servings
- `Implemented`: Planner calorie and protein estimates from `NUTRITION`
- `Implemented`: Planner deficit/surplus estimate from simplified burn model
- `Implemented`: Inventory total quantity = sum of active lot quantities
- `Implemented`: Price/unit summaries derived from purchase history
- `Implemented`: Usage metrics derived from inventory transactions

**Transaction rules**

- `Implemented`: Purchases add lots and inventory transactions
- `Implemented`: Finished/expired states remove lots from active stock totals
- `Recommended`: Every quantity-changing inventory action should append a transaction row
- `Recommended`: Derived analytics should prefer transaction history over mutable item totals

## 20. Security, Privacy, Performance, Authorization Requirements

**Current state**

- `Implemented`: Local-only file persistence
- `Implemented`: No remote API usage in repository
- `Partially implemented`: Authorization is only “enter a user ID”

**Requirements**

- `Required`: Do not leak one user’s data into another user’s store or session.
- `Required`: Do not use root legacy files for new writes.
- `Required`: Preserve per-user filesystem scoping.
- `Recommended`: Treat remembered user ID as convenience, not security.
- `Recommended`: Keep file writes atomic where practical if persistence is refactored.
- `Recommended`: Avoid O(n^2) scans in large tables if the app grows, but current scale is small.

## 21. Cross-Feature Workflows and Required User Confirmations

**Current workflows**

- Planner -> missing ingredients -> Shopping
- Planner -> open recipe -> Recipes
- Purchase Log -> review -> save -> Purchase History
- Shopping -> mark purchased -> update source rows
- Recipes -> add custom recipe -> Planner can use via template if template created

**Confirmation requirements**

- `Implemented`: Delete member/vendor/location confirmation
- `Required`: Any future delete of recipe/template/profile/inventory item must confirm first
- `Recommended`: Bulk shopping completion should confirm before changing multiple rows

## 22. Build Phases, Priorities, Dependencies, Migration Needs

**Phase 1: Stabilize current product**

- Keep user/profile isolation intact
- Keep daily planner working
- Keep recipes, purchase log, shopping, inventory, insights working
- Add tests around normalization and persistence

**Phase 2: Reconcile product brief with implementation**

- Move more routine/body-rule logic out of `app.py` constants into structured data
- Expose setup/profile flows more clearly
- Decide whether advanced inventory model or simplified table model is the source-of-truth UX

**Phase 3: Fill major feature gaps**

- Stronger meal template workflow
- Better purchase import/OCR/voice handling
- Better planner logging for full day

**Migration needs**

- `Implemented`: Legacy migration for `shreya`
- `Recommended`: Future migrations should preserve profile IDs and existing links

## 23. Explicit MVP Non-Goals and Deferred Features

- `Deferred`: Weekly meal-grid planner
- `Deferred`: Multi-user concurrent collaboration
- `Deferred`: Cloud sync and remote auth
- `Deferred`: Medical-grade nutrition logic
- `Deferred`: Exact barcode scanning
- `Deferred`: Reliable invoice OCR without a proper OCR dependency/service
- `Deferred`: Native mobile app

## 24. Feature-by-Feature Acceptance Criteria and Testing Requirements

| Feature | Acceptance criteria | Minimum testing |
| --- | --- | --- |
| User gate | Valid user ID opens app; invalid ID is rejected; remembered ID reloads correctly | Unit tests for `normalize_user_id()`, manual run |
| User isolation | Writes go only to `data/<active_user>/profiles_data.json` | Unit tests for path helpers, manual cross-user check |
| Planner | Brunch/dinner render; portions update; ingredients and routines show; meal can be logged | Manual run with 1-member and 2-member profiles |
| Recipes | Built-in recipes load; custom recipes save and render; links do not crash | Unit tests for recipe normalization; manual add/edit |
| Meal log | Logged meals persist and display; delete works | Unit tests for `normalize_meal_log_entry()`, manual delete |
| Meal templates | Templates resolve linked recipes inside planner | Unit tests for `resolve_linked_recipe()` and `option_to_dish()` |
| Purchase Log | Free text parses into review rows; reviewed rows save | Unit tests for `simple_parse_purchase_line()` |
| Inventory | Items/lots normalize correctly and persist | Unit tests for item/lot normalization |
| Shopping | Source rows merge into shopping; purchased rows update source state | Unit tests for `simple_build_shopping_rows()` / `simple_apply_shopping_row_change()` |
| Insights | Low-data states are safe; metrics render with saved data | Unit tests for summary helpers where feasible |
| App syntax | `app.py` compiles | `./.venv/bin/python -m py_compile app.py` |

## 25. Open Product or Architecture Decisions with Recommended Defaults

| Decision | Current state | Recommended default |
| --- | --- | --- |
| Is this only a meal planner or a broader household manager? | Code supports both | Keep meal planner as primary, household management as supporting surfaces |
| Should setup be a first-class workspace? | Code exists but not exposed | Re-expose setup inside Planner or as a clearly labeled profile/settings area |
| Should advanced inventory forms remain or be removed? | Both advanced and simplified models coexist | Keep one canonical UX and delete dormant duplicate flows after migration |
| Should meal templates be exposed in UI? | Data model exists, not first-class | Add a visible templates section under Planner or Recipes |
| How should body-specific rules be stored? | Split across YAML, constants, and free text | Move structured household rules into local data files |
| Should dinner logging be separate from brunch logging? | Current meal log is brunch-centric | Yes, add explicit dinner logging when implementing richer logs |
| How should home supplies appear in navigation? | Folded into Inventory | Keep one Inventory workspace with clear kitchen vs household separation |
| How should invoice image parsing work? | Stubbed | Keep placeholder until a real OCR path is chosen |
| Should multiple profiles be manageable in UI? | Data model supports it | Yes, but only after isolation and migration flows are tested |

## 26. Repository Map with Relevant Files and Implementation Gaps

| Path | Role | Status / gap |
| --- | --- | --- |
| [app.py](/Users/dusadv/Documents/meal-planner/app.py) | Main Streamlit app, storage logic, UI, calculations | Large monolith; multiple active and dormant flows coexist |
| [meal_data.yaml](/Users/dusadv/Documents/meal-planner/meal_data.yaml) | Built-in meals, routines, ingredients, methods | Good source for built-ins; not yet the only source of household rules |
| [requirements.txt](/Users/dusadv/Documents/meal-planner/requirements.txt) | Dependencies | Minimal and appropriate |
| [instructions.md](/Users/dusadv/Documents/meal-planner/instructions.md) | Canonical product brief before this spec | Broader than current implementation |
| [profiles_data.json](/Users/dusadv/Documents/meal-planner/profiles_data.json) | Legacy profile store | Migration/compatibility only |
| [meal_log.json](/Users/dusadv/Documents/meal-planner/meal_log.json) | Legacy meal log | Migration/compatibility only |
| [data/device_user.json](/Users/dusadv/Documents/meal-planner/data/device_user.json) | Remembered user ID | Device convenience only |
| [data/shreya/profiles_data.json](/Users/dusadv/Documents/meal-planner/data/shreya/profiles_data.json) | Example active user store | Confirms real-world use of per-user scoped data |
| [assets/...](/Users/dusadv/Documents/meal-planner/assets) | Theme art | Active design assets |

**Major verified gaps**

- The canonical brief expects a stricter cook-facing daily workflow than the current planner enforces.
- Home supplies and setup exist conceptually, but the main navigation has been simplified and some older code paths are dormant.
- Invoice image and voice purchase intake are not fully implemented.
- Multiple profile support exists in storage but lacks a full current UI.
- Meal template capability exists but lacks first-class discoverability.
- Advanced inventory model and simple table model coexist, creating ambiguity.

## 27. Instructions for Keeping This Specification Updated

- Update this file whenever behavior, persistence, navigation, validation, or data ownership changes.
- Verify code before editing the spec; do not document features that are only intended.
- Mark each changed area with the correct status: `Implemented`, `Partially implemented`, `Planned`, `Recommended`, `Deferred`, or `Removed`.
- Use real repository paths and function names where helpful.
- Add a new changelog entry for every meaningful spec update.
- If behavior changes, update acceptance criteria and open decisions in the same edit.
- If storage shape changes, update Sections 4, 5, 17, 18, and 19 together.

## 28. Specification Changelog

| Date | Summary |
| --- | --- |
| 2026-07-13 | Created initial repository-backed product specification from verified code and existing brief. |

## Reusable Codex Implementation Prompt

Use [docs/PRODUCT_SPEC.md](/Users/dusadv/Documents/meal-planner/docs/PRODUCT_SPEC.md) as the primary product source of truth, and [instructions.md](/Users/dusadv/Documents/meal-planner/instructions.md) as the supporting household brief when needed.

Before making changes:

1. Inspect the current code and relevant data files instead of assuming the spec is fully implemented.
2. Verify the active behavior in [app.py](/Users/dusadv/Documents/meal-planner/app.py), [meal_data.yaml](/Users/dusadv/Documents/meal-planner/meal_data.yaml), and any relevant data/storage files.
3. Implement only the requested task.
4. Preserve unrelated behavior and do not silently remove legacy compatibility unless the task asks for it.
5. Enforce strict data isolation:
   - keep all persistent data scoped to the active user store under `data/<user_id>/profiles_data.json`
   - keep profile data isolated within the active profile
   - keep member-specific data isolated within the owning profile
   - do not reintroduce root-level legacy files as primary write targets
6. Add or tighten validation for inputs, ownership, references, quantities, prices, and dates when touching related code.
7. Prefer the simplest working solution, keep changes small, and use existing project patterns unless the task requires refactoring.
8. Add lightweight tests for non-trivial logic.
9. At minimum, keep `app.py` passing `py_compile`.
10. If product behavior changes, update [docs/PRODUCT_SPEC.md](/Users/dusadv/Documents/meal-planner/docs/PRODUCT_SPEC.md) in the same task:
    - update statuses
    - update affected sections
    - add a changelog row
    - note any new open decisions

When reporting back:

- summarize what changed
- list validation/tests run
- mention any remaining gaps or open decisions

## Compact Codex Implementation Prompt

Read [docs/PRODUCT_SPEC.md](/Users/dusadv/Documents/meal-planner/docs/PRODUCT_SPEC.md) first, then inspect current code before changing anything. Implement only the requested task in the existing Streamlit app, preserve unrelated behavior, keep user/profile/member data isolated, add validation and lightweight tests for touched logic, keep `app.py` compilable, and update the spec plus changelog if behavior or storage changes.
