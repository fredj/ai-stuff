---
name: odoo-run-dev
description: Guide for running Odoo in Docker for development. Use when working in an Odoo project, starting Odoo services, running docker compose commands, or debugging Odoo with pdb.
---

# Running the Docker Composition

## Prerequisites

Before running the composition, ensure submodules are updated:

```bash
invoke submodule.update
```

## Build the Docker Image

Build is required when starting on the project, when the base image is updated, or when the Dockerfile changes:

```bash
docker compose build --pull
```

## Starting Services

Run in background:

```bash
docker compose up -d
```

## Common Commands

```bash
# View logs
docker compose logs odoo
docker compose logs db

# Check running services
docker compose ps

# Find Odoo port
docker compose port odoo 8069

# Stop services
docker compose stop
```

## Running Odoo for Development

### Important: Check for Running Containers

Before starting Odoo, always check if containers are already running from a previous session:

```bash
# Check if odoo container is running
docker ps --filter name=odoo

# Stop if running
docker stop odoo

# Or check all compose services
docker compose ps
```

**Note:** When starting Odoo in detached mode, containers will continue running even after closing the chat session. Always stop containers when done.

### Detached Mode (Recommended for AI agents)

Use detached mode (`-d`) to run Odoo in the background, allowing continued interaction:

```bash
# Start Odoo in detached mode
docker compose run --rm -d --name=odoo -e DB_NAME=prod -p 8890:8069 odoo odoo --workers=0 --max-cron-threads=0

# Run without migration (detached)
docker compose run --rm -d --name=odoo -e DB_NAME=prod -p 8890:8069 -e MIGRATE=False odoo odoo --workers=0 --max-cron-threads=0

# View logs
docker logs -f odoo

# Attach for pdb debugging (run in your terminal, not via AI agent)
docker attach odoo

# Stop the container when done
docker stop odoo
```

### Interactive Mode (for pdb debugging)

Use interactive mode when you need direct access to pdb breakpoints:

```bash
# Start Odoo interactively with workers=0 (required for pdb)
docker compose run --rm --name=odoo -e DB_NAME=prod -p 8890:8069 odoo odoo --workers=0 --max-cron-threads=0

# Run without migration
docker compose run --rm --name=odoo -e DB_NAME=prod -p 8890:8069 -e MIGRATE=False odoo odoo --workers=0 --max-cron-threads=0
```

**Note:** Interactive mode blocks the terminal. Use detached mode when working with AI agents.

## Developer Mode (--dev)

The `--dev` parameter enables developer features. Options can be combined with commas. The preferred option for development is `xml`:

```bash
# Auto-reload XML views (preferred for development)
docker compose run --rm -d --name=odoo -e DB_NAME=prod -p 8890:8069 odoo odoo --workers=0 --max-cron-threads=0 --dev=xml

# Enable all dev features (detached)
docker compose run --rm -d --name=odoo -e DB_NAME=prod -p 8890:8069 odoo odoo --workers=0 --max-cron-threads=0 --dev=all

# Auto-reload on Python file changes (detached)
docker compose run --rm -d --name=odoo -e DB_NAME=prod -p 8890:8069 odoo odoo --workers=0 --max-cron-threads=0 --dev=reload

# Combine multiple options (detached)
docker compose run --rm -d --name=odoo -e DB_NAME=prod -p 8890:8069 odoo odoo --workers=0 --max-cron-threads=0 --dev=reload,qweb,xml
```

Available options:

- `all` - Enable all dev features
- `reload` - Auto-reload Python code on changes
- `qweb` - Auto-reload QWeb templates
- `xml` - Auto-reload XML views
- `werkzeug` - Enable Werkzeug debugger for exceptions
- `pudb|wdb|ipdb|pdb` - Use specific debugger

## Debug Mode (URL Parameter)

Enable debug mode in the browser by adding `?debug=` to the URL. This shows additional fields, menus, and developer tools.

### URL Options

| Parameter | Description |
|-----------|-------------|
| `?debug=1` | Enable debug mode (shows additional info/fields, developer tools) |
| `?debug=assets` | Non-minified JS/CSS bundles with source-maps (for JS debugging) |
| `?debug=tests` | Injects test bundle for running test tours |
| `?debug=assets,tests` | Combine both modes |

### Examples

```
http://localhost:8890/web?debug=1
http://localhost:8890/web?debug=assets
http://localhost:8890/web?debug=assets,tests
```

### In XML Views

To show elements only in debug mode, use the group `base.group_no_one`:

```xml
<field name="fname" groups="base.group_no_one"/>
```

### In JavaScript

The debug mode value can be read from the environment:

```javascript
env.debug  // empty string if not active, otherwise contains mode string
```