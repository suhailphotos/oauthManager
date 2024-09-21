# API Authorization and Credentials Manager

Centralized repository for managing API authorizations and credentials across multiple projects.

## Purpose

This repository is designed to store and manage all the API credentials and authorization methods used in various projects. 
By keeping credentials in one place, we can easily access and reuse them across different services and avoid duplication of sensitive information.

## Features

- Manage multiple API authorizations in a single repository.
- Store credentials in a secure environment with the use of environment variables.
- Supports a wide variety of APIs including Spotify, Google, and more.
- Designed to be scalable and modular for adding new API integrations.

## Structure

- `config/`: Contains configuration files for each API.
- `credentials/`: Stores encrypted credentials for secure access.
- `scripts/`: Useful scripts for initializing authorization tokens and managing API sessions.

## Usage

1. Clone the repository:
    ```bash
    git clone https://github.com/suhailphotos/api-authorization-manager.git
    ```

2. Set up environment variables:
    ```bash
    export CREDENTIALS_PATH=/path/to/your/credentials
    ```

3. Run authorization script for specific API:
    ```bash
    python scripts/authorize_api.py --api spotify
    ```

## Security

Ensure that all sensitive information such as API keys and OAuth tokens are stored securely and never hardcoded in scripts. 
Use environment variables or secure vaults to manage access.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

