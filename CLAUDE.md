# Development Guide

## Plugin Modification Checklist

When any modification is made to a plugin (skills, commands, scripts, or configuration), you MUST update ALL of the following files:

1. **`CHANGELOG.db`** (SQLite database at repository root)
   - Table: `entries` (id, timestamp, version, release_title, category, component, description)
   - `timestamp`: current time in `YYYY-MM-DDTHH:MM` format (e.g. `2026-02-25T13:30`)
   - `version`: semver without `v` prefix (e.g. `2.2.0`, not `v2.2.0`)
   - `category`: `Added`, `Changed`, `Removed`, `Fixed`
   - Insert via: `INSERT INTO entries (timestamp, version, release_title, category, component, description) VALUES (...)`

2. **`plugin.json`** (`.claude/.claude-plugin/plugin.json`)
   - Bump `version` if the change is user-facing
   - Update `description`, `skills`, or `commands` arrays if added or removed

3. **`marketplace.json`** (`.claude-plugin/marketplace.json` at repository root)
   - Sync plugin `version` with plugin.json
   - Update `description`, `skills`, or `commands` arrays to match
   - Bump top-level `metadata.version` to reflect the overall marketplace update

4. **`README.md`** (repository root)
   - Sync plugin `version` in the summary section
   - Update component tables (Type, Description) if skills, commands, or agents were added, removed, or renamed
   - Update the Structure tree if directory layout changed
