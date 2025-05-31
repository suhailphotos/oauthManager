from abc import ABC, abstractmethod
from typing import Any, Dict


class Provider(ABC):
    """Every concrete provider returns a ready-to-use client object."""

    # which fields (or config keys) we must retrieve from 1Password / config
    required_fields: tuple[str, ...] = ()

    def __init__(self, secrets: Dict[str, str], cfg_block: Dict[str, Any]):
        """
        Parameters
        ----------
        secrets   : dict  – the raw secrets fetched from 1Password
        cfg_block : dict  – that provider’s block from creds_config.json
        """
        self.secrets = secrets
        self.cfg = cfg_block

    # ------------------------------------------------------------------ #
    @abstractmethod
    def build_client(self, **kwargs) -> Any:
        """Return a ready client (googleapiclient, spotipy.Spotify, …)."""
