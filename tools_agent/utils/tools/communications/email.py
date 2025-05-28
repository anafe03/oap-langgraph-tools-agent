"""
Email communication tools for real estate marketing and notifications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Annotated, List
from langchain_core.tools import tool
from ..common.config import (
    SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD,
    validate_email_config
)


#@tool(name="send_open_house_emails", description="Send open house email notifications to a list of prospects")
async def send_open_house_emails(
    subject: Annotated[str, "Email subject line"],
    body: Annotated[str, "Email body content"],
    recipient_emails: Annotated[List[str], "List of recipient email addresses"],
    sender_name: Annotated[str, "Name of the sender (agent)"],
    sender_email: Annotated[str, "Sender's email address"]
) -> str:
    """
    Send open house email notifications to prospective buyers.
    Requires SMTP configuration in environment variables.
    """
    
    if not validate_email_config():
        return """
❌ **Email Configuration Required**

To send emails automatically, please set these environment variables:
- EMAIL_USER: Your email address
- EMAIL_PASSWORD: Your email app password
- SMTP_SERVER: Your SMTP server (default: smtp.gmail.com)
- SMTP_PORT: Your SMTP port (default: 587)

**Alternative:** Copy the email content and send manually through your email client.
"""
    
    try:
        sent_count = 0
        failed_count = 0
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        for recipient in recipient_emails:
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = f"{sender_name} <{EMAIL_USER}>"
                msg['To'] = recipient
                msg['Subject'] = subject
                
                # Add body
                msg.attach(MIMEText(body, 'plain'))
                
                # Send email
                server.send_message(msg)
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {recipient}: {str(e)}")
        
        server.quit()
        
        return f"""
✅ **Email Sending Complete**

📧 **Results:**
- Successfully sent: {sent_count} emails
- Failed to send: {failed_count} emails
- Total recipients: {len(recipient_emails)}

The open house notifications have been delivered to your prospects!
"""
        
    except Exception as e:
        return f"❌ Error sending emails: {str(e)}"


def generate_buyer_inquiry_response(
    buyer_name: str,
    property_address: str,
    agent_name: str,
    agent_phone: str,
    agent_email: str,
    inquiry_type: str = "general",
    specific_questions: str = ""
) -> str:
    """Generate a professional response to buyer inquiries."""
    
    response_templates = {
        "showing": f"""
Hi {buyer_name},

Thank you for your interest in the property at {property_address}!

I'd be happy to schedule a private showing for you. I have availability:
• Weekdays: 9 AM - 6 PM
• Weekends: 10 AM - 5 PM
• Evenings by appointment

Please let me know what times work best for you, and I'll confirm our appointment.

The property offers many wonderful features, and I'm excited to show it to you in person. During the showing, you'll have plenty of time to explore every room and ask any questions.

Best regards,
{agent_name}
📞 {agent_phone}
📧 {agent_email}
""",
        
        "pricing": f"""
Hi {buyer_name},

Thank you for your interest in {property_address}!

The current asking price is competitive with similar properties in the area. I'd be happy to provide you with:
• Detailed pricing information
• Recent comparable sales data
• Market analysis for the neighborhood
• Information about any recent price adjustments

I can also discuss flexible terms and answer any questions about financing options.

Would you like to schedule a time to discuss this further? I'm available for a phone call or in-person meeting at your convenience.

Best regards,
{agent_name}
📞 {agent_phone}
📧 {agent_email}
""",
        
        "general": f"""
Hi {buyer_name},

Thank you for your inquiry about the property at {property_address}!

I'm excited to help you learn more about this wonderful home. Here's what I can provide:
• Detailed property information and photos
• Neighborhood and school district information
• Recent market activity in the area
• Flexible showing schedule
• Answers to any specific questions you have

{f"Regarding your specific questions: {specific_questions}" if specific_questions else ""}

I'm here to make your home buying process as smooth and informative as possible. Please don't hesitate to reach out with any questions, no matter how small.

Would you like to schedule a showing or phone consultation?

Best regards,
{agent_name}
📞 {agent_phone}
📧 {agent_email}
"""
    }
    
    return response_templates.get(inquiry_type, response_templates["general"]).strip()


def generate_listing_update_email(
    property_address: str,
    update_type: str,
    details: str,
    agent_name: str,
    agent_contact: str
) -> str:
    """Generate email notifications for listing updates."""
    
    update_templates = {
        "price_reduction": f"""
🏠 **PRICE REDUCTION ALERT** 🏠

Great news! The asking price for {property_address} has been reduced.

**Updated Details:**
{details}

This is an excellent opportunity to make this beautiful property yours at an even better value!

Don't wait - properties with price reductions often generate increased interest and move quickly.

**Ready to take the next step?**
• Schedule a private showing
• Request additional information
• Discuss making an offer

Contact me today!

{agent_name}
{agent_contact}
""",
        
        "status_change": f"""
📢 **LISTING STATUS UPDATE** 📢

{property_address}

**Status Update:**
{details}

Thank you for your continued interest in this property. I wanted to keep you informed of any changes that might affect your decision-making process.

If you have any questions or would like to discuss next steps, please don't hesitate to reach out.

{agent_name}
{agent_contact}
""",
        
        "new_photos": f"""
📸 **NEW PHOTOS AVAILABLE** 📸

We've just added beautiful new photos of {property_address} to the listing!

**What's New:**
{details}

These updated photos showcase the property's best features and give you an even better sense of what this home has to offer.

Check them out and let me know if you'd like to schedule a showing to see everything in person!

{agent_name}
{agent_contact}
""",
        
        "open_house": f"""
🏠 **OPEN HOUSE ANNOUNCED** 🏠

You expressed interest in {property_address}, and I'm excited to let you know we're hosting an open house!

**Open House Details:**
{details}

This is a perfect opportunity to tour the property at your convenience - no appointment necessary!

I look forward to seeing you there and answering any questions you might have.

{agent_name}
{agent_contact}
"""
    }
    
    return update_templates.get(update_type, f"""
📬 **LISTING UPDATE** 📬

{property_address}

{details}

Thank you for your interest in this property. Please let me know if you have any questions!

{agent_name}
{agent_contact}
""").strip()


def generate_welcome_email(
    buyer_name: str,
    agent_name: str,
    agent_phone: str,
    agent_email: str,
    specialties: str = "residential real estate"
) -> str:
    """Generate a welcome email for new prospects."""
    
    welcome = f"""
Hi {buyer_name},

Welcome, and thank you for your interest in working with me for your real estate needs!

**A Little About Me:**
I specialize in {specialties} and am committed to making your home buying experience as smooth and successful as possible. My goal is to be your trusted advisor throughout this important journey.

**What You Can Expect:**
• Prompt responses to all your questions
• Honest, professional guidance
• Flexible scheduling for showings
• Market insights and expert advice
• Support from search to closing

**Getting Started:**
I'd love to learn more about what you're looking for in a home. Are you available for a brief conversation this week? We can discuss:
• Your timeline and budget
• Neighborhood preferences
• Must-have features
• Any questions about the buying process

**Ready When You Are:**
There's no pressure - we'll move at your pace. I'm here to provide information and support whenever you need it.

Looking forward to working with you!

Best regards,
{agent_name}
📞 {agent_phone}
📧 {agent_email}

P.S. Feel free to save my contact information in your phone. I'm always available to help!
"""
    return welcome.strip()