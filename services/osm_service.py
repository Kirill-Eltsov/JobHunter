# from config import OPEN_STREET_MAP_URL

async def get_city_by_location(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://nominatim.openstreetmap.org/reverse", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                city = data["address"]["city"]
                return city

        except:
            return ""

def main():
    get_city_by_location('56.765158', '60.544131')

if __name__ == "__main__":
    main()
    # get_city_by_location('56.765158', '60.544131')