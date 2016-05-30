import twilio

from twilio.rest import TwilioRestClient

# put your own credentials here
ACCOUNT_SID = "AC1d0ac93061063ebcfa142779c5e62875"
AUTH_TOKEN = "a8d86e42d0a4b68106b2499a00d0fa0b"

client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

client.messages.create(
    to="4404768415",
    from_="+12164506265",
    body="test message"
)