
# OAuthManager

OAuthManager is a Python package for managing API authentication using 1Password Service Accounts and securely caching credentials.

## Features

- Manage API credentials securely via 1Password.
- Cache API credentials locally using encryption for faster retrieval.
- Designed to be extensible for any API that requires authentication.

## Requirements

- Python 3.11 or later
- 1Password Service Account
- 1Password CLI
- An environment variable for your 1Password service account token (`OP_SERVICE_ACCOUNT_TOKEN`).
- `cryptography` Python package

## Installation

1. **Install Python and Pip**

   Ensure you have Python 3.11 installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

2. **Install the OAuthManager package**

   You can install the OAuthManager package directly from PyPI:
   ```bash
   pip install oauthmanager
   ```

## Setting Up 1Password Service Account

### 1. Create a 1Password Account

   To begin, [sign up for a 1Password account](https://1password.com/). You will need to be on a 1Password Teams, Business, or Enterprise plan to create service accounts.

### 2. Create a 1Password Service Account

   A service account allows OAuthManager to securely retrieve your API credentials. Follow the steps below to create one:

#### Create Service Account via 1Password Website

1. **Sign in** to your account on [1Password.com](https://1password.com/).
2. Select **Developer Tools** in the sidebar.
3. Under **Infrastructure Secrets Management**, select **Other**.
4. Click **Create a Service Account** and follow the instructions:
   - Choose a name for the service account.
   - Choose whether the service account can create vaults.
   - Choose the vaults that the service account can access (make sure it can access your API vault).
   - Click **Create Account**.
   - Click **Save in 1Password** to store your service account token.

⚠️ **Important:** The service account token is shown only once during the creation process. Save it immediately in your 1Password account.

### 3. Set Environment Variables

#### Platform-Specific Instructions

You will need to set two environment variables:
- `OP_SERVICE_ACCOUNT_TOKEN`: The service account token created in the previous step.
- `OP_CACHE`: Enable caching for faster retrieval.

#### macOS/Linux

1. Open your terminal.
2. Use the following command to open your `.bashrc`, `.bash_profile`, or `.zshrc` (depending on your shell):

   ```bash
   nano ~/.bashrc
   ```

3. Add the following lines to export your service account token and enable caching:

   ```bash
   export OP_SERVICE_ACCOUNT_TOKEN="your-service-account-token"
   export OP_CACHE="true"
   ```

4. Save the file and run:

   ```bash
   source ~/.bashrc
   ```

#### Windows

1. Open the **Command Prompt** as Administrator.
2. Set the environment variables:

   ```cmd
   setx OP_SERVICE_ACCOUNT_TOKEN "your-service-account-token"
   setx OP_CACHE "true"
   ```

   This sets the variables globally. Restart the terminal for them to take effect.

## Usage

Once you’ve installed OAuthManager and set up the necessary environment variables, you can start retrieving credentials from 1Password.

### Example Code:

```python
from oauthmanager import AuthManager, OnePasswordAuthManager

# Initialize the Auth Manager
auth_manager = OnePasswordAuthManager()

# Retrieve credentials for Spotify
spotify_creds = auth_manager.get_credentials("Spotify", "client_id", "client_secret", "uri")

# Use the credentials
print(f"Client ID: {spotify_creds['client_id']}")
print(f"Client Secret: {spotify_creds['client_secret']}")
print(f"Redirect URI: {spotify_creds['uri']}")
```

### Caching

By default, the OAuthManager caches credentials locally using encryption. To refresh the cache, simply delete the `credentials_cache.json` file, or let it expire after 24 hours.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

