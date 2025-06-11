"""
Real Estate Tools Package - Main imports and tool registry.
Located at: tools_agent/utils/tools/__init__.py
"""

# Listing tools
from .listing.creation import make_listing,  insert_listing

# Market research and valuation tools
from .market.research import market_trends
from .market.valuation import generate_cma, quick_property_valuation

# Professional finder tools
from .professionals.finders import (
    find_real_estate_attorney,
    find_real_estate_photographer,
    find_title_company,
    find_mortgage_lender,
    find_home_inspector,
    find_appraiser
)

# Marketing and social media tools
from .marketing.social_media import (
    generate_property_listing_tweet,
    post_to_twitter,
    post_to_facebook
)
from .marketing.scheduling import schedule_open_house

# Communication tools
from .communications.email import send_open_house_emails

# Media processing tools
from .media.photography import generate_caption_from_image

# Integration tools
from .integrations.rag import create_rag_tool, wrap_mcp_authenticate_tool

# Common utilities - these are imported by other modules but also available here
from .common.config import *
from .common.utils import *

# Tool categories for easy organization
LISTING_TOOLS = [
    make_listing,
    insert_listing
]

MARKET_TOOLS = [
    market_trends,
    generate_cma,
    quick_property_valuation
]

PROFESSIONAL_TOOLS = [
    find_real_estate_attorney,
    find_real_estate_photographer,
    find_title_company,
    find_mortgage_lender,
    find_home_inspector,
    find_appraiser
]

MARKETING_TOOLS = [
    generate_property_listing_tweet,
    post_to_twitter,
    post_to_facebook,
    schedule_open_house
]

COMMUNICATION_TOOLS = [
    send_open_house_emails
]

MEDIA_TOOLS = [
    generate_caption_from_image
]

# All tools combined for easy import
ALL_TOOLS = (
    LISTING_TOOLS +
    MARKET_TOOLS +
    PROFESSIONAL_TOOLS +
    MARKETING_TOOLS +
    COMMUNICATION_TOOLS +
    MEDIA_TOOLS
)

# Tool registry by category
TOOL_REGISTRY = {
    "listing": LISTING_TOOLS,
    "market": MARKET_TOOLS,
    "professionals": PROFESSIONAL_TOOLS,
    "marketing": MARKETING_TOOLS,
    "communications": COMMUNICATION_TOOLS,
    "media": MEDIA_TOOLS,
    "all": ALL_TOOLS
}

def get_tools_by_category(category: str = "all"):
    """Get tools by category name."""
    return TOOL_REGISTRY.get(category, ALL_TOOLS)

def get_tool_names():
    """Get list of all tool names."""
    return [tool.name for tool in ALL_TOOLS]

def get_tools_summary():
    """Get a summary of all available tools organized by category."""
    summary = {}
    for category, tools in TOOL_REGISTRY.items():
        if category != "all":
            summary[category] = {
                "count": len(tools),
                "tools": [{"name": tool.name, "description": tool.description} for tool in tools]
            }
    return summary