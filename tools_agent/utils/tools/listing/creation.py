"""
Property listing creation and syndication tools.
"""
import aiohttp
from typing import Annotated
from langchain_core.tools import tool


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