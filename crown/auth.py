import hashlib
import json
import time
import uuid

import jwt


def sign_request(
    *,
    api_key: str,
    private_key: str,
    uri: str,
    body: dict | None = None,
) -> str:
    """Create a signed JWT for a Crown API request.

    Args:
        api_key: Your Crown API key.
        private_key: RSA private key in PEM format.
        uri: The API endpoint path (e.g. "/api/v0/orders").
        body: Request body dict for POST requests, or None for GET.

    Returns:
        A signed JWT string.
    """
    body_str = json.dumps(body) if body else ""
    body_hash = hashlib.sha256(body_str.encode()).hexdigest()

    now = int(time.time())
    payload = {
        "uri": uri,
        "nonce": str(uuid.uuid4()),
        "iat": now,
        "exp": now + 30,
        "sub": api_key,
        "bodyHash": body_hash,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")
