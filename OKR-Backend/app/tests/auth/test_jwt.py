"""
Unit tests for JWT utilities.
"""

import pytest
from jose import JWTError

from app.auth.jwt import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)

# =====================================================
# Token Creation
# =====================================================


def test_create_access_token_returns_string():
    token = create_access_token(
        {
            "sub": "user-id",
            "email": "test@test.com",
        }
    )

    assert isinstance(token, str)
    assert token


def test_create_refresh_token_returns_string():
    token = create_refresh_token(
        {
            "sub": "user-id",
            "email": "test@test.com",
        }
    )

    assert isinstance(token, str)
    assert token


def test_access_and_refresh_tokens_are_different():
    claims = {
        "sub": "user-id",
        "email": "test@test.com",
    }

    access = create_access_token(claims)
    refresh = create_refresh_token(claims)

    assert access != refresh


# =====================================================
# Decode Token
# =====================================================


def test_decode_access_token():
    token = create_access_token(
        {
            "sub": "user-id",
            "email": "test@test.com",
        }
    )

    payload = decode_token(token)

    assert payload["sub"] == "user-id"
    assert payload["email"] == "test@test.com"
    assert payload["token_type"] == ACCESS_TOKEN_TYPE


def test_decode_refresh_token():
    token = create_refresh_token(
        {
            "sub": "user-id",
            "email": "test@test.com",
        }
    )

    payload = decode_token(token)

    assert payload["sub"] == "user-id"
    assert payload["email"] == "test@test.com"
    assert payload["token_type"] == REFRESH_TOKEN_TYPE


# =====================================================
# JWT Standard Claims
# =====================================================


def test_access_token_contains_iat():
    token = create_access_token({"sub": "1"})

    payload = decode_token(token)

    assert "iat" in payload


def test_access_token_contains_exp():
    token = create_access_token({"sub": "1"})

    payload = decode_token(token)

    assert "exp" in payload


def test_access_token_contains_jti():
    token = create_access_token({"sub": "1"})

    payload = decode_token(token)

    assert "jti" in payload


def test_jti_is_unique():
    token1 = create_access_token({"sub": "1"})

    token2 = create_access_token({"sub": "1"})

    payload1 = decode_token(token1)
    payload2 = decode_token(token2)

    assert payload1["jti"] != payload2["jti"]


# =====================================================
# Token Type Verification
# =====================================================


def test_verify_access_token_type():
    payload = {
        "token_type": ACCESS_TOKEN_TYPE,
    }

    verify_token_type(
        payload,
        ACCESS_TOKEN_TYPE,
    )


def test_verify_refresh_token_type():
    payload = {
        "token_type": REFRESH_TOKEN_TYPE,
    }

    verify_token_type(
        payload,
        REFRESH_TOKEN_TYPE,
    )


def test_verify_token_type_raises_for_wrong_type():
    payload = {
        "token_type": REFRESH_TOKEN_TYPE,
    }

    with pytest.raises(ValueError):
        verify_token_type(
            payload,
            ACCESS_TOKEN_TYPE,
        )


def test_verify_token_type_raises_when_missing():
    payload = {}

    with pytest.raises(ValueError):
        verify_token_type(
            payload,
            ACCESS_TOKEN_TYPE,
        )


# =====================================================
# Invalid Tokens
# =====================================================


def test_decode_invalid_token():
    with pytest.raises(JWTError):
        decode_token("invalid.token.value")


def test_decode_empty_token():
    with pytest.raises(JWTError):
        decode_token("")


def test_decode_modified_token():
    token = create_access_token(
        {
            "sub": "user-id",
            "email": "test@test.com",
        }
    )

    tampered = token[:-5] + "abcde"

    with pytest.raises(JWTError):
        decode_token(tampered)


# =====================================================
# Claims Preservation
# =====================================================


def test_custom_claims_are_preserved():
    token = create_access_token(
        {
            "sub": "user-id",
            "email": "test@test.com",
            "role": "admin",
            "organization": "okr",
        }
    )

    payload = decode_token(token)

    assert payload["role"] == "admin"
    assert payload["organization"] == "okr"


def test_uuid_subject_is_preserved():
    uuid = "550e8400-e29b-41d4-a716-446655440000"

    token = create_access_token(
        {
            "sub": uuid,
        }
    )

    payload = decode_token(token)

    assert payload["sub"] == uuid
