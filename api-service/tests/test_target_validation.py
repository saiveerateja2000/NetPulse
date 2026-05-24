from pydantic import ValidationError

from app.main import TargetRequest


def test_accepts_ip_target():
    target = TargetRequest(target="8.8.8.8")
    assert target.target == "8.8.8.8"


def test_accepts_domain_target():
    target = TargetRequest(target="google.com")
    assert target.target == "google.com"


def test_rejects_invalid_target():
    try:
        TargetRequest(target="invalid_target")
        assert False, "Expected ValidationError"
    except ValidationError as exc:
        assert "target must be a valid IP address or domain" in str(exc)
