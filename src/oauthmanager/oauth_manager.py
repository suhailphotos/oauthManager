import subprocess
import os
import json
import time
from cryptography.fernet import Fernet
import platform

class AuthManager:
    """Base class for handling API authentication."""
    
    def get_credentials(self, service_name, **kwargs):
        """Method to be overridden by subclasses for specific credential retrieval."""
        raise NotImplementedError("Subclasses should implement this method.")


class OnePasswordAuthManager(AuthManager):
    """Subclass for 1Password authentication with encrypted caching."""

    def __init__(self, vault_name="API Keys", cache_file="credentials_cache.json", cache_ttl=86400):
        self.vault_name = vault_name
        self.cache_file = cache_file
        self.cache_ttl = cache_ttl  # Time to live for cache in seconds (e.g., 1 day)

        # Fetch or generate the encryption key on the fly
        self.encryption_key = self.get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.use_cache = os.getenv("OP_CACHE", "true").lower() == "true"
    
    def get_or_create_encryption_key(self):
        """Generate or fetch the encryption key."""
        key_file = self.get_key_file_path()
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def get_key_file_path(self):
        """Get the path to store the encryption key, platform-specific."""
        if platform.system() == "Windows":
            return os.path.join(os.getenv("APPDATA"), "oauthmanager", "encryption_key")
        else:
            return os.path.join(os.path.expanduser("~"), ".oauthmanager_key")

    def is_cache_expired(self):
        """Check if the cache is expired based on the cache TTL."""
        if not os.path.exists(self.cache_file):
            return True
        file_mtime = os.path.getmtime(self.cache_file)
        return time.time() - file_mtime > self.cache_ttl

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

    def _encrypt_cache(self, credentials):
        """Encrypt the credentials before saving to the cache."""
        with open(self.cache_file, 'wb') as f:
            encrypted_data = self.cipher.encrypt(json.dumps(credentials).encode())
            f.write(encrypted_data)

    def _decrypt_cache(self):
        """Decrypt the credentials from the cache."""
        try:
            with open(self.cache_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data).decode()
                return json.loads(decrypted_data)
        except Exception as e:
            print(f"Error decrypting cache: {e}")
            return None

    def get_cached_credentials(self):
        """Fetch credentials from the cache if they exist and aren't expired."""
        if not self.is_cache_expired():
            return self._decrypt_cache()
        return None

    def get_credentials(self, service_name, *fields):
        """
        Fetch credentials from 1Password or cache.

        Args:
            service_name (str): The name of the service in 1Password (e.g., 'Spotify').
            *fields: The fields to retrieve (e.g., 'client_id', 'client_secret', 'uri').

        Returns:
            dict: A dictionary containing the requested credentials.
        """
        # First, check if valid cached credentials exist
        credentials = self.get_cached_credentials()
        if credentials:
            print("Using cached credentials.")
            return credentials

        print("Cache expired or not found. Fetching from 1Password.")
        credentials = {}
        for field in fields:
            credentials[field] = self._read_op_field(service_name, field)
        
        # Encrypt and cache the fetched credentials
        self._encrypt_cache(credentials)

        return credentials

# Example Usage
if __name__ == "__main__":
    auth_manager = OnePasswordAuthManager()

    # Example for Spotify credentials, but it could be used for any API
    spotify_creds = auth_manager.get_credentials("Spotify", "client_id", "client_secret", "uri")
    
    print(f"Client ID: {spotify_creds['client_id']}")
    print(f"Client Secret: {spotify_creds['client_secret']}")
    print(f"Redirect URI: {spotify_creds['uri']}")
