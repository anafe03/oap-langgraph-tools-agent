import os
import httpx
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Configuration - Use your FastAPI backend, not Supabase directly
API_BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

async def _create_listing_async(
    title: str,
    address: str,
    price: float,  # Changed to float to match your models
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    sqft: Optional[int] = None,  # Match your field name
    property_type: Optional[str] = "house",
    description: Optional[str] = None,
    features: Optional[List[str]] = None,
    images: Optional[List[str]] = None,  # Match your field name
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None
) -> Dict[str, Any]:
    """Internal async function to create a listing via your FastAPI backend."""
    try:
        user_id = os.environ.get("CURRENT_USER_ID")
        if not user_id:
            return {"success": False, "error": "User authentication required"}

        # Get auth token (set by your FastAPI system message injection)
        auth_header = {}
        if user_id:
            # Your FastAPI backend handles auth via CURRENT_USER_ID env var
            # No need for explicit token here since it's handled by the system
            pass

        # Prepare listing data matching your ListingCreate model
        listing_data = {
            "title": title,
            "address": address,
            "price": price,  # Float, not cents
        }
        
        # Add optional fields only if provided
        if bedrooms is not None:
            listing_data["bedrooms"] = bedrooms
        if bathrooms is not None:
            listing_data["bathrooms"] = bathrooms
        if sqft is not None:
            listing_data["sqft"] = sqft
        if property_type:
            listing_data["property_type"] = property_type
        if description:
            listing_data["description"] = description
        if features:
            listing_data["features"] = features
        if images:
            listing_data["images"] = images
        if city:
            listing_data["city"] = city
        if state:
            listing_data["state"] = state
        if zip_code:
            listing_data["zip_code"] = zip_code

        # Call your FastAPI backend
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/listings/",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer fake_token_handled_by_system'  # Your system handles this
                },
                json=listing_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "success": True,
                    "listing": {
                        "id": result.get("id"),
                        "title": result.get("title"),
                        "address": result.get("address"),
                        "price": f"${result.get('price', 0):,.2f}",
                        "bedrooms": result.get("bedrooms"),
                        "bathrooms": result.get("bathrooms"),
                        "sqft": result.get("sqft"),
                        "property_type": result.get("property_type"),
                        "image_count": len(result.get("images", [])) if result.get("images") else 0
                    }
                }
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", str(error_data))
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                return {"success": False, "error": f"Backend error: {error_detail}"}
                
    except Exception as e:
        logger.error(f"Error creating listing: {str(e)}")
        return {"success": False, "error": f"Failed to create listing: {str(e)}"}

async def _update_listing_async(listing_id: str, **kwargs) -> Dict[str, Any]:
    """Internal async function to update a listing via your FastAPI backend."""
    try:
        user_id = os.environ.get("CURRENT_USER_ID")
        if not user_id:
            return {"success": False, "error": "User authentication required"}

        # Prepare update data (only non-None values)
        update_data = {}
        for key, value in kwargs.items():
            if value is not None:
                update_data[key] = value

        if not update_data:
            return {"success": False, "error": "No update data provided"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(
                f"{API_BASE_URL}/api/listings/{listing_id}",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer fake_token_handled_by_system'
                },
                json=update_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "success": True,
                    "listing": {
                        "id": result.get("id"),
                        "title": result.get("title"),
                        "address": result.get("address"),
                        "price": f"${result.get('price', 0):,.2f}",
                        "image_count": len(result.get("images", [])) if result.get("images") else 0
                    }
                }
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", str(error_data))
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                return {"success": False, "error": f"Update failed: {error_detail}"}
                
    except Exception as e:
        return {"success": False, "error": f"Failed to update: {str(e)}"}

async def _get_listings_async() -> Dict[str, Any]:
    """Internal async function to get user listings via your FastAPI backend."""
    try:
        user_id = os.environ.get("CURRENT_USER_ID")
        if not user_id:
            return {"success": False, "error": "User authentication required"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/listings/user/{user_id}",
                headers={
                    'Authorization': f'Bearer fake_token_handled_by_system'
                }
            )
            
            if response.status_code == 200:
                listings = response.json()
                
                formatted = []
                for listing in listings:
                    formatted.append({
                        "id": listing.get("id"),
                        "title": listing.get("title"),
                        "address": listing.get("address"),
                        "price": f"${listing.get('price', 0):,.2f}",
                        "bedrooms": listing.get("bedrooms"),
                        "bathrooms": listing.get("bathrooms"),
                        "views": listing.get("views", 0),
                        "image_count": len(listing.get("images", [])) if listing.get("images") else 0
                    })
                
                return {"success": True, "listings": formatted, "total_count": len(formatted)}
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", str(error_data))
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                return {"success": False, "error": f"Failed to fetch: {error_detail}"}
                
    except Exception as e:
        return {"success": False, "error": f"Failed to get listings: {str(e)}"}

def _run_async(coro):
    """Helper to run async functions safely."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

#@tool
def create_property_listing(
    title: str,
    address: str, 
    price: float,  # Changed to float
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    sqft: Optional[int] = None,
    property_type: Optional[str] = "house",
    description: Optional[str] = None,
    features: Optional[List[str]] = None,
    images: Optional[List[str]] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None
) -> str:
    """Create a new property listing using the FastAPI backend.
    
    Args:
        title: Property title
        address: Full address
        price: Price in dollars (float, e.g. 485000.00)
        bedrooms: Number of bedrooms (optional)
        bathrooms: Number of bathrooms (optional, can be decimal like 2.5)
        sqft: Size in square feet (optional)
        property_type: house, condo, townhouse, etc. (optional)
        description: Property description (optional)
        features: List of features (optional)
        images: List of image URLs (optional)
        city: City name (optional)
        state: State abbreviation (optional)  
        zip_code: ZIP code (optional)
    """
    result = _run_async(_create_listing_async(
        title=title, 
        address=address, 
        price=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms, 
        sqft=sqft,
        property_type=property_type, 
        description=description, 
        features=features, 
        images=images,
        city=city,
        state=state,
        zip_code=zip_code
    ))
    
    if result["success"]:
        info = result["listing"]
        return (f"✅ Successfully created '{info['title']}'!\n"
                f"📍 {info['address']}\n"
                f"💰 {info['price']}\n"
                f"🛏️ {info.get('bedrooms', 'N/A')}BR / 🚿 {info.get('bathrooms', 'N/A')}BA\n"
                f"📐 {info.get('sqft', 'N/A')} sq ft\n"
                f"📸 {info['image_count']} photo(s)\n"
                f"Your listing is now live!")
    else:
        return f"❌ Failed to create listing: {result['error']}"

#@tool 
def update_property_listing(
    listing_id: str,
    title: Optional[str] = None,
    address: Optional[str] = None,
    price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    sqft: Optional[int] = None,
    property_type: Optional[str] = None,
    description: Optional[str] = None,
    features: Optional[List[str]] = None,
    images: Optional[List[str]] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None
) -> str:
    """Update an existing property listing via FastAPI backend."""
    result = _run_async(_update_listing_async(
        listing_id=listing_id,
        title=title,
        address=address,
        price=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        sqft=sqft,
        property_type=property_type,
        description=description,
        features=features,
        images=images,
        city=city,
        state=state,
        zip_code=zip_code
    ))
    
    if result["success"]:
        info = result["listing"]
        return (f"✅ Updated '{info['title']}'!\n"
                f"📍 {info['address']}\n"
                f"💰 {info['price']}\n"
                f"📸 {info['image_count']} photo(s)")
    else:
        return f"❌ Failed to update: {result['error']}"

#@tool
def get_my_listings() -> str:
    """Get all property listings for the current user via FastAPI backend."""
    result = _run_async(_get_listings_async())
    
    if result["success"]:
        listings = result["listings"]
        if not listings:
            return "📋 No active listings. Want to create one?"
        
        response = f"📋 Your Listings ({result['total_count']}):\n\n"
        for i, listing in enumerate(listings, 1):
            response += (f"{i}. {listing['title']}\n"
                        f"   📍 {listing['address']}\n"
                        f"   💰 {listing['price']}\n"
                        f"   🛏️ {listing.get('bedrooms', 'N/A')}BR / 🚿 {listing.get('bathrooms', 'N/A')}BA\n"
                        f"   📊 {listing['views']} views\n"
                        f"   📸 {listing['image_count']} photo(s)\n\n")
        
        return response
    else:
        return f"❌ Failed to get listings: {result['error']}"

# Export tools for easy importing
LISTING_TOOLS = [
    create_property_listing,
    update_property_listing, 
    get_my_listings
]