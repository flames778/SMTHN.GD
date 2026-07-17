"""Encrypted token storage for OAuth credentials."""

from __future__ import annotations

import base64
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class TokenEncryption:
    """Encrypt and decrypt integration tokens using Fernet (AES-128-CBC with HMAC)."""

    def __init__(self, encryption_key: str) -> None:
        """Initialize with a 32+ character encryption key.

        The key is hashed to produce a valid Fernet key.
        """
        if not encryption_key or len(encryption_key) < 32:
            raise ValueError("Encryption key must be at least 32 characters")

        import hashlib

        key_hash = hashlib.sha256(encryption_key.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(key_hash))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext token to a base64-encoded ciphertext."""
        if not plaintext:
            return ""
        encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """Decrypt a ciphertext token to plaintext, or None if invalid."""
        if not ciphertext:
            return ""
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted.decode("utf-8")
        except InvalidToken:
            return None
