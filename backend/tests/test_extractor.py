import pytest
from app.services.contact_miner import clean_email

def test_clean_valid_email():
    assert clean_email("info@sample-ramen.jp") == "info@sample-ramen.jp"
    assert clean_email(" Contact@bar-tokyo.com ") == "contact@bar-tokyo.com"

def test_exclude_portal_emails():
    assert clean_email("support@tabelog.com") is None
    assert clean_email("info@hotpepper.jp") is None
    assert clean_email("customer@ubereats.com") is None

def test_exclude_system_emails():
    assert clean_email("noreply@sample-store.jp") is None
    assert clean_email("mailer-daemon@sample-store.jp") is None

def test_exclude_image_extensions():
    assert clean_email("logo.png@2x.com") is None
    assert clean_email("banner.jpg@example.org") is None
