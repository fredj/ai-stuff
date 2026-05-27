# Understanding `apriori.py` and custom module migration

## What is `apriori.py`?

`apriori.py` is a configuration file in OpenUpgrade that maps **known database schema changes** across Odoo versions. It contains:

1. **`renamed_modules`** — old module name → new module name
   - Affects: Your `depends` list in the manifest
   - Used in: Step 2 (manifest dependency updates)

2. **`merged_modules`** — old module name → target module name
   - Affects: Your `depends` list in the manifest
   - Used in: Step 2 (manifest dependency updates)

3. **`renamed_models`** — old model name → new model name
   - Affects: Your code only if your module inherits or uses these models
   - Used in: Step 3 (analyzing `upgrade_analysis.txt`) and Steps 7-9 (code updates)
   - **Only used by the external `upgrade_analysis` tool** to generate `upgrade_analysis.txt`; not executed by core migrations at runtime

4. **`merged_models`** — old model name → target model name
   - Affects: Your code only if your module inherits or uses these models
   - Used in: Step 3 (analyzing `upgrade_analysis.txt`) and Steps 7-9 (code updates)
   - **Only used by the external `upgrade_analysis` tool** to generate `upgrade_analysis.txt`; not executed by core migrations at runtime

## Key distinction: Core migrations vs. custom module migrations

- **OpenUpgrade's core migrations** (e.g., `/openupgrade_scripts/scripts/base/19.0.1.3/pre-migration.py`)
  - Read `renamed_modules`/`merged_modules` from `apriori.py` and call `openupgrade.update_module_names()`
  - Directly manipulate `ir_module_module` and `ir.model` records in the database
  - Handle **system-wide** module restructuring
  - `renamed_models`/`merged_models` are NOT used at runtime — only by the `upgrade_analysis` script that generates `upgrade_analysis.txt`

- **Your custom module's migration**
  - Does NOT directly import `apriori.py`
  - Does NOT call `openupgrade.update_module_names()` (unless your module itself was renamed/merged)
  - Instead, **reacts to** the changes documented in `apriori.py`:
    - Step 2: Update `depends` if dependencies were renamed/merged
    - Steps 7-9: Update code if models your module uses were renamed/merged

## Workflow: How `apriori.py` changes flow to your module

```
1. OpenUpgrade core migration runs update_module_names() using renamed_modules/merged_modules
   ↓
2. Database is now updated (module table, model inheritance paths, etc.)
   ↓
3. Your module's migration scripts run:
   - Step 2: Check if YOUR dependencies are in renamed_modules/merged_modules
   - Step 3: Check if MODELS YOUR MODULE USES are in renamed_models/merged_models
   - Steps 7-9: Update YOUR code to reference the new names
```

**Key insight:** You don't manipulate `apriori.py` entries; you **read them** to understand what changed upstream, then update your code accordingly.
