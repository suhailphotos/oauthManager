import json
from pathlib import Path
from typing import Any

from oauthmanager.vaults.onepassword import OnePasswordVault
from oauthmanager.providers import load_provider


CFG_PATH = Path.home() / ".oauthmanager" / "creds_config.json"
_VAULT = OnePasswordVault()


def _load_cfg() -> dict:
    return json.loads(CFG_PATH.read_text())


def get_client(service: str, **overrides: Any):
    """
    Public helper:  client = get_client("google_drive")
    """
    cfg = _load_cfg()
    block = next(p for p in cfg["providers"] if p["name"] == service)

    ProviderCls = load_provider(service)

    auth = block["auth"]
    method = auth["method"]

    # minimal routing – only need to fetch OP secrets for methods that require it
    if method == "oauth2_client_file":
        # we only need the document title (no normal fields)
        secrets = {}
    elif method in {"oauth2_client", "service_keys", "api_token", "basic_auth"}:
        fields = auth.get("fields") or [auth.get("field")]
        secrets = _VAULT.fetch(block["vault"], block["item"], tuple(fields))
    else:
        secrets = {}

    provider = ProviderCls(secrets, block)
    return provider.build_client(**overrides)
