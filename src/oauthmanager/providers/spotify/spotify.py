# src/oauthmanager/providers/spotify/spotify.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, List

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

from oauthmanager.providers.base import Provider
from oauthmanager.vaults.onepassword import OPFieldError

class SpotifyProvider(Provider):
    """
    Two auth modes (pick one in creds_config.json):
    • "oauth2_client"   – user-level access via Authorization-Code flow
    • "client_credentials" – app-only access (no user playlists)
    """

    required_fields: tuple[str, ...] = (
        "client_id",
        # client_secret is optional if you choose PKCE
    )

    def build_client(
        self,
        scopes: List[str] | None = None,
        username: str | None = None,
        open_browser: bool = True,
        **__,
    ) -> Any:
        auth_cfg = self.cfg["auth"]
        mode     = auth_cfg["method"]               # oauth2_client | client_credentials
        token_cache = Path(
            os.path.expanduser(
                auth_cfg.get("token_cache", "~/.cache/oauthmanager/spotify_token.json")
            )
        )
        token_cache.parent.mkdir(parents=True, exist_ok=True)

        vault = self.cfg["vault"]
        item  = self.cfg["item"]

        # ------------------------------------------------------------------ #
        # 1. Resolve secrets from 1Password                                  #
        # ------------------------------------------------------------------ #
        secrets = {}
        if mode == "oauth2_client":
            fields = ("client_id", "client_secret", "redirect_uri")
        else:  # client_credentials
            fields = ("client_id", "client_secret")
        try:
            secrets = self.secrets or self._VAULT.fetch(vault, item, fields)
        except OPFieldError:
            raise RuntimeError(
                f"Missing Spotify creds in 1Password item '{item}' (vault '{vault}')"
            )

        # ------------------------------------------------------------------ #
        # 2. Pick the Spotify auth manager                                   #
        # ------------------------------------------------------------------ #
        scopes = scopes or auth_cfg.get(
            "scopes",
            ["playlist-read-private", "playlist-modify-private"],
        )

        if mode == "oauth2_client":
            # Supports PKCE if 'client_secret' is None.
            auth_manager = SpotifyOAuth(
                client_id     = secrets["client_id"],
                client_secret = secrets.get("client_secret"),
                redirect_uri  = secrets.get("redirect_uri", "http://127.0.0.1:8080/"),
                cache_path    = str(token_cache),
                scope         = " ".join(scopes),
                open_browser  = open_browser,
            )
        elif mode == "client_credentials":
            auth_manager = SpotifyClientCredentials(
                client_id     = secrets["client_id"],
                client_secret = secrets["client_secret"],
                requests_timeout = 30,
            )
        else:
            raise ValueError(f"Unsupported auth method '{mode}'")

        return spotipy.Spotify(auth_manager=auth_manager)
