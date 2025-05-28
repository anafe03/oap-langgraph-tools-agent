"""
Photography and image processing tools for real estate listings.
"""
import httpx
from typing import Annotated
from langchain_core.tools import tool
from ..common.config import AZURE_ENDPOINT, AZURE_KEY, validate_azure_config


#@tool(name="generate_caption_from_image", description="Generate a natural language caption for a property image using AI")
async def generate_caption_from_image(
    image_url: Annotated[str, "URL of the image to generate caption for"]
) -> str:
    """Generate a natural language caption for an image using Azure Computer Vision API."""
    
    if not validate_azure_config():
        return """
❌ **Azure Computer Vision Configuration Required**

To generate image captions automatically, please set these environment variables:
- AZURE_CV_ENDPOINT: Your Azure Computer Vision endpoint URL
- AZURE_CV_KEY: Your Azure Computer Vision API key

**Alternative:** Manually write captions for your property photos.

**Getting Azure Computer Vision:**
1. Go to Azure Portal (portal.azure.com)
2. Create a Computer Vision resource
3. Get the endpoint URL and API key
4. Set the environment variables above
"""
    
    endpoint = f"{AZURE_ENDPOINT}/vision/v3.2/describe"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/json",
    }
    data = {"url": image_url}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, headers=headers, json=data, timeout=20)
            response.raise_for_status()
            result = response.json()
            
            # The API returns a list of captions, pick the first and its confidence
            caption = result.get("description", {}).get("captions", [{}])[0]
            text = caption.get("text", "")
            confidence = caption.get("confidence", 0)
            
            if text:
                return f"Caption: {text} (confidence: {confidence:.2f})"
            else:
                return "No caption generated."
                
    except Exception as e:
        return f"❌ Error generating caption: {str(e)}"


def generate_property_photo_descriptions():
    """Generate template descriptions for different types of property photos."""
    
    descriptions = {
        "exterior_front": [
            "Stunning curb appeal with well-maintained landscaping",
            "Beautiful front facade showcasing architectural details",
            "Welcoming entrance with attractive exterior features",
            "Impressive street view highlighting the home's character"
        ],
        
        "living_room": [
            "Spacious living area perfect for entertaining",
            "Bright and airy living room with natural light",
            "Cozy living space with modern updates",
            "Open concept living area with beautiful finishes"
        ],
        
        "kitchen": [
            "Gourmet kitchen with premium appliances and finishes",
            "Modern kitchen featuring ample counter and storage space",
            "Chef's dream kitchen with high-end amenities",
            "Updated kitchen perfect for cooking and entertaining"
        ],
        
        "bedroom": [
            "Peaceful bedroom retreat with generous closet space",
            "Comfortable bedroom with excellent natural lighting",
            "Spacious bedroom offering privacy and relaxation",
            "Master suite featuring elegant design elements"
        ],
        
        "bathroom": [
            "Luxurious bathroom with modern fixtures and finishes",
            "Spa-like bathroom retreat with premium amenities",
            "Updated bathroom featuring contemporary design",
            "Beautiful bathroom with attention to detail"
        ],
        
        "backyard": [
            "Private backyard oasis perfect for outdoor living",
            "Beautifully landscaped outdoor space for entertaining",
            "Serene backyard retreat with mature landscaping",
            "Spacious yard offering endless possibilities"
        ],
        
        "dining_room": [
            "Elegant dining space perfect for family gatherings",
            "Formal dining room with sophisticated charm",
            "Open dining area connecting to living spaces",
            "Beautiful dining room for memorable meals"
        ]
    }
    
    return descriptions


def generate_photo_shoot_checklist():
    """Generate a comprehensive checklist for property photo shoots."""
    
    checklist = """
📸 **PROPERTY PHOTO SHOOT CHECKLIST**

## 🏠 **EXTERIOR SHOTS**
□ Front view (straight on and angled)
□ Side views (both sides if accessible)
□ Backyard/outdoor living spaces
□ Landscaping and garden features
□ Driveway and parking areas
□ Pool/spa (if applicable)
□ Outdoor amenities (deck, patio, etc.)

## 🏡 **INTERIOR SHOTS**
□ Entryway/foyer
□ Living room (multiple angles)
□ Kitchen (overview and detail shots)
□ Dining room/eating areas
□ All bedrooms
□ All bathrooms
□ Family room/den
□ Home office/study
□ Basement/bonus rooms
□ Laundry room
□ Walk-in closets
□ Staircase (if notable)

## 💡 **PREPARATION TIPS**
□ Turn on all lights
□ Open all blinds/curtains
□ Remove personal items and clutter
□ Make all beds
□ Clean all surfaces
□ Arrange furniture for best angles
□ Add fresh flowers/plants if needed
□ Turn off ceiling fans
□ Hide trash cans and pet items
□ Set air conditioning to comfortable temp

## 📱 **SPECIAL SHOTS**
□ Unique architectural features
□ Built-in storage solutions
□ High-end appliances and fixtures
□ Views from windows
□ Outdoor entertaining areas
□ Garage/storage spaces
□ Neighborhood/street view

## 🎯 **POST-SHOOT**
□ Review all photos immediately
□ Retake any unclear/dark shots
□ Ensure each room has at least 2-3 angles
□ Capture both wide and detail shots
□ Edit for optimal lighting/color
□ Organize by room for easy use
"""
    
    return checklist.strip()


def generate_photo_marketing_tips():
    """Generate tips for using photos effectively in marketing."""
    
    tips = """
📸 **PHOTO MARKETING BEST PRACTICES**

## 🌟 **PHOTO SELECTION**
• Lead with your strongest exterior shot
• Use the best kitchen photo early in the sequence
• Show the most impressive room first
• Include at least 15-25 total photos
• Mix wide shots with detail photos

## 📱 **SOCIAL MEDIA OPTIMIZATION**
• Square crops work best for Instagram
• Bright, well-lit photos perform better
• Add property details as text overlay
• Use consistent filters/editing style
• Create photo carousels for engagement

## 🏠 **LISTING PLATFORMS**
• First photo is crucial - make it count
• Include floor plan if available
• Show progression through the home
• Highlight unique selling points
• End with exterior/neighborhood shots

## ✨ **ENHANCEMENT IDEAS**
• Virtual staging for empty rooms
• Twilight shots for dramatic effect
• Drone photography for large properties
• 360-degree virtual tours
• Before/after renovation photos

## 📊 **PERFORMANCE TRACKING**
• Monitor which photos get most views
• A/B test different lead photos
• Track engagement rates by photo type
• Update photos if listing stalls
• Seasonal updates for outdoor spaces
"""
    
    return tips.strip()


def suggest_photo_improvements(photo_issues: str) -> str:
    """Suggest improvements based on common photo issues."""
    
    improvements = {
        "dark": "• Increase natural light by opening blinds/curtains\n• Turn on all room lights\n• Consider additional lighting equipment\n• Shoot during peak daylight hours\n• Use HDR photography techniques",
        
        "cluttered": "• Remove personal items and excess decor\n• Clear all countertops and surfaces\n• Hide cables and electronic devices\n• Organize closets and storage areas\n• Stage with minimal, neutral decor",
        
        "blurry": "• Use a tripod for stability\n• Check camera settings and focus\n• Ensure adequate lighting\n• Use faster shutter speeds\n• Take multiple shots of each angle",
        
        "poor_angles": "• Shoot from corner to corner for wide views\n• Keep camera level (use grid lines)\n• Include more ceiling in vertical shots\n• Show room flow and connections\n• Capture unique architectural features",
        
        "color_issues": "• Adjust white balance for accurate colors\n• Edit photos for consistent tone\n• Avoid mixed lighting sources\n• Use natural light when possible\n• Consider professional editing software"
    }
    
    suggestions = []
    issues = photo_issues.lower()
    
    for issue, solution in improvements.items():
        if issue in issues:
            suggestions.append(f"**{issue.replace('_', ' ').title()} Issues:**\n{solution}")
    
    if not suggestions:
        suggestions.append("**General Improvements:**\n• Focus on lighting and decluttering\n• Ensure all photos are sharp and well-composed\n• Show the property's best features prominently\n• Maintain consistent editing style")
    
    return "\n\n".join(suggestions)