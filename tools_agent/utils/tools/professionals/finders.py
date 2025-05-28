"""
Professional service finder tools for real estate transactions.
"""
import aiohttp
from typing import Annotated, Dict, List
from langchain_core.tools import tool, ToolException
from ..common.config import TAVILY_API_KEY, validate_tavily_api
from ..common.utils import (
    extract_business_name, extract_phone, extract_address, extract_rating, 
    format_professional_card
)


async def _search_professionals(
    profession: str, 
    location: str, 
    additional_keywords: str = "",
    max_results: int = 8
) -> Dict:
    """Enhanced search for real estate professionals with better filtering."""
    validate_tavily_api()
    
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # More specific query to get actual business listings
    query = f'"{profession}" "{location}" contact phone address reviews -"search" -"find" -"best of"'
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_domains": [
            "yelp.com", "google.com", "yellowpages.com", "bbb.org", 
            "thumbtack.com", "angieslist.com", "homeadvisor.com",
            "facebook.com", "linkedin.com", "avvo.com"
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise ToolException(f"Search failed: {error_message}")
                
                data = await response.json()
                results = []
                
                for item in data.get("results", []):
                    # Filter out generic search pages
                    title = item.get("title", "")
                    url_str = item.get("url", "")
                    snippet = item.get("snippet", "")
                    
                    # Skip if it's a search results page
                    if any(word in title.lower() for word in ["search", "find", "best of", "top 10"]):
                        continue
                    if "search?" in url_str or "/search" in url_str:
                        continue
                    
                    # Extract business information
                    business_name = extract_business_name(title, snippet)
                    phone = extract_phone(snippet)
                    address = extract_address(snippet)
                    rating = extract_rating(snippet)
                    
                    if business_name and business_name != "Unknown Business":
                        result = {
                            "name": business_name,
                            "address": address,
                            "phone": phone,
                            "rating": rating,
                            "url": url_str,
                            "snippet": snippet,
                            "domain": url_str.split("//")[-1].split("/")[0] if url_str else ""
                        }
                        results.append(result)
                
                return {
                    "location": location,
                    "profession": profession,
                    "results": results[:6],  # Limit to top 6 results
                    "total_found": len(results)
                }
                
    except Exception as e:
        raise ToolException(f"Search error: {str(e)}")


def _format_chatbot_response(title: str, location: str, results: List[Dict], tips: List[str]) -> str:
    """Format response for chatbot with clean professional cards."""
    
    if not results:
        return f"""
❌ **No {title} Found**

I couldn't find specific {title.lower()} in {location}. 

**Try:**
• Expanding search to nearby cities
• Contacting local real estate offices for referrals
• Checking with your state's licensing board

Need help with something else? 😊
"""
    
    response = f"""
🎯 **{title} in {location}**

Found {len(results)} qualified professionals:

"""
    
    # Add each professional card
    for i, result in enumerate(results, 1):
        response += format_professional_card(result, i)
    
    # Add tips section
    if tips:
        response += "\n💡 **Quick Tips:**\n"
        for tip in tips[:3]:
            response += f"• {tip}\n"
    
    response += "\n💬 **Need more help?** Just ask!"
    
    return response


#@tool(name="find_real_estate_attorney", description="Find local real estate attorneys for legal assistance with property transactions")
async def find_real_estate_attorney(location: Annotated[str, "City and state to search for attorneys"]) -> str:
    """Find local real estate attorneys for legal assistance with property transactions."""
    try:
        data = await _search_professionals(
            "real estate attorney lawyer", 
            location, 
            "property law closing contract residential"
        )
        
        tips = [
            "Verify they're licensed in your state",
            "Ask about FSBO transaction experience", 
            "Get fee quotes upfront",
            "Check their availability for your timeline"
        ]
        
        return _format_chatbot_response(
            "Real Estate Attorneys", 
            location, 
            data["results"], 
            tips
        )
        
    except Exception as e:
        return f"❌ **Search Error**\n\nHad trouble finding attorneys in {location}.\nPlease try again or contact me for manual assistance."


#@tool(name="find_real_estate_photographer", description="Find local real estate photographers for property listing photos")
async def find_real_estate_photographer(location: Annotated[str, "City and state to search for photographers"]) -> str:
    """Find local real estate photographers for property listing photos."""
    try:
        data = await _search_professionals(
            "real estate photographer photography", 
            location, 
            "property listing photos drone aerial"
        )
        
        tips = [
            "Request portfolio samples before booking",
            "Ask about drone/aerial photography", 
            "Confirm 24-48 hour turnaround time",
            "Get pricing for different packages"
        ]
        
        return _format_chatbot_response(
            "Real Estate Photographers", 
            location, 
            data["results"], 
            tips
        )
        
    except Exception as e:
        return f"❌ **Search Error**\n\nHad trouble finding photographers in {location}.\nPlease try again or contact me for manual assistance."


#@tool(name="find_title_company", description="Find local title companies and escrow services")
async def find_title_company(location: Annotated[str, "City and state to search for title companies"]) -> str:
    """Find local title companies and escrow services."""
    try:
        data = await _search_professionals(
            "title company escrow", 
            location, 
            "real estate closing settlement insurance"
        )
        
        tips = [
            "Compare closing costs upfront",
            "Ask about average time to close", 
            "Verify they handle FSBO transactions",
            "Check if they provide title insurance"
        ]
        
        return _format_chatbot_response(
            "Title Companies", 
            location, 
            data["results"], 
            tips
        )
        
    except Exception as e:
        return f"❌ **Search Error**\n\nHad trouble finding title companies in {location}.\nPlease try again or contact me for manual assistance."


#@tool(name="find_mortgage_lender", description="Find local mortgage lenders and banks")
async def find_mortgage_lender(location: Annotated[str, "City and state to search for lenders"]) -> str:
    """Find local mortgage lenders and banks."""
    try:
        data = await _search_professionals(
            "mortgage lender bank", 
            location, 
            "home loan residential financing"
        )
        
        tips = [
            "Shop rates from multiple lenders",
            "Get pre-approval for serious buyers", 
            "Compare total closing costs",
            "Ask about first-time buyer programs"
        ]
        
        return _format_chatbot_response(
            "Mortgage Lenders", 
            location, 
            data["results"], 
            tips
        )
        
    except Exception as e:
        return f"❌ **Search Error**\n\nHad trouble finding lenders in {location}.\nPlease try again or contact me for manual assistance."


#@tool(name="find_home_inspector", description="Find local certified home inspectors")
async def find_home_inspector(location: Annotated[str, "City and state to search for inspectors"]) -> str:
    """Find local certified home inspectors."""
    try:
        data = await _search_professionals(
            "home inspector inspection", 
            location, 
            "certified property structural mechanical"
        )
        
        tips = [
            "Verify certifications (ASHI/InterNACHI)",
            "Ask for sample inspection reports", 
            "Get quotes including all systems",
            "Check availability for your timeline"
        ]
        
        return _format_chatbot_response(
            "Home Inspectors", 
            location, 
            data["results"], 
            tips
        )
        
    except Exception as e:
        return f"❌ **Search Error**\n\nHad trouble finding inspectors in {location}.\nPlease try again or contact me for manual assistance."


#@tool(name="find_appraiser", description="Find local certified real estate appraisers")
async def find_appraiser(location: Annotated[str, "City and state to search for appraisers"]) -> str:
    """Find local certified real estate appraisers."""
    try:
        data = await _search_professionals(
            "real estate appraiser", 
            location, 
            "certified residential property valuation"
        )
        
        tips = [
            "Verify state licensing/certification",
            "Ask about local market experience", 
            "Get timeline for completion",
            "Understand different appraisal types"
        ]
        
        return _format_chatbot_response(
            "Real Estate Appraisers", 
            location, 
            data["results"], 
            tips
        )
        
    except Exception as e:
        return f"❌ **Search Error**\n\nHad trouble finding appraisers in {location}.\nPlease try again or contact me for manual assistance."