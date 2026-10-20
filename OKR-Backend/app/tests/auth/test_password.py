"""
Unit tests for password hashing utilities.
"""

from app.auth.password import (
    hash_password,
    verify_password,
)

# =====================================================
# Password Hashing
# =====================================================


def test_hash_password_returns_string():
    """
    Hash function should return a string.
    """

    hashed = hash_password("Test@123")

    assert isinstance(hashed, str)


def test_hash_password_is_not_plain_text():
    """
    Hashed password should never equal plain password.
    """

    password = "Test@123"

    hashed = hash_password(password)

    assert hashed != password


def test_same_password_generates_different_hashes():
    """
    Bcrypt should generate different hashes because of random salt.
    """

    password = "Test@123"

    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2


def test_hash_has_bcrypt_prefix():
    """
    Generated hash should be a bcrypt hash.
    """

    hashed = hash_password("Test@123")

    assert hashed.startswith("$2")


# =====================================================
# Password Verification
# =====================================================


def test_verify_password_success():
    """
    Correct password should verify successfully.
    """

    password = "Test@123"

    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_wrong_password():
    """
    Incorrect password should fail verification.
    """

    hashed = hash_password("Test@123")

    assert verify_password("WrongPassword", hashed) is False


def test_verify_password_empty_password():
    """
    Empty password should not match.
    """

    hashed = hash_password("Test@123")

    assert verify_password("", hashed) is False


def test_verify_password_empty_hash():
    """
    Empty hash should safely return False.
    """

    assert verify_password("Test@123", "") is False


def test_verify_password_invalid_hash():
    """
    Random string should not crash verification.
    """

    assert (
        verify_password(
            "Test@123",
            "not-a-valid-bcrypt-hash",
        )
        is False
    )


def test_verify_password_none_like_hash():
    """
    Malformed hash should return False instead of raising.
    """

    assert (
        verify_password(
            "Test@123",
            "12345",
        )
        is False
    )


# =====================================================
# Edge Cases
# =====================================================


def test_hash_empty_password():
    """
    Empty password can still be hashed.
    """

    hashed = hash_password("")

    assert hashed
    assert verify_password("", hashed)


def test_hash_unicode_password():
    """
    Unicode passwords should hash correctly.
    """

    password = "Pāsswørd🔒भारत"

    hashed = hash_password(password)

    assert verify_password(password, hashed)


def test_hash_long_password():
    """
    Long passwords should hash successfully.
    """

    password = "A" * 100

    hashed = hash_password(password)

    assert verify_password(password, hashed)


def test_password_verification_is_case_sensitive():
    """
    Password comparison should be case-sensitive.
    """

    password = "Password123"

    hashed = hash_password(password)

    assert verify_password("password123", hashed) is False
