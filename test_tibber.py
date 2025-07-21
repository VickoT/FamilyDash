import requests
from dotenv import load_dotenv
import os

# Load the .env file where your Tibber API token is stored
load_dotenv()
TIBBER_TOKEN = os.getenv("TIBBER_TOKEN")

# GraphQL query to fetch electricity prices for today, tomorrow, and now
query = """
{
  viewer {
    homes {
      currentSubscription {
        priceInfo {
          current { startsAt energy }
          today { startsAt energy }
          tomorrow { startsAt energy }
        }
      }
    }
  }
}
"""

# Include the authentication token in the HTTP headers
headers = {
    "Authorization": f"Bearer {TIBBER_TOKEN}"
}

# Make a POST request to Tibber's GraphQL endpoint
response = requests.post(
    "https://api.tibber.com/v1-beta/gql",
    json={"query": query},
    headers=headers
)

# Parse the JSON response from the server
data = response.json()

# Extract the list of homes connected to your account
homes = data["data"]["viewer"]["homes"]

if not homes:
    print("No homes linked to your Tibber account.")
    exit(1)

# Get the price info object for the first home
price_info = homes[0]["currentSubscription"]["priceInfo"]

# Extract current, today and tomorrow price entries
price_current = price_info.get("current")
prices_today = price_info.get("today", [])
prices_tomorrow = price_info.get("tomorrow", [])

# Display current price if available
if price_current and price_current.get("energy") is not None:
    print(f"🔸 Current Price: {price_current['energy']:.4f} kr/kWh")

# Display today's prices
print("\n🔹 Electricity Prices – Today:")
for entry in prices_today:
    print(f"{entry['startsAt']} → {entry['energy']:.4f} kr/kWh")

# Display tomorrow's prices if available
if prices_tomorrow:
    print("\n🔸 Electricity Prices – Tomorrow:")
    for entry in prices_tomorrow:
        print(f"{entry['startsAt']} → {entry['energy']:.4f} kr/kWh")
else:
    print("\n🔸 Tomorrow: Not available yet.")
