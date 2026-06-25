---
name: odoo-migrate-module
description: Migrates a custom Odoo module to a new major version. Use when the user wants to migrate, upgrade, or prepare a custom Odoo module for a new major Odoo version (e.g. 17→18, 18→19). Triggers on requests like "migrate module X to Odoo 19", "update my module for v19", "create migration scripts for X", "upgrade module X compatibility", or any version upgrade request for a custom Odoo module.
---

# Odoo Module Migration with OpenUpgrade

This skill guides you through migrating a custom Odoo module to the next major
version. It covers: manifest bump, OpenUpgrade impact analysis on dependencies,
writing migration scripts (pre/post), fixing Python and XML code, and producing
a final change summary.

## Required information

Before starting, identify:
- **Module path** — absolute path to the module directory
- **Source version** — read from `__manifest__.py` (e.g. `18.0`)
- **Target version** — from the user's request (e.g. `19`)

If any of these is missing, ask the user before proceeding.

## Fetching OpenUpgrade data from GitHub

All OpenUpgrade reference data is fetched directly from GitHub — no local
checkout is required. Use the raw content URL pattern:

```
https://raw.githubusercontent.com/OCA/OpenUpgrade/<target_version>.0/<path>
```

Key files to fetch:
- `apriori.py`:
  `openupgrade_scripts/apriori.py`
- `upgrade_analysis.txt` for a dependency named `<dep>`:
  `openupgrade_scripts/scripts/<dep>/` — first list this directory to find the
  version folder (e.g. `19.0.1.3/`), then fetch
  `openupgrade_scripts/scripts/<dep>/<version>/upgrade_analysis.txt`

To list directory contents on GitHub (for version discovery), use the GitHub
API:
```
https://api.github.com/repos/OCA/OpenUpgrade/contents/openupgrade_scripts/scripts/<dep>?ref=<target_version>.0
```
This returns JSON; pick the entry whose `name` starts with `<target_version>.0`
and use its `name` as the version directory.

If a dependency has no entry in `openupgrade_scripts/scripts/`, it means
OpenUpgrade has no migration script for it — treat it as "nothing to do".

---

## Step 1 — Read the manifest

Read `__manifest__.py` and extract:
- Current `version` string (format: `<odoo_major>.<odoo_minor>.<module_version>`)
- `depends` list

The module version suffix (e.g. `1.0.0`) stays unchanged during the Odoo major
version bump. Only the Odoo major prefix changes.

**Action:** Update `version` in `__manifest__.py`:
- Old: `"18.0.1.2.3"` → New: `"19.0.1.2.3"` (keep everything after first two
  components)

---

## Step 2 — Scan OpenUpgrade's `apriori.py` and update `depends`

Fetch from GitHub:
```
https://raw.githubusercontent.com/OCA/OpenUpgrade/<target_version>.0/openupgrade_scripts/apriori.py
```

For each module in `depends`, check `renamed_modules` and `merged_modules` and **immediately update `__manifest__.py`**:

**Renamed module** — replace the old name with the new one in `depends`:
```
"pos_viva_wallet" → "pos_viva_com"
```

**Merged module** — replace with the merge target, or remove if already present:
```
"pos_epson_printer" → "point_of_sale"  (remove if "point_of_sale" is already listed)
```

Also scan `renamed_models` and `merged_models` for any model names your module inherits or uses — note these for Step 3. See [apriori.md](references/apriori.md) for a deeper explanation of how `apriori.py` relates to custom module migrations.

---

## Step 3 — Analyze upgrade_analysis.txt for each dependency

For each module in `depends`, fetch its analysis from GitHub:

1. List the version directories available for the dependency:
   ```
   GET https://api.github.com/repos/OCA/OpenUpgrade/contents/openupgrade_scripts/scripts/<dep>?ref=<target_version>.0
   ```
   Pick the directory whose `name` starts with `<target_version>.0`. If the
   directory doesn't exist, that dependency has no migration script — skip it.

2. Fetch the analysis file:
   ```
   https://raw.githubusercontent.com/OCA/OpenUpgrade/<target_version>.0/openupgrade_scripts/scripts/<dep>/<version_dir>/upgrade_analysis.txt
   ```

In `upgrade_analysis.txt`, look for entries involving:
- `# NOTHING TO DO` — no changes needed for that module
- `module / model / field (type) : NEW` — field added upstream; no action unless your module stores related/computed fields that depend on it
- `module / model / field (type) : DEL` — field removed; requires `delete_columns` in pre-migration
- `obsolete model X (renamed to Y)` — model renamed; if your module uses X, requires model rename in pre-migration and code updates in Steps 7-9
- `new model X` — new model added upstream; no action needed unless your module references it
- Merged models appear as `obsolete model X` with no rename target — if your module uses X, update inheritance/references to the merge target

### Practical approach to finding affected models:

**For each renamed or merged model found in `upgrade_analysis.txt`:**

1. Check if your module uses that model by searching your module's code:
   ```bash
   rg "old_model_name" <module_path>/models/ <module_path>/wizard/ --type py
   rg "old_model_name" <module_path>/views/ <module_path>/data/ --type xml
   ```

2. Search for inheritance patterns:
   ```bash
   # Find model inheritance
   rg "_inherit\s*=.*['\"]old_model_name['\"]" <module_path>/

   # Find model references in code (fields.Many2one, domain filters, etc.)
   rg "old_model_name" <module_path>/models/

   # Find XML view references
   rg 'model="old_model_name"' <module_path>/views/
   ```

3. **Only if matches are found:** Proceed to Steps 7-9 to update the affected code.

**Focus only on what directly affects this module:**
- Inherited models
- Fields referenced in views/Python
- Related/stored computed fields that depend on upstream fields
- Domain filters or record model references in wizard/controller code

Ignore upstream changes that don't affect your code.

---

## Step 4 — Create the migration script directory

If it doesn't exist, create:

```
<module_path>/migrations/<target_version>.1.0.0/
    __init__.py          (empty)
    pre-migration.py
    post-migration.py
    end-migration.py     (optional — final cleanup after all modules have migrated)
```

Use the convention `<target_version>.1.0.0` for the first migration of this
module version (e.g. `19.0.1.0.0`). If a `migrations/` directory already
exists with a matching version, edit the existing files instead.

> Note: Odoo looks for these under `migrations/` inside the module directory.
> The file names must be exactly `pre-migration.py`, `post-migration.py`, and
> `end-migration.py` (not `pre-migrate.py`).

---

## Step 5 — Write `pre-migration.py`

`pre-migration.py` runs **before** Odoo applies any ORM changes for this
module's upgrade. Use it for:

- **Column/table renames** — when a field or model was renamed in this module
- **XML ID renames** — when `ir.model.data` entries changed key names
- **Column deletions** — when a field was removed from the module
- **Custom data fixes** — any raw SQL needed before the ORM takes over

Template:

```python
# Copyright <year> <Author>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from openupgradelib import openupgrade


_renamed_fields = [
    # (model_name, table_name, old_column, new_column)
    # ("parking.reservation", "parking_reservation", "old_field", "new_field"),
]

_renamed_xmlids = [
    # ("old_module.xml_id", "new_module.xml_id"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
    openupgrade.rename_xmlids(env.cr, _renamed_xmlids)
```

If there is nothing to do in pre-migration, write the file with a `pass` in the
`migrate` function and a comment explaining why.

**Key openupgradelib functions:**
- `openupgrade.rename_columns(cr, spec)` — `spec` is a dict:
  `{"table_name": [("old_col", "new_col")]}`
- `openupgrade.rename_fields(env, spec)` — `spec` is a list of 4-tuples:
  `(model, table, old_field, new_field)`
- `openupgrade.rename_models(cr, spec)` — `spec` is a list of
  `(old_model, new_model)` tuples
- `openupgrade.rename_xmlids(cr, spec)` — `spec` is a list of
  `(old_xmlid, new_xmlid)` tuples
- `openupgrade.delete_columns(cr, spec)` — `spec` is a dict:
  `{"table_name": ["col1", "col2"]}`
- `openupgrade.logged_query(cr, sql)` — executes raw SQL and logs it
- `openupgrade.update_module_names(cr, items, merge_modules=False)` — **rarely used in custom module migrations**. This function updates module names in the `ir_module_module` table. Use it only if your custom module itself was renamed or merged in the target version (in which case add entries to `apriori.py`'s `renamed_modules` or `merged_modules` instead). Custom modules typically don't manipulate their own dependencies at the database level.

---

## Step 6 — Write `post-migration.py`

`post-migration.py` runs **after** Odoo has applied ORM changes. Use it for:

- **Recomputing stored computed fields** that depend on data changed during upgrade
- **Data migrations** that require the new schema to be in place
- **Filling in new required fields** from existing data

Template:

```python
# Copyright <year> <Author>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Recompute stored fields that may be stale after the upgrade
    env["my.model"].search([])._compute_my_stored_field()
```

**Which fields to recompute:** Look for fields in the module's model files that are stored in the database and may be stale after upstream changes.

**There are two distinct cases — do not confuse them:**

1. **`compute="_compute_foo"` + `store=True`** — there is a Python method `_compute_foo()` on the model. Call it directly:
   ```python
   env["my.model"].search([])._compute_foo()
   ```

2. **`related="some.field"` + `store=True`** — Odoo stores the value but there is **no** compute method to call. Invalidate the field so Odoo recomputes it on next access:
   ```python
   env["my.model"].search([]).invalidate_recordset(["foo"])
   ```
   For `precompute=True` related fields this is usually sufficient — Odoo recomputes them during the upgrade process after invalidation.

**Practical rule:** Before writing any `._compute_foo()` call, verify the method actually exists in the model's Python source. If the field uses `related=` instead of `compute=`, there is no such method and calling it will raise `AttributeError`.

---

## Step 7 — Fix Python code for deprecated APIs

Scan the module's Python files for patterns that changed between versions. The
most common Odoo version-to-version Python API changes are:

- **Field renames on core models** — e.g. `groups_id` → `group_ids` on
  `ir.ui.menu`, `ir.ui.view`, `res.users`; `users` → `user_ids` on
  `res.groups`. Check the target version's release notes or OpenUpgrade's
  `upgrade_analysis.txt` for the `base` module to find the full list.
- **Removed/changed ORM methods** — check the target version's release notes
  or OpenUpgrade's `upgrade_analysis.txt` for the `base` module
- **Changed field types or signatures** — e.g. Selection field value changes,
  new required parameters
- **Deprecated `@api.multi` / `@api.one`** — already removed in v14+, but
  worth checking for old code
- **`_name` vs `_inherit`** — no change, but verify inherited model names
  haven't changed (Step 2)

### Practical approach:

For each dependency analyzed in Step 3, look at its `upgrade_analysis.txt` and:

1. **Identify renamed fields and models** that your module uses:
   ```bash
   # Search for renamed field references
   rg "old_field_name" <module_path>/models/ --type py
   rg 'name="old_field_name"' <module_path>/ --type xml

   # Search for renamed model references
   rg "old_model_name" <module_path>/models/ --type py
   ```

2. **Search for core model field usage** in your code:
   ```bash
   # For example, if release notes mention groups_id → group_ids rename
   rg "\.groups_id" <module_path>/ --type py
   rg 'field="groups_id"' <module_path>/ --type xml
   ```

3. **Check for deprecated method calls** by searching your code for patterns mentioned in the target version's changelog.

**Make the changes directly** in the source files.

---

## Step 8 — Fix XML views and data files

Scan all XML files in `views/`, `wizard/`, `data/`, `security/` for:

- **References to renamed fields** — field names used in `<field name="...">`,
  `<filter string="..." name="...">`, domain expressions, `attrs`, `column_invisible`
- **References to renamed models** — `model="..."` attributes in `<record>`,
  `<act_window>`, etc.
- **`groups` attribute** — `groups_id` → `group_ids` in view XML; but note
  that in XML `groups` attribute refers to `res.groups` XML IDs, not field
  names — this is different from the Python field rename
- **Deprecated view attributes** — check target version release notes;
  e.g. `attrs` was replaced by `invisible`/`readonly`/`required` in v17+

### Practical search patterns:

```bash
# Find renamed field references in XML
rg 'name="old_field_name"' <module_path>/views/ --type xml
rg 'field="old_field_name"' <module_path>/ --type xml

# Find renamed model references in XML
rg 'model="old_model_name"' <module_path>/ --type xml

# Find domain expressions referencing renamed fields
rg '\[.*(old_field_name)' <module_path>/views/ --type xml

# Find core model field references that may have been renamed
rg 'domain=.*groups_id' <module_path>/ --type xml
```

**Make the changes directly** in the XML files.

---

## Step 9 — Fix security files

Check `security/ir.model.access.csv`:
- Model names in the `model_id/id` column — update if any model was renamed
  (e.g. `model_my_old_name` → `model_my_new_name`)

Check `security/ir_rule.xml`:
- Domain filters referencing field names — update if fields were renamed
- Model references — update if models were renamed

---

## Step 10 — Produce a migration summary

After all changes, output a clear summary:

```
## Migration Summary: <module_name> <source_version> → <target_version>

### Manifest
- Version bumped: 18.0.x.y.z → 19.0.x.y.z
- Dependencies updated: [list any changes]

### Migration scripts
- migrations/19.0.x.y.z/pre-migration.py: [what it does, or "nothing to do"]
- migrations/19.0.x.y.z/post-migration.py: [what it does]

### Python code changes
- [file:line] — description of change

### XML changes
- [file] — description of change

### Security changes
- [file] — description of change

### Manual review required
- [anything the developer must verify manually, e.g. business logic changes,
  new required fields with no obvious default, PG constraint compatibility]
```

---

## Tips and gotchas

- **`pre-migrate.py` vs `pre-migration.py`**: Odoo looks for `pre-migration.py`
  (with full word). Files named `pre-migrate.py` are NOT automatically picked
  up by Odoo's upgrade machinery — they must be renamed.
- **GIST constraints and PostgreSQL**: If the module uses `_sql_constraints`
  with `EXCLUDE USING GIST`, verify the constraint syntax is compatible with
  the target Odoo version's PostgreSQL requirement. The constraint itself lives
  in Python and doesn't need a migration script unless the column types changed.
- **openupgradelib version**: The library must be installed in the target Odoo
  environment. It is a required dependency of `openupgrade_framework`.
- **`@openupgrade.migrate()` decorator**: Required on the `migrate(env, version)`
  function — it handles version checking and logging automatically. Don't omit it.
- **Stored `related=` fields**: In Odoo, `related=..., store=True` fields are
  stored in the DB. If the source field was renamed upstream, these need a
  column rename in pre-migration AND recomputation in post-migration.
- **TransientModel fields**: Wizard (`TransientModel`) tables are dropped and
  recreated on each Odoo restart. Skip them in migration scripts — they need no
  column renames.

---

## Additional resources

**Understanding `apriori.py`**: See [apriori.md](references/apriori.md) for a detailed explanation of how `apriori.py` dictionaries work and how they relate to custom module migrations.
