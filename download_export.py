"""
Run the Actor and download the export file (XLSX/CSV/JSON) to the current directory.
"""
import os
from apify_client import ApifyClient

from client_helpers import download_export_file

ACTOR_ID = "oyxxsUyPX6Oa4P2h0"

client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run_input = {
    "business_name": "Casa D' Angelo New York",
    "location": "New York, USA",
    "zip_code": "10013",
    "country": "US",
    "limit_per_platform": 50,
    "export_as_file": True,
    "export_format": "xlsx",
}

print("Starting Actor run…")
run = client.actor(ACTOR_ID).call(run_input=run_input)
print(f"Run finished — status: {run['status']}  id: {run['id']}")

path = download_export_file(client, run)
if path:
    print(f"Saved: {path.resolve()}")
else:
    kv_id = run["defaultKeyValueStoreId"]
    print("No export file found in Key-Value store.")
    print(f"Check here: https://console.apify.com/storage/key-value-stores/{kv_id}")
