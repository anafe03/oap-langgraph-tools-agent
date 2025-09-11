"""
Property listing creation and syndication tools.
"""
import aiohttp
from typing import Annotated
from langchain_core.tools import tool
import os
import json
 

# Supabase configuration via environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gdmdurzaeezcrgrmtabx.supabase.co")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

#@tool(name="insert_listing", description="Insert a new FSBO listing into the Supabase 'listings' table with proper schema matching.")
async def insert_listing(
    user_id: Annotated[str, "The seller's user_id (UUID)"],
    title: Annotated[str, "Listing title"],
    address: Annotated[str, "Full street address"],
    city: Annotated[str, "City"],
    state: Annotated[str, "State"],
    zip_code: Annotated[str, "Zip code"],
    price: Annotated[float, "Asking price in dollars (e.g., 350000)"],
    bedrooms: Annotated[int, "Number of bedrooms"] = None,
    bathrooms: Annotated[float, "Number of bathrooms"] = None,
    sqft: Annotated[int, "Square footage"] = None,
    lot_size: Annotated[str, "Lot size (e.g. '0.25 acres')"] = None,
    year_built: Annotated[int, "Year built"] = None,
    property_type: Annotated[str, "Property type (e.g. 'Single Family', 'Condo', 'Townhouse')"] = None,
    description: Annotated[str, "Detailed description"] = None,
    features: Annotated[dict, "Any extra features as JSON object"] = None,
    images: Annotated[list, "Array of image URLs"] = None,
) -> str:
    """
    Inserts a new FSBO listing into Supabase with the correct schema.
    Matches the exact database schema: id, user_id, title, description, price, address, city, state, zip_code, bedrooms, bathrooms, sqft, lot_size, year_built, property_type, features, images, status, views, created_at, updated_at
    """
    if not SERVICE_ROLE_KEY:
        return "❌ SUPABASE_SERVICE_ROLE_KEY is not set."

    url = f"{SUPABASE_URL}/rest/v1/listings"
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Build the row matching exact database schema
    row = {
        "user_id": user_id,
        "title": title,
        "address": address,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "price": price,
        "status": "active",
        "views": 0
    }
    
    # Add optional fields only if they're provided and not None
    if bedrooms is not None:
        row["bedrooms"] = bedrooms
    if bathrooms is not None:
        row["bathrooms"] = bathrooms
    if sqft is not None:
        row["sqft"] = sqft
    if lot_size is not None:
        row["lot_size"] = lot_size
    if year_built is not None:
        row["year_built"] = year_built
    if property_type is not None:
        row["property_type"] = property_type
    if description is not None:
        row["description"] = description
    if features is not None:
        row["features"] = features
    if images is not None:
        row["images"] = images

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=row) as resp:
                text = await resp.text()
                if resp.status >= 300:
                    return f"❌ Supabase error {resp.status}: {text}"
                
                inserted = json.loads(text)
                listing_id = inserted.get("id", "unknown")
                listing_title = inserted.get("title", "unknown")
                return f"✅ Successfully created listing '{listing_title}' with ID: {listing_id}"
                
    except Exception as e:
        return f"❌ Error inserting listing: {str(e)}"


@tool(name="make_listing", description="Create a formatted FSBO property listing preview from user inputs.")
async def make_listing(
    title: Annotated[str, "A short, attention-grabbing title for the property"],
    address: Annotated[str, "The full address of the property"],
    city: Annotated[str, "City"],
    state: Annotated[str, "State"], 
    price: Annotated[str, "The asking price for the property (e.g., '$350,000')"],
    bedrooms: Annotated[int, "Number of bedrooms"] = None,
    bathrooms: Annotated[float, "Number of bathrooms"] = None,
    sqft: Annotated[int, "Square footage of the home"] = None,
    description: Annotated[str, "Detailed description of the property"] = None,
) -> str:
    """Generate a formatted FSBO property listing preview based on user inputs."""
    
    listing = f"""
🏡 **{title}**

📍 **Address:** {address}, {city}, {state}
💰 **Price:** {price}
"""
    
    if bedrooms is not None:
        listing += f"🛏️ **Bedrooms:** {bedrooms}\n"
    if bathrooms is not None:
        listing += f"🛁 **Bathrooms:** {bathrooms}\n"
    if sqft is not None:
        listing += f"📐 **Square Feet:** {sqft:,}\n"
    
    if description:
        listing += f"\n📝 **Description:**\n{description}\n"
    
    listing += "\n_This is a preview. Use insert_listing to save it to the database._"
    
    return listing.strip()