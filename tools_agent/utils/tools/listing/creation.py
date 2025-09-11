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

#@tool@tool
async def insert_listing(
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
    Insert a new FSBO listing into the Supabase 'listings' table.
    Automatically gets the user_id from the current chat context.
    """
    
    # Get user ID from environment variable (set by chat context)
    user_id = os.getenv("CURRENT_USER_ID")
    if not user_id:
        return "❌ User authentication required. Please make sure you're logged in and try again."
    
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
                
                # FIX: Handle both list and dict responses from Supabase
                try:
                    inserted = json.loads(text)
                    
                    # If Supabase returns a list, get the first item
                    if isinstance(inserted, list):
                        if len(inserted) > 0:
                            listing_data = inserted[0]
                        else:
                            return "❌ No data returned from database"
                    else:
                        # If it's already a dict, use it directly
                        listing_data = inserted
                    
                    # Now safely get the values
                    listing_id = listing_data.get("id", "unknown")
                    listing_title = listing_data.get("title", "unknown")
                    
                    return f"✅ Successfully created listing '{listing_title}' with ID: {listing_id}. Your listing is now live and can be viewed by potential buyers!"
                    
                except json.JSONDecodeError:
                    return f"❌ Invalid JSON response from database: {text}"
                
    except Exception as e:
        return f"❌ Error inserting listing: {str(e)}"

#@tool
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
    """Create a formatted FSBO property listing preview from user inputs."""
    
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


# Legacy function for backward compatibility
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