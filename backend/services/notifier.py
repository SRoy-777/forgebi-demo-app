import os
import requests

def send_admin_email_alert(subject, html_content):
    """
    Sends an email notification to the administrator (mis@forgebi.in) via Resend.
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("Error: RESEND_API_KEY environment variable is not set.")
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": "ForgeBI Security <alerts@forgebi.in>",
        "to": "mis@forgebi.in",
        "subject": subject,
        "html": html_content
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            print("Email alert sent successfully via Resend.")
            return True
        else:
            print(f"Failed to send email alert via Resend. Code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error calling Resend API: {e}")
        return False
