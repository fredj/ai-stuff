---
name: odoo-database
description: Guide for copying Odoo databases from remote environments to local development. Use when working in an Odoo project, downloading dumps from integration, or restoring databases locally.
---

# Odoo Database Operations

## Important: Local Environment Only

**DO NOT** make any changes to remote environments (production, integration, labs, etc.).
All operations should be performed on the local development environment only.

## Copying Database from Remote Environment to Local

### Using celebrimbor_cli

**Prerequisites:**

- **Port 8080 must be free.** `celebrimbor_cli` uses port 8080 for the Azure AD OAuth redirect URI. If anything is already listening on port 8080, the command fails immediately with `[Errno 98] Address already in use`. Check with `ss -tlnp | grep 8080` and stop the conflicting service before running.

- **VPN must be connected.** Without VPN, the request will be rejected with `Forbidden: check if you are connected to the VPN.`

- `celebrimbor_cli` must be installed:

  ```bash
  pip install --user git+ssh://git@github.com/camptocamp/celebrimbor-cli#egg=celebrimbor_cli
  ```

### Step-by-step Approach

Get the platform (`-p`) and client (`-c`) values from `.cookiecutter.context.yml`:

- `-p` (platform): use the `country` value
- `-c` (client): use the `customer_name` value
- `-e` (environment): `int` (default), `prod`, `labs`, etc.

1. **Download a dump (default: integration):**

   ```bash
   celebrimbor_cli -p <country> download -c <customer_name> -e int
   ```

   Or from another environment:

   ```bash
   celebrimbor_cli -p <country> download -c <customer_name> -e prod
   ```

   Or download a specific dump by name:

   ```bash
   celebrimbor_cli -p <country> download -c <customer_name> -e int --name <dump_name>
   ```

2. **Restore the dump locally:**

   ```bash
   docker-compose run --rm odoo dropdb prod
   docker-compose run --rm odoo createdb prod
   docker-compose run --rm -T odoo pg_restore --verbose --no-owner --no-acl -d prod < dump_file.pg
   ```

   **Note:** The `-T` flag disables pseudo-TTY allocation, which is required when piping data via stdin.

   **Important:** Database restores can take a **very long time** (30+ minutes for large databases). This is normal behavior. Do not interrupt the process. For AI agents, it's recommended to inform the user that the restore is running and they should wait for completion, or run the restore manually in a separate terminal.

## DB_NAME Environment Variable

The `DB_NAME` environment variable specifies which PostgreSQL database Odoo should connect to.

### Default Value

The default database name is configured in `docker-compose.yml`:

```yaml
environment:
  DB_NAME: odoodb
```

### Usage

Override `DB_NAME` with `-e DB_NAME=<name>` when running containers:

```bash
# Use default database (odoodb)
docker compose run --rm odoo

# Use production dump
docker compose run --rm -e DB_NAME=prod odoo
```

### Common Database Names

| Database | Purpose |
|----------|---------|
| `odoodb` | Default development database |
| `prod` | Restored production dumps |
| `testdb` | Running tests |
| `odoo_demo` | Demo database with sample data |

### Key Points

- The Docker image only operates on **one database at a time**
- You can have multiple databases in the postgres container
- To switch databases, override `DB_NAME` when running the container
- List all databases and their versions with: `invoke database.list-versions`

For more details, check the project's `docs/` directory (e.g., `docker-and-databases.md`, `how-to-use-a-prod-db-in-dev.md`).
