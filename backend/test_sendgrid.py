import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

print("=== SendGrid Configuration Test ===\n")

# Check environment variables
api_key = os.environ.get('SENDGRID_API_KEY')
from_email = os.environ.get('DEFAULT_FROM_EMAIL')
to_email = os.environ.get('TO_EMAIL')

print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0} characters")
print(f"From Email: {from_email}")
print(f"To Email: {to_email}")
print()

if not all([api_key, from_email, to_email]):
    print("❌ Missing environment variables!")
    exit(1)

# Test SendGrid API connection
print("Testing SendGrid API connection...")
try:
    sg = SendGridAPIClient(api_key)

    # Create a simple test message
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='SendGrid Test Email from Django Backend',
        html_content=('<strong>This is a test email from your ESE inventory system!</strong>'
                      '<br><br>If you received this, SendGrid is configured correctly.')
    )

    print(f"\nAttempting to send email from {from_email} to {to_email}...")
    response = sg.send(message)

    print("\n✅ Email sent successfully!")
    print("Status Code: {}".format(response.status_code))
    print("Message ID: {}".format(response.headers.get('X-Message-Id', 'N/A')))

    if response.status_code == 202:
        print("\n🎉 Success! Check your inbox at", to_email)
        print("\nNote: Email might take a few minutes to arrive.")
        print("Check spam folder if you don't see it in inbox.")

except Exception as e:
    print(f"\n❌ Error: {str(e)}\n")

    # Provide helpful debugging info
    if "certificate" in str(e).lower() or "ssl" in str(e).lower():
        print("This is an SSL certificate issue. Usually caused by:")
        print("1. Corporate/school network with SSL inspection")
        print("2. VPN or proxy interfering with SSL")
        print("3. System certificates not installed properly")
        print("\nTry running the email send from a different network.")

    elif "unauthorized" in str(e).lower() or "401" in str(e):
        print("API Key issue. Check that:")
        print("1. Your API key is correct in .env")
        print("2. API key has 'Mail Send' permissions")
        print("3. API key hasn't been revoked/expired")

    elif "403" in str(e) or "forbidden" in str(e).lower():
        print("Sender verification issue. Make sure:")
        print("1. You've verified your sender email in SendGrid")
        print("2. Go to: SendGrid → Settings → Sender Authentication")
        print("3. Verify the single sender:", from_email)

    else:
        print("Unexpected error. Check:")
        print("1. Your internet connection")
        print("2. SendGrid dashboard for any account issues")
        print("3. Your API key permissions")
