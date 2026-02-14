from .mock import MockMessaging, MockEmail, MockPayment

# Later: add Twilio/Meta/Stripe providers here

def get_messaging_provider(provider: str):
    return MockMessaging()

def get_email_provider(provider: str):
    return MockEmail()

def get_payment_provider(provider: str):
    return MockPayment()
