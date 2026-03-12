from unittest.mock import MagicMock, patch

from app.routes.contact import _rate_limits


def _valid_payload(**overrides):
    base = {
        "name": "Test User",
        "email": "test@example.com",
        "message": "I need help with CSA.",
    }
    base.update(overrides)
    return base


def test_contact_success(client):
    _rate_limits.clear()
    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        response = client.post("/api/contact", json=_valid_payload())
    assert response.status_code == 200
    assert response.json()["message"] == "Message sent. I'll be in touch."
    mock_resend.Emails.send.assert_called_once()


def test_contact_with_company(client):
    _rate_limits.clear()
    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        response = client.post(
            "/api/contact", json=_valid_payload(company="Acme Medical")
        )
    assert response.status_code == 200
    call_args = mock_resend.Emails.send.call_args[0][0]
    assert "Acme Medical" in call_args["html"]


def test_contact_missing_name(client):
    _rate_limits.clear()
    response = client.post("/api/contact", json=_valid_payload(name="   "))
    assert response.status_code == 400


def test_contact_invalid_email(client):
    _rate_limits.clear()
    response = client.post("/api/contact", json=_valid_payload(email="invalid"))
    assert response.status_code == 400


def test_contact_empty_message(client):
    _rate_limits.clear()
    response = client.post("/api/contact", json=_valid_payload(message="  "))
    assert response.status_code == 400


def test_contact_name_too_long(client):
    _rate_limits.clear()
    response = client.post("/api/contact", json=_valid_payload(name="a" * 101))
    assert response.status_code == 422


def test_contact_message_too_long(client):
    _rate_limits.clear()
    response = client.post("/api/contact", json=_valid_payload(message="a" * 2001))
    assert response.status_code == 422


def test_contact_rate_limit(client):
    _rate_limits.clear()
    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        client.post("/api/contact", json=_valid_payload())
        client.post("/api/contact", json=_valid_payload())
        response = client.post("/api/contact", json=_valid_payload())
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]


def test_contact_rate_limit_resets(client):
    _rate_limits.clear()
    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        client.post("/api/contact", json=_valid_payload())
        client.post("/api/contact", json=_valid_payload())

    # Simulate window expiry
    for entry in _rate_limits.values():
        entry["reset"] = 0

    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        response = client.post("/api/contact", json=_valid_payload())
    assert response.status_code == 200


def test_contact_reply_to_set(client):
    _rate_limits.clear()
    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        client.post("/api/contact", json=_valid_payload(email="visitor@company.com"))
    call_args = mock_resend.Emails.send.call_args[0][0]
    assert call_args["reply_to"] == "visitor@company.com"


def test_contact_forwarded_ip(client):
    _rate_limits.clear()
    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        # First two from forwarded IP
        client.post(
            "/api/contact",
            json=_valid_payload(),
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        client.post(
            "/api/contact",
            json=_valid_payload(),
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        # Third should be rate limited
        response = client.post(
            "/api/contact",
            json=_valid_payload(),
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
    assert response.status_code == 429

    # Different IP should work
    _rate_limits.clear()
    with patch("app.routes.contact.resend") as mock_resend:
        mock_resend.Emails = MagicMock()
        response = client.post(
            "/api/contact",
            json=_valid_payload(),
            headers={"X-Forwarded-For": "5.6.7.8"},
        )
    assert response.status_code == 200
