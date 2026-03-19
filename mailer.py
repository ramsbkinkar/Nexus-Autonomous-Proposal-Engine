import os
import smtplib
from email.message import EmailMessage
from icalendar import Calendar, Event
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def send_proposal_email(recipient_email, client_name, pdf_bytes):
    print(f"Preparing email and calendar invite for {client_name}...")
    
    # 1. Create the Calendar Event (.ics)
    cal = Calendar()
    event = Event()
    event.add('summary', f'Kickoff Meeting: {client_name} Project')
    # Set meeting for 2 days from right now
    event.add('dtstart', datetime.now() + timedelta(days=2)) 
    event.add('dtend', datetime.now() + timedelta(days=2, hours=1))
    event.add('description', 'Discussion regarding the approved technical proposal.')
    cal.add_component(event)
    
    ics_data = cal.to_ical()

    # 2. Setup the Email
    msg = EmailMessage()
    msg['Subject'] = f"🚀 Proposal Approved: {client_name} Transformation"
    msg['From'] = os.getenv("EMAIL_USER")
    msg['To'] = recipient_email
    msg.set_content(f"""
    Hello Team,
    
    The enterprise proposal for {client_name} has been officially approved by the Cloud Architect and Engagement Manager.
    
    Attached you will find:
    1. The Final Technical Proposal (PDF)
    2. A Calendar Invite for the project kickoff meeting.
    
    Best regards,
    Enterprise RFP Engine (Automated System)
    """)

    # 3. Add Attachments
    msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f"{client_name}_Proposal.pdf")
    msg.add_attachment(ics_data, maintype='text', subtype='calendar', filename="kickoff_meeting.ics")

    # 4. Send the Email via Gmail
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            smtp.send_message(msg)
        print("✅ Email and Calendar invite sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False