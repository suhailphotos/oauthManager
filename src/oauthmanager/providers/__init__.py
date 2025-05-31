"""
Register built-in providers here.

External packages can register via entry-points:
    [project.entry-points."oauthmanager.providers"]
    my_service = "otherpackage.foo:MyProvider"
"""
from importlib import import_module
from typing import Dict, Type

from oauthmanager.providers.base import Provider

_BUILT_INS: Dict[str, str] = {
    "google_drive": "oauthmanager.providers.googleDrive.drive:GoogleDriveProvider",
    # "spotify":      "oauthmanager.providers.spotify.spotify:SpotifyProvider",
}


def load_provider(name: str) -> Type[Provider]:
    """
    Return the Provider subclass for *name*.
    """
    if name in _BUILT_INS:
        module_path, cls_name = _BUILT_INS[name].split(":")
        mod = import_module(module_path)
        return getattr(mod, cls_name)

    # FUTURE: fall back to entry-points
    raise KeyError(f"No provider registered for '{name}'")
