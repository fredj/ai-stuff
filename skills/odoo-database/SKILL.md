---
name: odoo-database
description: Guide for copying Odoo databases from remote environments to local development. Use when working in an Odoo project, downloading dumps from integration, or restoring databases locally.
---

# Odoo Database Operations

**DO NOT** make any changes to remote environments. All operations are local only.

## Prerequisites

- **VPN connected** — requests are rejected without VPN
- **Port 8080 free** — needed for Azure AD OAuth (`ss -tlnp | grep 8080`)
- **`odoo-project-tools` installed:**
  ```bash
  uv tool install git+https://github.com/camptocamp/odoo-project-tools
  ```
- **`celebrimbor_cli` up-to-date and on the right Python** — it enforces a strict version check and refuses to run if outdated. It must also be installed for the Python version active in the project (check `.python-version`). If you see `A new version of celebrimbor_cli is available`, upgrade it:
  ```bash
  # Find latest tag, then install it for the project's active Python
  git ls-remote --tags git@github.com:camptocamp/celebrimbor-cli | tail -5
  PYENV_VERSION=<active-python> pyenv exec pip install "git+ssh://git@github.com/camptocamp/celebrimbor-cli@<latest-tag>"
  ```

## Commands

`otools-cloud` reads platform and customer from `.cookiecutter.context.yml` automatically. The customer name is derived from `project_name` by stripping the last `_`-separated segment (e.g. `bitofit_odoo` → `bitofit`). If the project was renamed, this derived name may not match the registered celebrimbor customer — ask the ops team for the correct name and pass it with `--customer`.

```bash
# List available dumps
otools-cloud dump list --env int

# Download and restore in one step (recommended)
otools-cloud dump download --env int --restore-to-db odoodb
otools-cloud dump download --env prod --restore-to-db odoodb
otools-cloud dump download --env int --name <dump_name> --restore-to-db odoodb
```

Restores can take 30+ minutes for large databases — do not interrupt.

## Switching Databases

Override `DB_NAME` when running containers:

```bash
docker compose run --rm -e DB_NAME=prod odoo
```

List all local databases and their versions:

```bash
invoke database.list-versions
```
