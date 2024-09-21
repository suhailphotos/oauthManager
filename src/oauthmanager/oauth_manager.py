# src/oauthmanager/auth_manager.py
import subprocess
import os

class AuthManager:
    """Base class for handling API authentication."""
    
    def get_credentials(self, service_name, **kwargs):
        """Method to be overridden by subclasses for specific credential retrieval."""
        raise NotImplementedError("Subclasses should implement this method.")


class OnePasswordAuthManager(AuthManager):
    """Subclass for 1Password authentication."""

    def __init__(self, vault_name="API Keys"):
        self.vault_name = vault_name
        self.use_cache = os.getenv("OP_CACHE", "true").lower() == "true"
    
    def _read_op_field(self, item_name, field_name):
        """Helper method to read a specific field from 1Password using the CLI."""
        try:
            op_path = f'op://{self.vault_name}/{item_name}/{field_name}'
            cmd = ["op", "read", f"{op_path}"]
            if self.use_cache:
                cmd.append("--cache")
            result = subprocess.run(cmd, capture_output=True, text=True)
            result.check_returncode()
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error fetching {field_name}: {e}")
            return None

    def get_credentials(self, service_name, *fields):
        """
        Fetch credentials from 1Password.

        Args:
            service_name (str): The name of the service in 1Password (e.g., 'Spotify').
            *fields: The fields to retrieve (e.g., 'client_id', 'client_secret', 'uri').

        Returns:
            dict: A dictionary containing the requested credentials.
        """
        credentials = {}
        for field in fields:
            credentials[field] = self._read_op_field(service_name, field)
        
        return credentials

# Example Usage
if __name__ == "__main__":
    auth_manager = OnePasswordAuthManager()
    
    # Example for Spotify credentials, but it could be used for any API
    spotify_creds = auth_manager.get_credentials("Spotify", "client_id", "client_secret", "uri")
    
    print(f"Client ID: {spotify_creds['client_id']}")
    print(f"Client Secret: {spotify_creds['client_secret']}")
    print(f"Redirect URI: {spotify_creds['uri']}")
