oauthManager — credentials template

creds_config.json must be valid JSON.
This companion file explains the shape, allowed values, and examples.

⸻

Top-level structure

{
  "providers": [ /* array of provider blocks */ ]
}

Provider block keys

key	type	required	purpose
name	str	✓	lowercase identifier used by provider code (google_drive, spotify, …)
vault	str	✓	1Password vault name that stores the secrets
item	str	✓	item title in that vault (or document title for file-based creds)
auth	obj	✓	describes which authentication pattern and which fields/documents are required


⸻

auth.method values

method	when to use	required fields in auth
api_token	single static token	field – label of the token field
oauth2_client	client ID + secret (plus redirect URI)	fields – array of labels
oauth2_client_file	vendor supplies a JSON client-secret file (e.g. Google)	document_title, token_cache, scopes
service_keys	Supabase-style anon / service keys	fields – array
basic_auth	username + password	fields – array
ssh_key	private key (optional passphrase)	fields – array

Add new patterns as you encounter them.

⸻

Example blocks

Google Drive

{
  "name": "google_drive",
  "vault": "cloudSvc",
  "item": "GoogleDrive",
  "auth": {
    "method": "oauth2_client_file",
    "document_title": "ml4vfxClientSecretFile",
    "token_cache": "~/.cache/oauthmanager/google_drive_token.json",
    "scopes": [
      "https://www.googleapis.com/auth/drive.metadata.readonly"
    ]
  }
}

Spotify

{
  "name": "spotify",
  "vault": "mediaAPIs",
  "item": "Spotify",
  "auth": {
    "method": "oauth2_client",
    "fields": ["client_id", "client_secret", "redirect_uri"],
    "token_cache": "~/.cache/oauthmanager/spotify_token.json",
    "scopes": ["playlist-read-private"]
  }
}


⸻

Duplicate and adapt these stubs for new providers. After editing, always run jq . ~/.oauthmanager/creds_config.json (or any JSON validator) to confirm it’s still valid.
