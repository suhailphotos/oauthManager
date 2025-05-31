#!/usr/bin/env python3
"""
listVaults.py

Uses the 1Password CLI to enumerate every vault, then every item in each vault.
Outputs a single JSON blob to stdout, in the format:

{
  "vaults": [
    {
      "id": "<vault-id>",
      "name": "<vault-name>",
      "items": [
        {
          "id": "<item-id>",
          "name": "<item-title>",
          "field_keys": ["username", "client_id", ...]
        },
        ...
      ]
    },
    ...
  ]
}

Empty vaults will have an empty "items": [] list.
"""

import subprocess
import json
import sys

def run_op_command(cmd_list):
    """
    Helper to run a subprocess command containing "op … --format json".
    Returns the parsed JSON object if successful, otherwise exits with an error.
    """
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd_list)}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from: {' '.join(cmd_list)}", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)

def list_all_vaults():
    return run_op_command(["op", "vault", "list", "--format", "json"])

def list_items_in_vault(vault_id):
    return run_op_command(["op", "item", "list", "--vault", vault_id, "--format", "json"])

def get_item_full(item_id, vault_id):
    return run_op_command(["op", "item", "get", item_id, "--vault", vault_id, "--format", "json"])

def main():
    vaults_raw = list_all_vaults()
    output = {"vaults": []}

    for vault in vaults_raw:
        vid = vault.get("id")
        vname = vault.get("name")
        items_raw = list_items_in_vault(vid)
        items_list = []
        for item in items_raw:
            item_id = item.get("id")
            item_name = (
                item.get("overview", {}).get("title")
                or item.get("title")
                or "(no title)"
            )

            # Get the full item to extract field_keys
            full_item = get_item_full(item_id, vid)
            field_keys = []
            for fld in full_item.get("fields", []):
                key_name = fld.get("label") or fld.get("designation") or fld.get("name")
                if key_name:
                    field_keys.append(key_name)

            items_list.append({
                "id": item_id,
                "name": item_name,
                "field_keys": field_keys
            })

        output["vaults"].append({
            "id": vid,
            "name": vname,
            "items": items_list
        })

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
