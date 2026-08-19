"""Unit tests for Asymmetric Signed JWT Token Generation & Verification (ADR-0006, SEC-0001)."""

import unittest
import time


class TestSecurityJWT(unittest.TestCase):
    """Test suite verifying asymmetric JWT signing, claims validation, and JWKS discovery."""

    def setUp(self):
        from src.config.security import JWTManager
        self.jwt_manager = JWTManager()

    def test_generate_and_verify_valid_token(self):
        """Verify generation and cryptographic verification of delegated bearer token."""
        token = self.jwt_manager.generate_delegated_token(
            employee_id="EMP-1001",
            scopes=["hcm:leave:read", "hcm:leave:write"]
        )
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 50)

        # Verify signature and claims
        claims = self.jwt_manager.verify_token(token)
        self.assertEqual(claims["sub"], "EMP-1001")
        self.assertEqual(claims["iss"], "so-elevated-hr-orchestrator")
        self.assertEqual(claims["aud"], "enterprise-mcp-mesh")
        self.assertIn("hcm:leave:write", claims["scopes"])
        self.assertTrue(claims["exp"] > time.time())

    def test_verify_scope_permission(self):
        """Verify scope authorization checking."""
        token = self.jwt_manager.generate_delegated_token(
            employee_id="EMP-1001",
            scopes=["hcm:leave:read"]
        )
        claims = self.jwt_manager.verify_token(token)

        self.assertTrue(self.jwt_manager.has_scope(claims, "hcm:leave:read"))
        self.assertFalse(self.jwt_manager.has_scope(claims, "itsm:ticket:write"))

    def test_expired_token_rejected(self):
        """Verify expired tokens are rejected with TokenExpired error."""
        token = self.jwt_manager.generate_delegated_token(
            employee_id="EMP-1001",
            scopes=["hcm:leave:read"],
            expires_in_seconds=-10  # Already expired
        )
        with self.assertRaises(Exception):
            self.jwt_manager.verify_token(token)

    def test_tampered_token_rejected(self):
        """Verify token tampering breaks signature verification."""
        token = self.jwt_manager.generate_delegated_token(
            employee_id="EMP-1001",
            scopes=["hcm:leave:read"]
        )
        parts = token.split(".")
        # Tamper payload
        tampered_token = f"{parts[0]}.eyJuZXdfc3ViIjoiRVhQTElDSVRfQVRUQUNLRVIifQ.{parts[2]}"
        with self.assertRaises(Exception):
            self.jwt_manager.verify_token(tampered_token)

    def test_jwks_export(self):
        """Verify JSON Web Key Set (JWKS) public key export (SEC-0001)."""
        jwks = self.jwt_manager.get_jwks()
        self.assertIn("keys", jwks)
        self.assertTrue(len(jwks["keys"]) >= 1)
        key = jwks["keys"][0]
        self.assertEqual(key["kty"], "EC")
        self.assertEqual(key["crv"], "P-256")
        self.assertEqual(key["alg"], "ES256")
        self.assertEqual(key["use"], "sig")
        self.assertIn("kid", key)
        self.assertIn("x", key)
        self.assertIn("y", key)


if __name__ == "__main__":
    unittest.main()
