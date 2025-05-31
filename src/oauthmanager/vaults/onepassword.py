# src/oauthmanager/vaults/onepassword.py
from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Dict, Tuple

from cryptography.fernet import Fernet

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# custom exceptions                                                           #
# --------------------------------------------------------------------------- #
class OPFieldError(RuntimeError):
    """Raised when a specific field cannot be fetched from 1Password."""


# --------------------------------------------------------------------------- #
# main class                                                                  #
# --------------------------------------------------------------------------- #
class OnePasswordVault:
    """
    Secure 1Password wrapper with encrypted on-disk caching.

    Example
    -------
    vault = OnePasswordVault()
    creds = vault.fetch("mediaAPIs", "Spotify",
                        ("client_id", "client_secret", "redirect_uri"))
    """

    def __init__(self, cache_ttl: int = 86_400):
        self.cache_ttl = cache_ttl
        self.cache_file = (
            Path.home() / ".cache" / "oauthmanager" / "credentials_cache.enc"
        )
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cipher = Fernet(self._ensure_key())

    # ------------------------------------------------------------------ #
    # public API                                                         #
    # ------------------------------------------------------------------ #
    def fetch(
        self,
        vault_name: str,
        item_name: str,
        fields: Tuple[str, ...],
    ) -> Dict[str, str]:
        """
        Return `{field: value}` for the requested vault / item.

        Raises
        ------
        OPFieldError
            If one or more fields cannot be retrieved.
        """
        cache = self._read_cache()
        cell = (
            cache.get(vault_name, {})
            .get(item_name, {})
        )
        if cell and not self._cache_expired(cell["_fetched_at"]):
            return {f: cell[f] for f in fields if f in cell}

        values: Dict[str, str] = {}
        missing: list[str] = []

        for f in fields:
            try:
                values[f] = self._op_read(vault_name, item_name, f)
            except OPFieldError as e:
                log.debug("Field fetch failed: %s", e)
                missing.append(f)

        if missing:
            raise OPFieldError(
                f"Missing fields {missing} in 1Password item "
                f"'{item_name}' (vault '{vault_name}')."
            )

        cache.setdefault(vault_name, {})[item_name] = {
            **values,
            "_fetched_at": time.time(),
        }
        self._write_cache(cache)
        return values

    # ------------------------------------------------------------------ #
    # internal – cache helpers                                           #
    # ------------------------------------------------------------------ #
    def _cache_expired(self, fetched_at: float) -> bool:
        return (time.time() - fetched_at) > self.cache_ttl

    def _read_cache(self) -> Dict:
        if not self.cache_file.exists():
            return {}
        try:
            raw = self.cache_file.read_bytes()
            decrypted = self.cipher.decrypt(raw).decode()
            return json.loads(decrypted)
        except Exception as e:  # corrupt / wrong key / …
            log.warning("Could not read credentials cache: %s", e)
            return {}

    def _write_cache(self, obj: Dict) -> None:
        encrypted = self.cipher.encrypt(json.dumps(obj).encode())
        self.cache_file.write_bytes(encrypted)

    # ------------------------------------------------------------------ #
    # internal – 1Password CLI                                           #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _op_read(vault: str, item: str, field: str) -> str:
        op_path = f"op://{vault}/{item}/{field}"
        try:
            result = subprocess.run(
                ["op", "read", "--cache", op_path],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as err:
            # Normalise the CLI's stderr into a concise message
            stderr = (err.stderr or "").strip()
            raise OPFieldError(
                f"op read failed for {op_path!s}: {stderr or err}"
            ) from None

    # ------------------------------------------------------------------ #
    # internal – encryption key                                          #
    # ------------------------------------------------------------------ #
    def _ensure_key(self) -> bytes:
        if platform.system() == "Windows":
            key_file = Path(os.getenv("APPDATA", "")) / "oauthmanager" / "encryption_key"
        else:
            key_file = Path.home() / ".oauthmanager_key"
        key_file.parent.mkdir(parents=True, exist_ok=True)

        if key_file.exists():
            return key_file.read_bytes()

        key = Fernet.generate_key()
        key_file.write_bytes(key)
        return key


# --------------------------------------------------------------------------- #
# quick diagnostic run                                                        #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    vault = OnePasswordVault()

    try:
        spotify_creds = vault.fetch(
            "mediaAPIs",
            "Spotify",
            ("client_id", "client_secret", "uri"),
        )
    except OPFieldError as e:
        print(f" {e}")
    else:
        print("Retrieved Spotify credentials:")
        for k, v in spotify_creds.items():
            print(f"  {k}: {v[:6]}…")
