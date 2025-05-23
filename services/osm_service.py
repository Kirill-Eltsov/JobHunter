import asyncio
from config.api_url import OPEN_STREET_MAP_URL
import aiohttp
from utils.logger import log_error

async def get_city_by_location(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(OPEN_STREET_MAP_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                city = data["address"]["city"]
                return city
        except Exception as e:
            log_error(f"Ошибка (Openstreetmap): {e}")
            return ""

async def main():
    await get_city_by_location('56.765158', '60.544131')

if __name__ == "__main__":
    asyncio.run(main())