"""
HMAC-Signed Confirmation Token Service for Governed AI Database Copilot.
Issues and validates short-lived (5-minute TTL) cryptographic tokens for destructive operations.
"""

import hmac
import hashlib
import time
import uuid
from typing import Tuple, Optional
from config import settings


class TokenService:
    def __init__(self, secret: Optional[str] = None, ttl_seconds: int = 300):
        sec = secret or getattr(settings, "jwt_secret", "governed-copilot-default-secret-key-32b")
        self.secret = sec.encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def issue_token(self, connection_id: str, sql: str) -> str:
        """
        Generate HMAC-SHA256 token encoding timestamp (in milliseconds) and action hash.
        Format: token_id.timestamp_ms.signature (strictly 3 dot-separated segments)
        """
        token_id = uuid.uuid4().hex[:12]
        timestamp_ms = int(time.time() * 1000)
        payload = f"{token_id}:{timestamp_ms}:{connection_id}:{sql}"
        sig = hmac.new(self.secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
        return f"{token_id}.{timestamp_ms}.{sig}"

    def verify_token(self, token: str, connection_id: str, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate token integrity and verify it has not expired (5-minute TTL).
        """
        parts = token.split(".")
        if len(parts) != 3:
            return False, "Malformed confirmation token format."

        token_id, timestamp_ms_str, received_sig = parts
        try:
            timestamp_ms = int(timestamp_ms_str)
            timestamp = timestamp_ms / 1000.0
        except ValueError:
            return False, "Invalid timestamp in confirmation token."

        # Check expiration
        current_time = time.time()
        if current_time - timestamp >= self.ttl_seconds:
            return False, "Confirmation token has expired (5-minute window exceeded). Please request a new preview."

        # Verify signature
        payload = f"{token_id}:{timestamp_ms_str}:{connection_id}:{sql}"
        expected_sig = hmac.new(self.secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:24]

        if not hmac.compare_digest(received_sig, expected_sig):
            return False, "Cryptographic signature mismatch. Token is invalid."

        return True, None


token_service = TokenService()
