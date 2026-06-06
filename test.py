import os
from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

# Prepare the Actor input
run_input = {
    "business_name": "Casa D' Angelo New York",
    "location": "New York, USA",
    "zip_code": "10013",
    "country": "US",
    "limit_per_platform": 50,
    "export_as_file": True,
    "export_format": "xlsx",
}

# Run the Actor and wait for it to finish
run = client.actor("oyxxsUyPX6Oa4P2h0").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)