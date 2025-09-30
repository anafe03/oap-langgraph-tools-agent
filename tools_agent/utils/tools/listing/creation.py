import os
import httpx
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool, InjectedToolArg
from langchain_core.runnables import RunnableConfig
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

# Configuration - Use your FastAPI backend
API_BASE_URL = os.getenv("BASE_URL", "https://vesty-app-fastapi.onrender.com")

#@tool
def _get_user_context_from_config(config: Optional[RunnableConfig] = None) -> Dict[str, str]:
    """Extract user context from the RunnableConfig passed by LangGraph."""
    if not config:
        raise ValueError("No configuration provided - user authentication required")
    
    # Try multiple ways to get user info
    configurable = config.get("configurable", {})
    
    # Method 1: Direct from configurable
    user_id = (
        configurable.get("current_user_id") or 
        configurable.get("langgraph_auth_user_id") or 
        configurable.get("user_id")
    )
    user_email = configurable.get("user_email")
    
    # Method 2: From environment variables (LangGraph might set these)
    if not user_id:
        user_id = os.getenv("CURRENT_USER_ID")
    if not user_email:
        user_email = os.getenv("USER_EMAIL")
    
    logger.info(f"Extracted user context - ID: {user_id}, Email: {user_email}")
    
    if not user_id:
        logger.error(f"Failed to get user ID. Config: {config}")
        raise ValueError("User authentication required - please log in")
    
    return {
        "user_id": str(user_id),
        "user_email": user_email or "unknown@example.com"
    }

#@tool
async def _create_listing_with_auth(
    title: str,
    address: str,
    price: float,
    user_context: Dict[str, str],
    supabase_token: str,
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
) -> Dict[str, Any]:
    """Create listing using FastAPI backend with proper authentication."""
    try:
        # Prepare listing data with user_id included
        listing_data = {
            "title": title,
            "address": address,
            "price": price,
            "user_id": user_context["user_id"]
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

        # Use Supabase token for authentication
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {supabase_token}',
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/listings/",
                headers=headers,
                json=listing_data
            )
            
            logger.info(f"FastAPI response status: {response.status_code}")
            logger.info(f"FastAPI response text: {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
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
                
                logger.error(f"FastAPI error: {error_detail}")
                return {"success": False, "error": f"Backend error: {error_detail}"}
                
    except Exception as e:
        logger.error(f"Error creating listing: {str(e)}")
        return {"success": False, "error": f"Failed to create listing: {str(e)}"}

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
    price: float,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    sqft: Optional[int] = None,
    property_type: Optional[str] = "house",
    description: Optional[str] = None,
    features: Optional[List[str]] = None,
    images: Optional[List[str]] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None
) -> str:
    """Create a new property listing using the FastAPI backend with proper authentication."""
    try:
        # Get user context from LangGraph config
        user_context = _get_user_context_from_config(config)
        logger.info(f"Creating listing for user: {user_context['user_id']}")
        
        # Get Supabase token from config
        configurable = config.get("configurable", {})
        supabase_token = configurable.get("x-supabase-access-token")
        
        if not supabase_token:
            logger.error("No Supabase token found in config")
            return "❌ Authentication token not found. Please log in again."
        
        result = _run_async(_create_listing_with_auth(
            title=title, 
            address=address, 
            price=price,
            user_context=user_context,
            supabase_token=supabase_token,
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
    
    except ValueError as e:
        logger.error(f"Authentication error: {str(e)}")
        return f"❌ User authentication required. Please make sure you're logged in and try again."
    except Exception as e:
        logger.error(f"Unexpected error in create_property_listing: {e}")
        return f"❌ Unexpected error: {str(e)}"

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
    zip_code: Optional[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None
) -> str:
    """Update an existing property listing via FastAPI backend."""
    return "Update listing functionality - placeholder implementation"

#@tool
def get_my_listings(config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
    """Get all property listings for the current user via FastAPI backend."""
    return "Get listings functionality - placeholder implementation"

# Export tools for easy importing
LISTING_TOOLS = [
    create_property_listing,
    update_property_listing, 
    get_my_listings
]