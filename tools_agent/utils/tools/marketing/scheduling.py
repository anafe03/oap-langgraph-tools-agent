"""
Event scheduling and open house management tools.
"""
from typing import Annotated, Optional, List
from datetime import datetime
from urllib.parse import quote
from langchain_core.tools import tool
from ..common.utils import validate_date_format


#@tool(name="schedule_open_house", description="Schedule an open house event with options for email notifications, social media posting, and calendar integration")
async def schedule_open_house(
    property_address: Annotated[str, "The full address of the property for the open house"],
    date: Annotated[str, "Date of the open house (format: YYYY-MM-DD)"],
    start_time: Annotated[str, "Start time of the open house (format: HH:MM AM/PM)"],
    end_time: Annotated[str, "End time of the open house (format: HH:MM AM/PM)"],
    agent_name: Annotated[str, "Name of the listing agent"],
    agent_phone: Annotated[str, "Agent's phone number"],
    agent_email: Annotated[str, "Agent's email address"],
    property_price: Annotated[str, "Asking price of the property (e.g., '$450,000')"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Square footage of the property"],
    special_features: Annotated[str, "Special features or highlights of the property"] = "",
    parking_info: Annotated[str, "Parking information for visitors"] = "Street parking available",
    additional_notes: Annotated[str, "Any additional notes or instructions"] = "",
    send_to_prospects: Annotated[bool, "Whether to send email notifications to prospective buyers"] = True,
    post_to_facebook: Annotated[bool, "Whether to create a Facebook post"] = False,
    add_to_calendar: Annotated[bool, "Whether to generate Google Calendar integration"] = True,
    prospect_emails: Annotated[Optional[List[str]], "List of prospective buyer email addresses"] = None
) -> str:
    """
    Schedule an open house with comprehensive marketing and organization features.
    
    This tool creates:
    - Professional open house announcement
    - Email notifications to prospects
    - Social media post content
    - Google Calendar integration
    - Marketing materials
    """
    
    try:
        # Validate date format
        event_date = validate_date_format(date)
        if not event_date:
            return "❌ Invalid date format. Please use YYYY-MM-DD format."
        
        formatted_date = event_date.strftime("%A, %B %d, %Y")
        
        # Create the open house announcement
        announcement = f"""
🏠 **OPEN HOUSE SCHEDULED**

**📍 Property:** {property_address}
**📅 Date:** {formatted_date}
**🕐 Time:** {start_time} - {end_time}
**💰 Price:** {property_price}
**🏡 Details:** {bedrooms} BR | {bathrooms} BA | {square_feet:,} sq ft

**👤 Hosted by:** {agent_name}
**📞 Contact:** {agent_phone}
**📧 Email:** {agent_email}

**✨ Special Features:**
{special_features if special_features else "Beautiful property with many attractive features"}

**🚗 Parking:** {parking_info}

{f"**📝 Additional Information:** {additional_notes}" if additional_notes else ""}

We look forward to seeing you there! Please feel free to reach out with any questions.
"""
        
        result_summary = [announcement]
        result_summary.append("\n" + "="*50 + "\n")
        
        # Generate email content for prospects
        if send_to_prospects:
            email_subject = f"Open House: {property_address} - {formatted_date}"
            email_body = f"""
Dear Prospective Buyer,

You're invited to an exclusive open house viewing!

🏠 PROPERTY DETAILS:
Address: {property_address}
Price: {property_price}
Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Square Feet: {square_feet:,}

📅 OPEN HOUSE DETAILS:
Date: {formatted_date}
Time: {start_time} - {end_time}
Parking: {parking_info}

✨ HIGHLIGHTS:
{special_features if special_features else "This beautiful property offers many attractive features and is located in a desirable area."}

{f"IMPORTANT NOTES: {additional_notes}" if additional_notes else ""}

Please mark your calendar and join us for this exciting opportunity to view this exceptional property. No appointment necessary during open house hours.

For private showings or questions, please contact:
{agent_name}
📞 {agent_phone}
📧 {agent_email}

Best regards,
{agent_name}
Real Estate Professional

---
This email was sent because you expressed interest in properties in this area. If you no longer wish to receive these updates, please reply with "UNSUBSCRIBE".
"""
            
            result_summary.append("📧 **EMAIL NOTIFICATION READY**")
            result_summary.append(f"**Subject:** {email_subject}")
            result_summary.append("**Email Body Created:** ✅")
            
            if prospect_emails and len(prospect_emails) > 0:
                result_summary.append(f"**Recipients:** {len(prospect_emails)} prospects")
                result_summary.append("**Email Status:** Ready to send (requires SMTP configuration)")
            else:
                result_summary.append("**Recipients:** No prospect emails provided")
                result_summary.append("**Action Required:** Provide prospect email addresses to send notifications")
            
            result_summary.append(f"\n**Email Preview:**\n{email_body[:300]}...\n")
        
        # Generate Facebook post content
        if post_to_facebook:
            facebook_post = f"""🏠 OPEN HOUSE ALERT! 🏠

📍 {property_address}
📅 {formatted_date}
🕐 {start_time} - {end_time}
💰 {property_price}

🏡 {bedrooms} bedrooms | {bathrooms} bathrooms | {square_feet:,} sq ft

✨ {special_features if special_features else "Beautiful property with amazing features!"}

🚗 {parking_info}

Hosted by {agent_name} 📞 {agent_phone}

Don't miss this opportunity! See you there! 

#OpenHouse #RealEstate #ForSale #DreamHome #PropertyTour
{f"#{property_address.split(',')[-1].strip().replace(' ', '')}" if ',' in property_address else ""}
"""
            
            result_summary.append("\n📱 **FACEBOOK POST READY**")
            result_summary.append("**Post Content Created:** ✅")
            result_summary.append(f"\n**Facebook Post Preview:**\n{facebook_post}\n")
        
        # Generate Google Calendar integration
        if add_to_calendar:
            # Create Google Calendar URL for easy adding
            calendar_title = quote(f"Open House: {property_address}")
            calendar_details = quote(f"Open House at {property_address}\n\nProperty Details:\n- Price: {property_price}\n- {bedrooms} BR, {bathrooms} BA, {square_feet:,} sq ft\n\nHost: {agent_name}\nPhone: {agent_phone}\nEmail: {agent_email}\n\nFeatures: {special_features}\nParking: {parking_info}")
            calendar_location = quote(property_address)
            
            # Convert time to 24-hour format for URL (simplified)
            try:
                start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %I:%M %p")
                end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %I:%M %p")
                
                start_formatted = start_datetime.strftime("%Y%m%dT%H%M%S")
                end_formatted = end_datetime.strftime("%Y%m%dT%H%M%S")
                
                google_calendar_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={calendar_title}&dates={start_formatted}/{end_formatted}&details={calendar_details}&location={calendar_location}"
                
                result_summary.append("\n📅 **GOOGLE CALENDAR INTEGRATION**")
                result_summary.append("**Calendar Event:** Ready ✅")
                result_summary.append(f"**Quick Add URL:** {google_calendar_url[:100]}...")
                result_summary.append("**Action:** Click the URL above to add to your Google Calendar")
                
            except ValueError:
                result_summary.append("\n📅 **GOOGLE CALENDAR INTEGRATION**")
                result_summary.append("**Status:** Error parsing time format")
                result_summary.append("**Action Required:** Verify time format (HH:MM AM/PM)")
        
        # Generate summary and next steps
        result_summary.append("\n" + "="*50)
        result_summary.append("\n🎯 **NEXT STEPS:**")
        
        if send_to_prospects and prospect_emails:
            result_summary.append("1. ✅ Send email notifications to prospects")
        elif send_to_prospects:
            result_summary.append("1. 📝 Collect prospect email addresses and send notifications")
        
        if post_to_facebook:
            result_summary.append("2. 📱 Post to Facebook using the content above")
        
        if add_to_calendar:
            result_summary.append("3. 📅 Add event to your Google Calendar using the provided link")
        
        result_summary.append("4. 📋 Save this information for your records")
        result_summary.append("5. 🏠 Prepare the property for the open house")
        result_summary.append("6. 📧 Send reminder emails 1-2 days before the event")
        
        # Additional marketing suggestions
        result_summary.append("\n💡 **ADDITIONAL MARKETING IDEAS:**")
        result_summary.append("- Post on Instagram Stories with property photos")
        result_summary.append("- Add open house signs and directional signs")
        result_summary.append("- Update MLS listing with open house information")
        result_summary.append("- Notify neighbors about the open house")
        result_summary.append("- Prepare refreshments and informational materials")
        
        return "\n".join(result_summary)
        
    except Exception as e:
        return f"❌ Error scheduling open house: {str(e)}"


def generate_open_house_reminder(
    property_address: str,
    date: str,
    start_time: str,
    end_time: str,
    agent_name: str,
    agent_phone: str
) -> str:
    """Generate a reminder email/message for upcoming open house."""
    
    event_date = validate_date_format(date)
    if not event_date:
        formatted_date = date
    else:
        formatted_date = event_date.strftime("%A, %B %d, %Y")
    
    reminder = f"""
🏠 **OPEN HOUSE REMINDER** 🏠

Don't forget! Our open house is coming up soon:

📍 **Property:** {property_address}
📅 **Date:** {formatted_date}
🕐 **Time:** {start_time} - {end_time}

We're excited to show you this beautiful property!

**What to Expect:**
• Full property tour
• Information packets available
• Q&A with the listing agent
• No appointment necessary

**Questions?** Contact {agent_name} at {agent_phone}

See you there! 🎉

---
*This is a friendly reminder for the open house you expressed interest in.*
"""
    return reminder.strip()


def generate_open_house_follow_up(
    property_address: str,
    attendee_name: str,
    agent_name: str,
    agent_phone: str,
    agent_email: str,
    additional_info: str = ""
) -> str:
    """Generate a follow-up message after open house attendance."""
    
    follow_up = f"""
Hi {attendee_name},

Thank you for visiting our open house at {property_address}! It was great meeting you and showing you the property.

I hope you enjoyed the tour and got a good feel for what this beautiful home has to offer.

**Next Steps:**
• If you'd like to schedule a private showing, just let me know
• I'm happy to answer any additional questions you might have
• I can provide more detailed information about the neighborhood, schools, etc.
• If you're interested in making an offer, I can walk you through the process

{additional_info if additional_info else ""}

Please don't hesitate to reach out if you need anything at all. I'm here to help make your home buying journey as smooth as possible.

Best regards,
{agent_name}
📞 {agent_phone}
📧 {agent_email}

P.S. If you know anyone else who might be interested in this property, I'd appreciate you sharing our information with them!
"""
    return follow_up.strip()