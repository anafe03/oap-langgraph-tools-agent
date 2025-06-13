"""
Property listing creation and syndication tools.
"""
import aiohttp
from typing import Annotated
from langchain_core.tools import tool
import os
import json
 

#@tool(name="make_listing", description="Create a FSBO property listing by gathering key details from the seller.")
async def make_listing(
    title: Annotated[str, "A short, attention-grabbing title for the property (e.g., 'Charming 3-Bedroom Bungalow with Large Yard')"],
    address: Annotated[str, "The full address of the property"],
    price: Annotated[str, "The asking price for the property (e.g., '$350,000')"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Approximate square footage of the home"],
    description: Annotated[str, "Detailed description of the property, including features, updates, or neighborhood highlights"],
    horse_friendly: Annotated[str, "Do they allow horses?"]
) -> str:
    """Generate a formatted FSBO property listing based on user inputs."""
    
    listing = f"""
🏡 **{title}**

📍 **Address:** {address}
💰 **Price:** {price}
🛏️ **Bedrooms:** {bedrooms}
🛁 **Bathrooms:** {bathrooms}
📐 **Square Feet:** {square_feet:,}
🐎 **Horse Friendly:** {horse_friendly}

📝 **Description:**
{description}

_Interested buyers can contact the seller directly to schedule a showing or request more information._
"""
    return listing.strip()


#@tool(name="syndicate_listing", description="Send a completed FSBO listing to the MLS via API for broader exposure.")
async def syndicate_listing(
    title: Annotated[str, "The listing title"],
    address: Annotated[str, "The property address"],
    price: Annotated[str, "The listing price"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Total square footage"],
    description: Annotated[str, "The detailed listing description"],
    access_token: Annotated[str, "Your API token to authenticate with the MLS service"],
    mls_api_url: Annotated[str, "The URL of the MLS listing API endpoint"]
) -> str:
    """Submits the listing data to the MLS system."""
    payload = {
        "title": title,
        "address": address,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "square_feet": square_feet,
        "description": description
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                mls_api_url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
        return f"✅ Listing successfully syndicated to MLS. MLS ID: {response_data.get('listing_id', 'unknown')}"
    except Exception as e:
        return f"❌ Failed to syndicate listing: {str(e)}"
    


# Supabase configuration via environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gdmdurzaeezcrgrmtabx.supabase.co")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

#@tool(name="insert_listing",description=("Insert a new FSBO listing into the Supabase 'listings' table. ""Arguments: {user_id: str, title: str, address: str, price: float, bedrooms: int, ""bathrooms: float, square_feet: int, description: str, horse_friendly: str}."))
async def insert_listing(
    user_id: Annotated[str, "The seller's user_id"],
    title: Annotated[str, "Listing title"],
    address: Annotated[str, "Property address"],
    price: Annotated[float, "Asking price"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Square footage"],
    description: Annotated[str, "Detailed description"],
    horse_friendly: Annotated[str, "'yes' or 'no'"]
) -> str:
    """
    Calls the Supabase REST API to insert one row into the 'listings' table,
    returns the inserted record or an error message.
    """
    if not SERVICE_ROLE_KEY:
        return "❌ Environment variable SUPABASE_SERVICE_ROLE_KEY is not set."

    url = f"{SUPABASE_URL}/rest/v1/listings?return=representation"
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    payload = [{
        "user_id": user_id,
        "title": title,
        "address": address,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqft": square_feet,
        "description": description,
        "horse_friendly": horse_friendly,
        "status": "active"
    }]

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            text = await resp.text()
            if resp.status >= 300:
                return f"❌ Supabase error {resp.status}: {text}"
            inserted = json.loads(text)
            # Supabase returns a list of inserted rows
            return f"✅ Inserted listing: {inserted[0]}"
