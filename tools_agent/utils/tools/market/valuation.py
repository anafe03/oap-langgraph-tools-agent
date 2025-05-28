"""
Property valuation and CMA (Comparative Market Analysis) tools.
"""
import asyncio
from typing import Annotated
from datetime import datetime
from langchain_core.tools import tool
from ..common.utils import extract_price_from_text, calculate_price_per_sqft
from .research import _search_property_data


#@tool(name="generate_cma", description="Generate a comprehensive Comparative Market Analysis (CMA) report for a property")
async def generate_cma(
    address: Annotated[str, "The subject property address"],
    bedrooms: Annotated[int, "Number of bedrooms in the subject property"],
    bathrooms: Annotated[float, "Number of bathrooms in the subject property"],
    square_feet: Annotated[int, "Square footage of the subject property"],
    property_type: Annotated[str, "Type of property (e.g., Single Family, Condo, Townhouse)"] = "Single Family",
    radius_miles: Annotated[float, "Search radius in miles for comparable properties"] = 1.0
) -> str:
    """Generate a comprehensive CMA report with comparable sales, market trends, and pricing analysis."""
    
    try:
        # Extract location from address for searches
        location_parts = address.split(',')
        if len(location_parts) >= 2:
            city_state = ','.join(location_parts[-2:]).strip()
        else:
            city_state = address
        
        # Create search queries for different data types
        search_queries = [
            f"recently sold homes {city_state} {bedrooms} bedroom {bathrooms} bathroom {property_type}",
            f"home sales {city_state} {square_feet} square feet comparable properties",
            f"real estate market trends {city_state} 2024 home prices",
            f"active listings {city_state} {bedrooms}br {bathrooms}ba for sale"
        ]
        
        # Execute searches concurrently
        search_results = await asyncio.gather(
            *[_search_property_data(query, 8) for query in search_queries],
            return_exceptions=True
        )
        
        # Process results
        sold_properties = []
        active_listings = []
        market_trends = []
        
        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                continue
                
            for item in result.get("results", []):
                property_data = {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "price": extract_price_from_text(item.get("snippet", "")),
                    "source": item.get("url", "").split("//")[-1].split("/")[0]
                }
                
                # Categorize based on search query
                if i == 0 and ("sold" in item.get("snippet", "").lower() or "sale" in item.get("title", "").lower()):
                    sold_properties.append(property_data)
                elif i == 3 and ("for sale" in item.get("snippet", "").lower() or "listing" in item.get("snippet", "").lower()):
                    active_listings.append(property_data)
                elif i == 2:
                    market_trends.append(property_data)
        
        # Generate the CMA report
        current_date = datetime.now().strftime("%B %d, %Y")
        
        cma_report = f"""
# 🏠 COMPARATIVE MARKET ANALYSIS (CMA)

**Property Address:** {address}  
**Report Date:** {current_date}  
**Property Type:** {property_type}  
**Bedrooms:** {bedrooms} | **Bathrooms:** {bathrooms} | **Square Feet:** {square_feet:,}

---

## 📊 EXECUTIVE SUMMARY

This Comparative Market Analysis provides a comprehensive evaluation of the subject property's market value based on recent comparable sales, current market conditions, and active competition in the area.

**Search Parameters:**
- Property Type: {property_type}
- Bedrooms: {bedrooms}
- Bathrooms: {bathrooms}
- Square Footage: {square_feet:,}
- Search Radius: {radius_miles} miles

---

## 🏘️ RECENTLY SOLD COMPARABLES

"""
        
        if sold_properties:
            cma_report += "The following properties have sold recently in your area:\n\n"
            for i, prop in enumerate(sold_properties[:6], 1):
                price_per_sqft = calculate_price_per_sqft(prop["price"], square_feet)
                cma_report += f"**{i}. {prop['title']}**\n"
                cma_report += f"   💰 **Price:** {prop['price']}\n"
                cma_report += f"   📐 **Price/SqFt:** {price_per_sqft}\n"
                cma_report += f"   🔗 **Source:** {prop['source']}\n"
                cma_report += f"   📝 **Details:** {prop['snippet'][:200]}...\n"
                cma_report += f"   🌐 **Link:** {prop['url']}\n\n"
        else:
            cma_report += "No recent comparable sales found in the immediate area. Consider expanding the search radius.\n\n"
        
        cma_report += "---\n\n## 🏪 ACTIVE COMPETITION\n\n"
        
        if active_listings:
            cma_report += "Current properties for sale in your area:\n\n"
            for i, prop in enumerate(active_listings[:6], 1):
                price_per_sqft = calculate_price_per_sqft(prop["price"], square_feet)
                cma_report += f"**{i}. {prop['title']}**\n"
                cma_report += f"   💰 **Asking Price:** {prop['price']}\n"
                cma_report += f"   📐 **Price/SqFt:** {price_per_sqft}\n"
                cma_report += f"   🔗 **Source:** {prop['source']}\n"
                cma_report += f"   📝 **Details:** {prop['snippet'][:200]}...\n"
                cma_report += f"   🌐 **Link:** {prop['url']}\n\n"
        else:
            cma_report += "Limited active listings found in the immediate area.\n\n"
        
        cma_report += "---\n\n## 📈 MARKET TRENDS\n\n"
        
        if market_trends:
            cma_report += "Current market conditions and trends:\n\n"
            for i, trend in enumerate(market_trends[:4], 1):
                cma_report += f"**{i}. {trend['title']}**\n"
                cma_report += f"   📊 **Insight:** {trend['snippet'][:250]}...\n"
                cma_report += f"   🔗 **Source:** {trend['source']}\n"
                cma_report += f"   🌐 **Link:** {trend['url']}\n\n"
        else:
            cma_report += "Market trend data not available for this specific area.\n\n"
        
        # Add pricing recommendations
        cma_report += """---

## 💡 PRICING RECOMMENDATIONS

Based on the comparative analysis above, consider the following pricing strategies:

### 📋 **Pricing Strategy Options:**

1. **🎯 Competitive Pricing:** Price at or slightly below comparable sold properties to attract quick offers
2. **📈 Market Rate Pricing:** Price in line with current market averages for similar properties
3. **💰 Premium Pricing:** Price above market if your property has unique features or superior condition

### 🔍 **Key Considerations:**
- **Days on Market:** How long similar properties are taking to sell
- **Price Reductions:** Whether comparable properties had to reduce their asking prices
- **Market Conditions:** Current buyer demand and inventory levels
- **Property Condition:** Your home's condition relative to the comparables
- **Unique Features:** Special amenities or upgrades that add value

---

## ⚠️ IMPORTANT DISCLAIMERS

- This CMA is for informational purposes and should not replace a professional appraisal
- Property values can fluctuate based on market conditions, property condition, and other factors
- Consult with a licensed real estate professional for official valuation guidance
- Data accuracy depends on available public information and listing sources

---

## 📞 NEXT STEPS

1. **Review Comparables:** Visit or drive by comparable properties when possible
2. **Professional Consultation:** Consider hiring a licensed appraiser for official valuation
3. **Market Timing:** Monitor market conditions and adjust pricing strategy accordingly
4. **Property Preparation:** Ensure your home is in optimal condition for sale

*Report generated on {current_date}*
"""
        
        return cma_report.strip()
        
    except Exception as e:
        return f"❌ Error generating CMA report: {str(e)}"


#@tool(name="quick_property_valuation", description="Get a quick property value estimate based on comparable sales")
async def quick_property_valuation(
    address: Annotated[str, "The property address to value"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Square footage of the property"]
) -> str:
    """Get a quick property valuation based on recent sales data."""
    
    try:
        # Extract location for search
        location_parts = address.split(',')
        if len(location_parts) >= 2:
            city_state = ','.join(location_parts[-2:]).strip()
        else:
            city_state = address
        
        # Search for recent sales
        query = f"recently sold homes {city_state} {bedrooms} bedroom {bathrooms} bathroom {square_feet} square feet"
        search_result = await _search_property_data(query, 5)
        
        valuation_text = f"🏠 **Quick Valuation for {address}**\n\n"
        valuation_text += f"**Property Details:** {bedrooms}BR | {bathrooms}BA | {square_feet:,} sq ft\n\n"
        
        if search_result.get("results"):
            valuation_text += "**📊 Based on Recent Comparable Sales:**\n\n"
            
            for i, result in enumerate(search_result["results"][:5], 1):
                price = extract_price_from_text(result.get("snippet", ""))
                price_per_sqft = calculate_price_per_sqft(price, square_feet)
                
                valuation_text += f"{i}. **{result.get('title', 'Property')}**\n"
                valuation_text += f"   💰 {price} | {price_per_sqft}\n"
                valuation_text += f"   📝 {result.get('snippet', '')[:150]}...\n\n"
            
            valuation_text += f"**💡 Estimated Value Range:** Based on comparable sales, your property may be valued between the range of prices shown above.\n\n"
            valuation_text += f"**⚠️ Note:** This is a preliminary estimate. For accurate valuation, order a professional appraisal or detailed CMA report."
        
        else:
            valuation_text += "❌ No recent comparable sales found. Try expanding your search area or use the full CMA tool for more comprehensive analysis."
        
        return valuation_text
        
    except Exception as e:
        return f"❌ Error generating property valuation: {str(e)}"