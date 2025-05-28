"""
Social media marketing tools for real estate listings.
"""
import aiohttp
from typing import Annotated
from langchain_core.tools import tool
from ..common.config import (
    FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID, TWITTER_BEARER_TOKEN,
    validate_facebook_config, validate_twitter_config
)


#@tool(name="generate_property_listing_tweet", description="Generate a short tweet for a property listing")
def generate_property_listing_tweet(
    title: Annotated[str, "Listing title (e.g., 'Charming 3BR Bungalow')"],
    address: Annotated[str, "Street address (e.g., '1234 Elm St, Chicago, IL')"],
    price: Annotated[str, "Price (e.g., '$420,000')"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Total square footage"],
) -> str:
    """Returns a short tweet string announcing a new property listing."""
    tweet = f"""
🏡 {title}
📍 {address}
💰 {price}
🛏️ {bedrooms} bd | 🛁 {bathrooms} ba | 📐 {square_feet} sqft

New on the market!
#realestate #FSBO #homeforsale
""".strip()

    if len(tweet) > 280:
        tweet = tweet[:276] + "..."

    return tweet


#@tool(name="post_to_twitter", description="Post any custom message to Twitter")
async def post_to_twitter(
    text: Annotated[str, "The tweet content (must be under 280 characters)"]
) -> str:
    """
    Posts a plain text tweet to Twitter using the API v2.
    Requires TWITTER_BEARER_TOKEN in environment variables.
    """
    if not validate_twitter_config():
        return """
❌ **Twitter API Configuration Required**

To post automatically to Twitter, please set this environment variable:
- TWITTER_BEARER_TOKEN: Your Twitter API bearer token

**Alternative:** Copy the tweet content and post manually on Twitter.

**Getting Twitter API Access:**
1. Go to Twitter Developer Portal (developer.twitter.com)
2. Create an app and get bearer token
3. Set the TWITTER_BEARER_TOKEN environment variable
"""

    tweet_url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    if len(text) > 280:
        return "❌ Tweet exceeds 280 characters."

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                tweet_url,
                json={"text": text},
                headers=headers
            ) as response:
                result = await response.json()
                if response.status == 201 and "data" in result:
                    return f"✅ Tweet posted. Tweet ID: {result['data']['id']}"
                else:
                    return f"❌ Failed to post tweet: {result}"
    except Exception as e:
        return f"❌ Error posting to Twitter: {str(e)}"


#@tool(name="post_to_facebook", description="Post open house announcement to Facebook page")
async def post_to_facebook(
    post_content: Annotated[str, "The content to post on Facebook"],
    page_id: Annotated[str, "Facebook page ID"] = None,
    access_token: Annotated[str, "Facebook page access token"] = None
) -> str:
    """
    Post open house announcement to Facebook page.
    Requires Facebook API configuration.
    """
    
    # Use environment variables if not provided
    if not page_id:
        page_id = FACEBOOK_PAGE_ID
    if not access_token:
        access_token = FACEBOOK_PAGE_ACCESS_TOKEN
    
    if not validate_facebook_config():
        return """
❌ **Facebook API Configuration Required**

To post automatically to Facebook, please set these environment variables:
- FACEBOOK_PAGE_ID: Your Facebook page ID
- FACEBOOK_PAGE_ACCESS_TOKEN: Your page access token

**Alternative:** Copy the post content and share manually on your Facebook page.

**Getting Facebook API Access:**
1. Go to Facebook Developers (developers.facebook.com)
2. Create an app and get page access token
3. Set the environment variables above
"""
    
    try:
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        payload = {
            "message": post_content,
            "access_token": access_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    post_id = result.get("id", "unknown")
                    return f"""
✅ **Facebook Post Successful**

🎉 Your open house announcement has been posted to Facebook!
📱 Post ID: {post_id}

The post is now live and visible to your page followers.
"""
                else:
                    error_text = await response.text()
                    return f"❌ Facebook posting failed: {error_text}"
                    
    except Exception as e:
        return f"❌ Error posting to Facebook: {str(e)}"


def generate_social_media_content(
    property_type: str,
    address: str,
    price: str,
    bedrooms: int,
    bathrooms: float,
    square_feet: int,
    special_features: str = "",
    platform: str = "general"
) -> str:
    """Generate platform-specific social media content for property listings."""
    
    if platform == "facebook":
        return f"""🏠 NEW LISTING ALERT! 🏠

📍 {address}
💰 {price}
🏡 {bedrooms} bedrooms | {bathrooms} bathrooms | {square_feet:,} sq ft

✨ {special_features if special_features else "Beautiful property with amazing features!"}

FSBO - Contact us directly for showings!

#NewListing #RealEstate #ForSale #DreamHome #FSBO
"""
    
    elif platform == "instagram":
        return f"""🏡✨ JUST LISTED ✨🏡

{address}
{price} • {bedrooms}BR • {bathrooms}BA • {square_feet:,}sqft

{special_features if special_features else "Your dream home awaits! 🌟"}

DM for details! 📩

#JustListed #RealEstate #FSBO #DreamHome #PropertyTour #ForSale #NewListing
"""
    
    elif platform == "twitter":
        content = f"""🏡 NEW: {address}
💰 {price}
🛏️ {bedrooms}BR | 🛁 {bathrooms}BA | 📐 {square_feet:,}sqft

{special_features[:50] + "..." if len(special_features) > 50 else special_features}

#RealEstate #FSBO #ForSale"""
        
        return content[:280]  # Twitter character limit
    
    else:  # general
        return f"""🏠 Beautiful {property_type} Available!

📍 Location: {address}
💰 Price: {price}
🏡 Details: {bedrooms} BR | {bathrooms} BA | {square_feet:,} sq ft

{special_features if special_features else "Don't miss this opportunity!"}

Contact us for more information and to schedule a showing.
"""