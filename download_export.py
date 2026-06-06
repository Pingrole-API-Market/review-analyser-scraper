"""
Run the Actor and download the export file (XLSX/CSV/JSON) to the current directory.
This is a companion to test.py — it does the same run but also saves the export file locally.
"""
import os
from apify_client import ApifyClient

API_TOKEN = os.environ["APIFY_API_TOKEN"]
ACTOR_ID  = "oyxxsUyPX6Oa4P2h0"

client = ApifyClient(API_TOKEN)

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
print(f"Run finished — status: {run['status']}")

# Download the export file from the Key-Value Store
kv_id = run["defaultKeyValueStoreId"]
kv    = client.key_value_store(kv_id)

found = False
for item in kv.list_keys()["items"]:
    key = item["key"]
    if key.endswith((".xlsx", ".csv", ".json")) and key != "INPUT" and key != "OUTPUT":
        record = kv.get_record(key, as_bytes=True)
        with open(key, "wb") as f:
            f.write(record["value"])
        print(f"Saved: {key}  ({len(record['value'])} bytes)")
        found = True
        break

if not found:
    print("No export file found. Make sure export_as_file is True and the Actor run succeeded.")
    print(f"KV store: https://console.apify.com/storage/key-value-stores/{kv_id}")
