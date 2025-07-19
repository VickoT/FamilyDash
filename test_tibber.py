import requests

TOKEN = "PAzsBbG5Sgzp13lfFSj8V3kaB3ns40PKJ3vZ-14ca9Y"

query = """
{
  viewer {
    homes {
      currentSubscription {
        priceInfo {
          today {
            startsAt
            energy
          }
          tomorrow {
            startsAt
            energy
          }
        }
      }
    }
  }
}
"""

headers = {"Authorization": f"Bearer {TOKEN}"}

response = requests.post(
    "https://api.tibber.com/v1-beta/gql",
    json={"query": query},
    headers=headers
)

data = response.json()

# Plocka ut data för idag och imorgon
homes = data["data"]["viewer"]["homes"]
if not homes:
    print("Inga hem kopplade till ditt konto.")
    exit(1)

price_info = homes[0]["currentSubscription"]["priceInfo"]
today = price_info.get("today", [])
tomorrow = price_info.get("tomorrow", [])

# Skriv ut alla tillgängliga timmar
print("🔹 Elpris – Idag:")
for entry in today:
    print(f"{entry['startsAt']} → {entry['energy']} kr/kWh")

if tomorrow:
    print("\n🔸 Elpris – Imorgon:")
    for entry in tomorrow:
        print(f"{entry['startsAt']} → {entry['energy']} kr/kWh")
else:
    print("\n🔸 Imorgon: Ej tillgängligt ännu.")
