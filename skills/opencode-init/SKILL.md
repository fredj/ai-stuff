---
name: opencode-init
description: Initialize or update an opencode.json config file for a project by converting .mcp.json into OpenCode format. Use when setting up OpenCode for a project that already has a .mcp.json, or when asked to create/update opencode.json.
---

# opencode-init Skill

Generate or update `opencode.json` for the current project by converting `.mcp.json` to OpenCode's configuration format.

## Steps

1. **Read `.mcp.json`** from the project root.
2. **Convert** each entry under `mcpServers` using the mapping below.
3. **Write `opencode.json`** — if the file already exists, read it first and update only the `mcp` key, preserving all other settings.

## Format Mapping

| `.mcp.json` field | `opencode.json` field |
|---|---|
| `mcpServers.<name>` | `mcp.<name>` |
| `type: "stdio"` + `command` + `args` | `type: "local"`, `command: [command, ...args]` |
| `env` | `environment` |
| `type: "http"` / `"sse"` + `url` | `type: "remote"`, `url` |
| `headers` | `headers` |

Always include `"$schema": "https://opencode.ai/config.json"` at the top level.

## Example

Input `.mcp.json`:
```json
{
  "mcpServers": {
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp"
    },
    "local-postgresql": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "postgres-mcp-server", "--connection-string", "postgresql://user:pass@localhost:5432/mydb"]
    }
  }
}
```

Output `opencode.json`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "sentry": {
      "type": "remote",
      "url": "https://mcp.sentry.dev/mcp"
    },
    "local-postgresql": {
      "type": "local",
      "command": ["npx", "-y", "postgres-mcp-server", "--connection-string", "postgresql://user:pass@localhost:5432/mydb"]
    }
  }
}
```

## Future Extensions (not yet implemented)

These sections can be added in future iterations of this skill:

- **Permissions**: Map `allowedTools`/`deniedTools` from `.claude/settings.json` or `~/.claude/settings.json` to OpenCode's `agent.permissions` format.
- **Model**: Map the user's preferred Claude model to OpenCode's `model` field.
