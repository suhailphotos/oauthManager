import subprocess
import os
import json
import time
from cryptography.fernet import Fernet

class AuthManager:
    """Base class for handling API authentication"""

    def get_credentials(self, service_name, **kwargs):
        """Method to be overridden by subclass for specific credential retrival."""
        raise NotImplementedError("Subclasses should implement this method.")
