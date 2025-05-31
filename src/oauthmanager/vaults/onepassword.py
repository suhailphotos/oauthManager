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


class OPFieldError(RuntimeError):
    """Raised when a specific field cannot be fetched from 1Password."""


class OnePasswordVault:
    """
    1Password wrapper with encrypted on-disk caching.

    vault = OnePasswordVault()
    creds = vault.fetch("mediaAPIs", "Spotify",
                        ("client_id", "client_secret", "redirect_uri"),
                        fresh=True)   # ← ignore cache just this once
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
        *,
        fresh: bool = False,
    ) -> Dict[str, str]:
        """
        Return `{field: value}` for the vault / item.

        Parameters
        ----------
        vault_name : str
        item_name  : str
        fields     : tuple[str, ...]
        fresh      : bool   If True (or env OP_FRESH=1) skip cache and re-pull.
        """
        fresh = fresh or os.getenv("OP_FRESH", "0") in {"1", "true", "yes"}

        if not fresh:
            cache = self._read_cache()
            cell = cache.get(vault_name, {}).get(item_name, {})
            if cell and not self._cache_expired(cell["_fetched_at"]):
                return {f: cell[f] for f in fields if f in cell}
        else:
            cache = self._read_cache()  # still load so we can overwrite later

        values, missing = {}, []

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
    # cache invalidation helpers                                         #
    # ------------------------------------------------------------------ #
    def invalidate(self, vault_name: str, item_name: str | None = None) -> None:
        """
        Remove a cached entry.

        • `invalidate("mediaAPIs", "Spotify")` removes just that item.
        • `invalidate("mediaAPIs")` wipes the whole vault's cache.
        """
        cache = self._read_cache()
        if vault_name not in cache:
            return
        if item_name:
            cache[vault_name].pop(item_name, None)
            if not cache[vault_name]:
                cache.pop(vault_name, None)
        else:
            cache.pop(vault_name, None)
        self._write_cache(cache)

    # ------------------------------------------------------------------ #
    # internal – cache helpers                                           #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _cache_expired(fetched_at: float) -> bool:
        return (time.time() - fetched_at) > 86_400  # 24 h

    def _read_cache(self) -> Dict:
        if not self.cache_file.exists():
            return {}
        try:
            raw = self.cache_file.read_bytes()
            return json.loads(self.cipher.decrypt(raw).decode())
        except Exception as e:
            log.warning("Could not read credentials cache: %s", e)
            return {}

    def _write_cache(self, obj: Dict) -> None:
        self.cache_file.write_bytes(self.cipher.encrypt(json.dumps(obj).encode()))

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
            stderr = (err.stderr or "").strip()
            raise OPFieldError(f"op read failed for {op_path}: {stderr or err}") from None

    # ------------------------------------------------------------------ #
    # internal – encryption key                                          #
    # ------------------------------------------------------------------ #
    def _ensure_key(self) -> bytes:
        dest = (
            Path(os.getenv("APPDATA", "")) / "oauthmanager" / "encryption_key"
            if platform.system() == "Windows"
            else Path.home() / ".oauthmanager_key"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            return dest.read_bytes()
        key = Fernet.generate_key()
        dest.write_bytes(key)
        return key


# ---------------------------------------------------------------------- #
# diagnostic run                                                         #
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    v = OnePasswordVault()

    # first run, stateless cache bypass
    creds = v.fetch("mediaAPIs", "Spotify", ("client_id",), fresh=True)
    print("client_id:", creds["client_id"][:6], "…")

    # subsequent run should hit cache unless OP_FRESH=1 or fresh=True
    creds2 = v.fetch("mediaAPIs", "Spotify", ("client_id",))
    print("cached id :", creds2["client_id"][:6], "…")
