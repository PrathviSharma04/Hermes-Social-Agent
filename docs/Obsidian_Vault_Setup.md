# Obsidian Vault Setup

The Hermes Social Agent uses a local Obsidian vault (Phase 9) as a command center and dashboard. It provides a human-readable interface to the agent's strategy, experiments, and performance over time.

## 1. Prerequisites
- Download and install [Obsidian](https://obsidian.md/).

## 2. Configuration
In your Hermes Social Agent `.env` file, set the path to where you want the vault to live on your local machine:

```env
OBSIDIAN_VAULT_PATH=/path/to/your/documents/HermesVault
```
*(On Windows, use forward slashes or double backslashes, e.g. `C:/Users/You/Documents/HermesVault`)*

## 3. Initialize the Vault
Run the following CLI command to create the necessary folder structure:

```bash
python -m hermes_social vault init
```

This will create folders like `00-Dashboard`, `02-Strategy-Rules`, `03-Experiments`, etc.

## 4. Open in Obsidian
1. Open the Obsidian app.
2. Select **Open folder as vault**.
3. Select the folder you specified in `OBSIDIAN_VAULT_PATH`.

## 5. Sync Data
To populate the vault with the latest strategy rules, active experiments, and monthly performance from the agent's SQLite database, run:

```bash
python -m hermes_social vault sync
```

This pulls data from SQLite and generates cleanly formatted Markdown pages.

## Note on Secrets
> [!WARNING]
> The vault is automatically generated. **Do not** write API keys, passwords, or other secrets into the vault files, as they may be overwritten or synced insecurely depending on your Obsidian setup.
