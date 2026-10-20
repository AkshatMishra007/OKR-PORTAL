from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)


def test_jwt_flow():

    payload = {
        "sub": "123",
        "email": "test@test.com",
    }

    access_token = create_access_token(payload)

    refresh_token = create_refresh_token(
        {
            "sub": "123",
        }
    )

    access_payload = decode_token(access_token)

    refresh_payload = decode_token(refresh_token)

    assert access_payload["sub"] == "123"
    assert refresh_payload["sub"] == "123"

    verify_token_type(
        access_payload,
        "access",
    )

    verify_token_type(
        refresh_payload,
        "refresh",
    )


def test_verify_token_type_mismatch():
    import pytest

    payload = {"token_type": "access"}
    with pytest.raises(ValueError, match="Invalid token type"):
        verify_token_type(payload, "refresh")


def test_decode_invalid_token():
    import pytest

    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_token("invalid.jwt.token")
