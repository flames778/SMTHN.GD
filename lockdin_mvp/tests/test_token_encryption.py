"""Tests for token encryption service."""

import pytest

from app.security.token_encryption import TokenEncryption


class TestTokenEncryption:
    """Test TokenEncryption service."""

    def test_encrypt_and_decrypt_roundtrip(self):
        """Test that encrypted tokens can be decrypted."""
        key = "a" * 32
        encryption = TokenEncryption(key)

        plaintext = "test_access_token_12345"
        ciphertext = encryption.encrypt(plaintext)

        assert ciphertext != plaintext
        assert isinstance(ciphertext, str)

        decrypted = encryption.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_empty_token(self):
        """Test encrypting empty token."""
        key = "a" * 32
        encryption = TokenEncryption(key)

        result = encryption.encrypt("")
        assert result == ""

    def test_decrypt_empty_token(self):
        """Test decrypting empty token."""
        key = "a" * 32
        encryption = TokenEncryption(key)

        result = encryption.decrypt("")
        assert result == ""

    def test_decrypt_invalid_ciphertext_returns_none(self):
        """Test that invalid ciphertext returns None."""
        key = "a" * 32
        encryption = TokenEncryption(key)

        result = encryption.decrypt("invalid_ciphertext")
        assert result is None

    def test_different_keys_produce_different_ciphertexts(self):
        """Test that different keys encrypt differently."""
        plaintext = "test_token"
        key1 = "a" * 32
        key2 = "b" * 32

        enc1 = TokenEncryption(key1)
        enc2 = TokenEncryption(key2)

        ct1 = enc1.encrypt(plaintext)
        ct2 = enc2.encrypt(plaintext)

        assert ct1 != ct2

    def test_key_too_short_raises_error(self):
        """Test that short keys raise ValueError."""
        key = "short"
        with pytest.raises(ValueError, match="at least 32 characters"):
            TokenEncryption(key)

    def test_key_exactly_32_chars_accepted(self):
        """Test that 32-character keys are accepted."""
        key = "a" * 32
        encryption = TokenEncryption(key)
        plaintext = "test"
        ciphertext = encryption.encrypt(plaintext)
        assert encryption.decrypt(ciphertext) == plaintext

    def test_cross_instance_decrypt(self):
        """Test that tokens encrypted by one instance can be decrypted by another with same key."""
        key = "a" * 32
        enc1 = TokenEncryption(key)
        enc2 = TokenEncryption(key)

        plaintext = "shared_token"
        ciphertext = enc1.encrypt(plaintext)
        decrypted = enc2.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_long_token_encryption(self):
        """Test encrypting long tokens."""
        key = "a" * 32
        encryption = TokenEncryption(key)

        long_token = "x" * 5000
        ciphertext = encryption.encrypt(long_token)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == long_token

    def test_special_chars_token_encryption(self):
        """Test encrypting tokens with special characters."""
        key = "a" * 32
        encryption = TokenEncryption(key)

        token_with_special_chars = "token!@#$%^&*()_+-={}[]|:;<>?,./"
        ciphertext = encryption.encrypt(token_with_special_chars)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == token_with_special_chars
