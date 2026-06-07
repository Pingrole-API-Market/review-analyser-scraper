"""
Example: run the Actor from Python and read results.

File delivery (email / Discord) happens inside the Actor — the client does not
download attachments. Check delivery_status in the OUTPUT key after the run.
"""
import os

from apify_client import ApifyClient

ACTOR_ID = "oyxxsUyPX6Oa4P2h0"

client = ApifyClient(os.environ["APIFY_API_TOKEN"])

# --- Dataset only (no file delivery) ---
run_input = {
    "business_name": "Casa D' Angelo New York",
    "location": "New York, USA",
    "zip_code": "10013",
    "country": "US",
    "limit_per_platform": 50,
    "get_as_file": False,
}

# --- Or send report by email ---
# run_input = {
#     "business_name": "Casa D' Angelo New York",
#     "location": "New York, USA",
#     "zip_code": "10013",
#     "country": "US",
#     "limit_per_platform": 50,
#     "get_as_file": True,
#     "export_format": "xlsx",
#     "destination_platform": "email",
#     "destination_address": "you@example.com",
# }

# --- Or send report by Discord DM (join https://discord.gg/p5aCRvkHWE first) ---
# run_input = {
#     "business_name": "Casa D' Angelo New York",
#     "location": "New York, USA",
#     "zip_code": "10013",
#     "country": "US",
#     "limit_per_platform": 50,
#     "get_as_file": True,
#     "export_format": "xlsx",
#     "destination_platform": "discord",
#     "destination_address": "your_discord_username",
# }

run = client.actor(ACTOR_ID).call(run_input=run_input)
print(f"Run {run.id} — {run.status}")

for item in client.dataset(run.default_dataset_id).iterate_items():
    print(item)

if run_input.get("get_as_file"):
    output = client.key_value_store(run.default_key_value_store_id).get_record("OUTPUT")
    delivery = (output.get("value") or {}).get("delivery_status")
    if delivery:
        print("Delivery:", delivery)
    else:
        print("No delivery_status in OUTPUT — check Actor logs.")
