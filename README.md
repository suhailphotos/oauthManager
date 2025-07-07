# oauthManager

A lightweight wrapper that centralises **API authentication** for your projects while keeping raw secrets *out of the codebase*.

* 🔐 Secrets live in **1Password** (via the official CLI).
* 🗄️ Config lives in **`~/.config/oauthmanager/creds_config.json`** (portable across hosts).
* 📦 Each provider returns a **ready‑to‑use SDK client** – no boilerplate.
* 🧩 Designed to be *imported* from any other package or script.

Currently‑bundled providers:

| Provider         | Auth method                                                                               | What you get                                                                                                                                 |
| ---------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Google Drive** | OAuth 2.0 – Client‑Secret *file* (stored as 1Password **Document**)                       | A fully authorised [`googleapiclient.discovery.build("drive", "v3")`](https://developers.google.com/drive/api/v3/quickstart/python) instance |
| **Spotify**      | OAuth 2.0 – PKCE / Client‑Secret (**user scopes**) *or* Client‑Credentials (**app‑only**) | A [`spotipy.Spotify`](https://spotipy.readthedocs.io/) client with auto‑refreshing tokens                                                    |

> ✨ More services can be added via the `oauthmanager.providers` entry‑point – see `providers/base.py`.

---

## 1  Installation

```bash
pip install --upgrade oauthmanager            # from PyPI
# or
pip install --user ~/oauthmanager‑0.1.12‑py3‑none‑any.whl  # self‑built wheel
```

### 1.1 One‑time initialisation (per host)

```bash
# 1Password CLI must already be signed in / unlocked
#  (eval $(op signin) … or Service‑Account token)

oauthmanager init   # → creates ~/.config/oauthmanager & copies template files
```

Files created:

```
~/.config/oauthmanager/
├── creds_config.json   # main config – edit me
├── creds_config.md     # inline docs
└── .env                # optional runtime overrides
```

---

## 2  Wiring up 1Password secrets

### 2.1 Google Drive

1. In the Google Cloud Console → OAuth 2.0 client, **download the JSON**.
2. **Upload that JSON as a 1Password *Document*** (e.g. name it `ml4vfxClientSecretFile`) in vault `cloudSvc`.
3. Ensure your `creds_config.json` has:

```jsonc
{
  "name": "google_drive",
  "vault": "cloudSvc",
  "item":  "GoogleDrive",          // any title you like
  "auth": {
    "method": "oauth2_client_file",
    "document_title": "ml4vfxClientSecretFile",
    "token_cache": "~/.cache/oauthmanager/google_drive_token.json",
    "scopes": [
      "https://www.googleapis.com/auth/drive.metadata.readonly"
    ]
  }
}
```

### 2.2 Spotify

1. In the Spotify Developer Dashboard add a **Redirect URI**.   Example:
   `http://127.0.0.1:8765/callback`
2. Add (or update) a 1Password item in vault `mediaAPIs` with fields:

| field key                                       | value                            |
| ----------------------------------------------- | -------------------------------- |
| `client_id`                                     | *Your App Client ID*             |
| `client_secret` *(optional – omit to use PKCE)* | *Your Client Secret*             |
| `redirect_uri`                                  | `http://127.0.0.1:8765/callback` |

3. Config block:

```jsonc
{
  "name": "spotify",
  "vault": "mediaAPIs",
  "item":  "Spotify",
  "auth": {
    "method": "oauth2_client",          // or "client_credentials"
    "fields": ["client_id", "client_secret", "redirect_uri"],
    "token_cache": "~/.cache/oauthmanager/spotify_token.json",
    "scopes": [
      "playlist-read-private",
      "playlist-modify-private",
      "user-library-read",
      "user-read-private"
    ]
  }
}
```

---

## 3  Using oauthManager in *any* script

```python
from oauthmanager.core import get_client
```

### 3.1 Google Drive example

```python
# Obtain a Drive SDK client (scopes pulled from config)
drive = get_client("google_drive")

resp = drive.files().list(pageSize=5, fields="files(id,name)").execute()
for f in resp["files"]:
    print(f["name"], f["id"])
```

*First run* shows the Google OAuth consent screen; a token is cached at
`~/.cache/oauthmanager/google_drive_token.json` and refreshed automatically.

### 3.2 Spotify example (headless SSH flow)

```python
sp = get_client("spotify", open_browser=False)  # hands you a Spotipy client

for p in sp.current_user_playlists(limit=10)["items"]:
    print(p["name"])
```

*First run* prints a long **authorise URL**.

1. Copy–paste it into your local browser.
2. Approve permissions; Spotify redirects to `127.0.0.1:8765/callback?code=…` and fails to load.
3. Copy that full URL back into the SSH prompt → tokens are stored in the cache file.

> Prefer a seamless browser flow?  `ssh -L 8765:127.0.0.1:8765 nimbus` then omit `open_browser=False`.

---

## 4  Inside other packages

Just import `oauthmanager.core.get_client` – no extra dependencies:

```python
# mymusiclib/utils.py
from oauthmanager.core import get_client

_sp = None

def spotify():
    global _sp
    if _sp is None:
        _sp = get_client("spotify")
    return _sp
```

Your library stays API‑agnostic; oauthManager handles secrets, token refresh, and retries.

---

## 5  FAQ

| Q                                       | A                                                                                                                                                            |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Where are secrets stored?**           | In 1Password only. OauthManager pulls them on demand via the `op` CLI, encrypts a short‑lived cache on disk (`~/.cache/oauthmanager/credentials_cache.enc`). |
| **How do I invalidate a cached token?** | Delete the token file or `OP_FRESH=1 python myscript.py`.                                                                                                    |
| **Can I add my own provider?**          | Yes – create a subclass of `oauthmanager.providers.base.Provider` and register it via `project.entry‑points."oauthmanager.providers"` in your own package.   |

---

## 6  Directory layout

| Path                      | Purpose                                             |
| ------------------------- | --------------------------------------------------- |
| `~/.config/oauthmanager/` | Human‑editable config & docs                        |
| `~/.cache/oauthmanager/`  | Auto‑generated token + encrypted secret cache       |
| `~/.oauthmanager_key`     | Encryption key for the cache (created on first run) |

---

## 7  Development

```bash
poetry install
pytest -q
```

Build & publish:

```bash
poetry version patch
poetry build
poetry publish  # requires PYPI_TOKEN in env or configured in Poetry
```

---

## License

MIT © Suhail

