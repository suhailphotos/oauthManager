from oauthmanager.core import get_client

drive = get_client("google_drive")                     # uses scopes from config
# OR
drive = get_client("google_drive", scopes=[
        "https://www.googleapis.com/auth/drive"
])

# list 10 files to prove it works
resp = drive.files().list(pageSize=10, fields="files(id,name)").execute()
for f in resp["files"]:
    print(f["name"], f["id"])
