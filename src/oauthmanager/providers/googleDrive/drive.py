from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from oauthmanager.providers.base import Provider
from oauthmanager.vaults.onepassword import OnePasswordVault, OPFieldError

class GoogleDriveProvider(Provider):
    """
    Auth method:  oauth2_client_file
    Expects in creds_config.json:

        {
          "name": "google_drive",
          "vault": "cloudSvc",
          "item":  "GoogleDrive",
          "auth": {
              "method": "oauth2_client_file",
              "document_title": "ml4vfxClientSecretFile",
              "token_cache": "~/.cache/oauthmanager/google_drive_token.json",
              "scopes": [ ... ]
          }
        }

    • client-secret JSON is stored as an **OP document** with that title
    • token.json is cached on disk so the browser pops up only once
    """

    required_fields: tuple[str, ...] = ("document_title",)


    def build_client(self, scopes: List[str] | None = None, **_) -> Any:
        vault_name: str = self.cfg["vault"]
        document_title: str = self.cfg["auth"]["document_title"]

        scopes = scopes or self.cfg["auth"].get(
            "scopes", ["https://www.googleapis.com/auth/drive.metadata.readonly"]
        )

        token_cache = Path(
            os.path.expanduser(self.cfg["auth"].get(
                "token_cache",
                "~/.cache/oauthmanager/google_drive_token.json"
            ))
        )
        token_cache.parent.mkdir(parents=True, exist_ok=True)

        creds: Credentials | None = None
        if token_cache.exists():
            creds = Credentials.from_authorized_user_file(token_cache, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # fetch the client-secret JSON document from 1Password
                secret_json = self._op_get_document(vault_name, document_title)

                # write to a temp file because Google API wants a path
                with tempfile.NamedTemporaryFile(
                    "w+", suffix=".json", delete=False
                ) as tmp:
                    tmp.write(secret_json)
                    tmp.flush()
                    flow = InstalledAppFlow.from_client_secrets_file(tmp.name, scopes)
                    creds = flow.run_local_server(port=0)
                Path(tmp.name).unlink(missing_ok=True)

            # cache token
            token_cache.write_text(creds.to_json())

        try:
            service = build("drive", "v3", credentials=creds)
            return service
        except HttpError as e:
            raise RuntimeError(f"Google Drive build() failed: {e}") from e

    # ------------------------------------------------------------------ #
    # helpers                                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _op_get_document(vault: str, title: str) -> str:
        """
        Returns the raw JSON string stored in the OP document.
        """
        try:
            out = subprocess.check_output(
                ["op", "document", "get", title, "--vault", vault], text=True
            )
            return out.strip()
        except subprocess.CalledProcessError as e:
            raise OPFieldError(
                f"Could not fetch OP document '{title}' from vault '{vault}'.\n{e.stderr}"
            ) from None
