from oauthmanager import AuthManager, OnePasswordAuthManager


auth_manager = OnePasswordAuthManager()
# Example for Spotify credentials, but it could be used for any API
spotify_creds = auth_manager.get_credentials("Spotify", "client_id", "client_secret", "uri")
    
print(f"Client ID: {spotify_creds['client_id']}")
print(f"Client Secret: {spotify_creds['client_secret']}")
print(f"Redirect URI: {spotify_creds['uri']}")
