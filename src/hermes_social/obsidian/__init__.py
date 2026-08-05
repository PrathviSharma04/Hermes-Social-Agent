"""Obsidian Vault Integration Engine (Phase 9)."""

from hermes_social.obsidian.models import VaultSyncResult, DecisionEntry
from hermes_social.obsidian.vault_init import initialize_vault
from hermes_social.obsidian.sync import sync_vault

__all__ = ["VaultSyncResult", "DecisionEntry", "initialize_vault", "sync_vault"]
