"""
Neighborhood market activity analysis tool.

Summarizes recent sales, new listings, and market velocity to help FSBO sellers understand local conditions.
"""

from typing import Annotated, List, Optional


# @tool(name="neighborhood_activity_tracker", description="Analyze recent market activity like sales, listings, and market speed in a ZIP code")
async def neighborhood_activity_tracker(
    zip_code: Annotated[str, "ZIP code of the neighborhood to analyze"],
    recent_sales: Annotated[List[str], "Recent home sales formatted like '$500,000 - 3bd/2ba - Sold 2024-05-10'"],
    new_listings: Annotated[List[str], "New listings formatted like '$525,000 - 4bd/3ba - Listed 2024-05-22'"],
    average_days_on_market: Annotated[Optional[float], "Average number of days homes are staying on market"] = None
) -> str:
    """
    Formats neighborhood activity data into a clean summary string for later AI summarization.
    """

    try:
        summary = f"""
📍 **Neighborhood Activity in {zip_code}**

- 🏠 Recent Sales: {len(recent_sales)}
- 🆕 New Listings: {len(new_listings)}
- ⏳ Avg. Days on Market: {average_days_on_market if average_days_on_market else 'N/A'}

**Recent Sales Examples:**
{chr(10).join(f'- {s}' for s in recent_sales[:3])}

**New Listings Examples:**
{chr(10).join(f'- {l}' for l in new_listings[:3])}
"""
        return summary.strip()

    except Exception as e:
        return f"❌ Error generating neighborhood summary: {str(e)}"
