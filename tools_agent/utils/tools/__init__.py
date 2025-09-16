# tools_agent/utils/tools/__init__.py

from .common import *
from .communications import *
from .finance_legal import *
from .integrations import *

# Import the listing tools with correct names
from .listing.creation import create_property_listing, update_property_listing, get_my_listings

# Import market tools
from .market import neighborhood_activity_tracker, market_trends

# Import marketing tools
from .marketing import *

# Import media tools  
from .media import *

# Import predictive tools
from .predictive import *

# Import professional finder tools
from .professionals import *

# Import valuation tools (assuming these exist in appropriate modules)
# You may need to adjust these imports based on your actual file structure
try:
    from .valuation import generate_cma, quick_property_valuation
except ImportError:
    # If valuation tools are in a different module, adjust accordingly
    from .market import generate_cma, quick_property_valuation

# Import professional finder tools (adjust module names as needed)
try:
    from .professionals import (
        find_mortgage_lender,
        find_real_estate_attorney, 
        find_title_company,
        find_appraiser,
        find_real_estate_photographer,
        find_home_inspector
    )
except ImportError:
    # Define placeholder functions if they don't exist yet
    def find_mortgage_lender(): pass
    def find_real_estate_attorney(): pass
    def find_title_company(): pass
    def find_appraiser(): pass
    def find_real_estate_photographer(): pass
    def find_home_inspector(): pass

# Import scheduling and social media tools
try:
    from .scheduling import schedule_open_house
    from .social import (
        post_to_facebook,
        send_open_house_emails,
        generate_property_listing_tweet,
        post_to_twitter
    )
except ImportError:
    # Define placeholder functions if they don't exist yet
    def schedule_open_house(): pass
    def post_to_facebook(): pass
    def send_open_house_emails(): pass
    def generate_property_listing_tweet(): pass
    def post_to_twitter(): pass

# Export all the tools
__all__ = [
    # Listing tools
    "create_property_listing", 
    "update_property_listing",
    "get_my_listings",
    
    # Market tools
    "market_trends",
    "neighborhood_activity_tracker",
    
    # Valuation tools
    "generate_cma",
    "quick_property_valuation",
    
    # Professional finder tools
    "find_mortgage_lender",
    "find_real_estate_attorney",
    "find_title_company", 
    "find_appraiser",
    "find_real_estate_photographer",
    "find_home_inspector",
    
    # Marketing and scheduling tools
    "schedule_open_house",
    "post_to_facebook",
    "send_open_house_emails", 
    "generate_property_listing_tweet",
    "post_to_twitter",
    
    # Legacy exports (if they exist)
    "LISTING_TOOLS",
]