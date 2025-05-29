import os
import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import quote
from typing import List, Dict, Annotated

# from langchain_core.tools import tool  # uncomment to enable

# @tool(name="school_walkscore_lookup", description="Lookup WalkScore, TransitScore and nearby school ratings for a given address.")
async def school_walkscore_lookup(
    address: Annotated[str, "Full street address, e.g. '123 Maple Ave, Austin, TX'"],
    state: Annotated[str, "Two-letter state abbreviation, e.g. 'TX'"]
) -> Dict:
    """
    Returns walkscore, transit score, and up to 5 nearby school ratings from GreatSchools for the given address.
    Requires environment variables:
      - WALK_SCORE_API_KEY
      - GREAT_SCHOOLS_API_KEY
    """
    # Geocode address via Nominatim
    geocode_url = (
        f"https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=1"
        f"&q={quote(address)}"
    )
    async with aiohttp.ClientSession(headers={"User-Agent": "VestyAgent/1.0"}) as session:
        # Step 1: geocode
        async with session.get(geocode_url) as resp:
            resp.raise_for_status()
            geo_data = await resp.json()
            if not geo_data:
                raise ValueError(f"Could not geocode address: {address}")
            loc = geo_data[0]
            lat = loc.get("lat")
            lon = loc.get("lon")

        # Step 2: WalkScore API
        ws_key = os.getenv("WALK_SCORE_API_KEY")
        if not ws_key:
            raise EnvironmentError("WALK_SCORE_API_KEY not set")
        ws_url = (
            f"http://api.walkscore.com/score?format=json"
            f"&address={quote(address)}&lat={lat}&lon={lon}&wsapikey={ws_key}"
        )
        async with session.get(ws_url) as ws_resp:
            ws_resp.raise_for_status()
            ws_json = await ws_resp.json()

        # Step 3: GreatSchools API
        gs_key = os.getenv("GREAT_SCHOOLS_API_KEY")
        if not gs_key:
            raise EnvironmentError("GREAT_SCHOOLS_API_KEY not set")
        # Limit to 5 schools
        gs_url = (
            f"https://api.greatschools.org/schools/nearby?key={gs_key}"
            f"&state={state}&lat={lat}&lon={lon}&limit=5"
        )
        async with session.get(gs_url) as gs_resp:
            gs_resp.raise_for_status()
            # GreatSchools returns XML
            xml_text = await gs_resp.text()
            root = ET.fromstring(xml_text)

        schools: List[Dict] = []
        for school in root.findall('.//school'):
            name = school.findtext('name')
            rating = school.findtext('gsRating')
            level = school.findtext('level')
            dist = school.findtext('distance')
            url = school.findtext('schoolURL')
            schools.append({
                'name': name,
                'rating': rating,
                'level': level,
                'distance_miles': dist,
                'url': url,
            })

    # Assemble result
    result = {
        'address': address,
        'latitude': lat,
        'longitude': lon,
        'walk_score': ws_json.get('walkscore'),
        'walk_description': ws_json.get('description'),
        'transit_score': ws_json.get('transit') and ws_json['transit'].get('score'),
        'transit_description': ws_json.get('transit') and ws_json['transit'].get('description'),
        'nearby_schools': schools,
    }
    return result
