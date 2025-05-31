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
        { "id": "<item-id>", "name": "<item-title>" },
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
    """
    Runs: op vault list --format json
    Returns a list of vault dicts, each having "id" and "name" keys (and other metadata).
    """
    return run_op_command(["op", "vault", "list", "--format", "json"])

def list_items_in_vault(vault_id):
    """
    Runs: op item list --vault <vault_id> --format json
    Returns a list of item dicts, each having keys like "id", "overview", etc.
    We will extract "id" and "overview.title" as name.
    """
    return run_op_command(["op", "item", "list", "--vault", vault_id, "--format", "json"])

def main():
    # 1) Get all vaults (list of dicts with "id" and "name")
    vaults_raw = list_all_vaults()

    output = {"vaults": []}

    for vault in vaults_raw:
        vid = vault.get("id")
        vname = vault.get("name")

        # 2) For each vault, get all items
        items_raw = list_items_in_vault(vid)

        # 3) Build item list with only id + name
        items_list = []
        for item in items_raw:
            item_id = item.get("id")
            # "overview" always exists if the item has a title
            # Try “overview.title” first; if missing, try “title” at the top level
            item_name = (
                item.get("overview", {}).get("title")
                or item.get("title")
                or "(no title)"
            )
            items_list.append({
                "id": item_id,
                "name": item_name
            })

        # 4) Append this vault + its items to the output
        output["vaults"].append({
            "id": vid,
            "name": vname,
            "items": items_list
        })

    # 5) Print the final JSON to stdout, nicely indented
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
