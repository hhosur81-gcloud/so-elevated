"""Cryptographic Signed JWT Token Management & JWKS Export (ADR-0006, SEC-0001)."""

import base64
import time
import uuid
from typing import Any, Dict, List, Optional
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)
from src.config.settings import settings


class JWTManager:
    """Manages asymmetric cryptographic signing, claim validation, and JWKS discovery."""

    def __init__(self, private_key: Optional[ec.EllipticCurvePrivateKey] = None, kid: Optional[str] = None):
        """Initialize JWTManager with an ECDSA P-256 key pair."""
        if private_key is None:
            self._private_key = ec.generate_private_key(ec.SECP256R1())
        else:
            self._private_key = private_key

        self._public_key = self._private_key.public_key()
        self._kid = kid or f"key-{uuid.uuid4().hex[:8]}"
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience

    @property
    def kid(self) -> str:
        """Current Key ID."""
        return self._kid

    def generate_delegated_token(
        self,
        employee_id: str,
        scopes: List[str],
        expires_in_seconds: Optional[int] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a signed delegated JWT bearer token for downstream MCP origin verification."""
        now = int(time.time())
        ttl = expires_in_seconds if expires_in_seconds is not None else settings.jwt_ttl_seconds
        exp = now + ttl

        payload = {
            "sub": employee_id,
            "iss": self._issuer,
            "aud": self._audience,
            "scopes": scopes,
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
        }

        if custom_claims:
            payload.update(custom_claims)

        headers = {
            "kid": self._kid,
            "alg": "ES256",
            "typ": "JWT"
        }

        pem_private = self._private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        )

        token = jwt.encode(
            payload,
            pem_private,
            algorithm="ES256",
            headers=headers
        )

        return token if isinstance(token, str) else token.decode("utf-8")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Cryptographically verify token signature, expiry, issuer, and audience."""
        pem_public = self._public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )

        claims = jwt.decode(
            token,
            pem_public,
            algorithms=["ES256"],
            issuer=self._issuer,
            audience=self._audience,
            options={"require": ["exp", "iss", "sub", "aud", "scopes"]}
        )

        return claims

    def has_scope(self, claims: Dict[str, Any], required_scope: str) -> bool:
        """Verify whether token claims contain the required authorization scope."""
        scopes = claims.get("scopes", [])
        return required_scope in scopes or "*" in scopes

    def get_jwks(self) -> Dict[str, Any]:
        """Export JSON Web Key Set (JWKS) dictionary for public key discovery (SEC-0001)."""
        numbers = self._public_key.public_numbers()
        
        # Base64url encode coordinates without padding
        def b64url_uint(val: int) -> str:
            byte_len = (val.bit_length() + 7) // 8
            b = val.to_bytes(byte_len, "big")
            return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")

        x_b64 = b64url_uint(numbers.x)
        y_b64 = b64url_uint(numbers.y)

        return {
            "keys": [
                {
                    "kty": "EC",
                    "crv": "P-256",
                    "alg": "ES256",
                    "use": "sig",
                    "kid": self._kid,
                    "x": x_b64,
                    "y": y_b64,
                }
            ]
        }
