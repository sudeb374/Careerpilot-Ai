import jwt
from fastapi import HTTPException, status
from jwt.exceptions import ExpiredSignatureError, InvalidIssuerError, InvalidTokenError

from app.core.config import settings

# Cache the JWKS client so we don't fetch it on every request
_jwks_client = None


def get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        if not settings.supabase_url:
            raise ValueError("SUPABASE_URL must be configured to fetch JWKS.")
        # Standard Supabase JWKS endpoint
        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = jwt.PyJWKClient(jwks_url)
    return _jwks_client


def verify_token(token: str) -> dict:
    """
    Verifies a Supabase JWT token.
    Supports legacy HS256 (using SUPABASE_JWT_SECRET) and modern asymmetric (RS256, ES256 using JWKS).
    """
    try:
        # Decode the unverified header to determine the signing algorithm
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")

        # Supabase default issuer is usually the Supabase URL or something specific,
        # but often it's safe to validate the audience or just rely on signature and expiration.
        # Typically audience is "authenticated" for Supabase access tokens.

        verify_kwargs = {
            "algorithms": [alg],
            "audience": "authenticated",
            "issuer": f"{settings.supabase_url.rstrip('/')}/auth/v1",
            "options": {
                "verify_aud": True,
                "verify_exp": True,
                "verify_iss": True,
            },
        }

        if alg == "HS256":
            # Legacy verification using symmetric key
            if not settings.supabase_jwt_secret:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SUPABASE_JWT_SECRET is not configured for HS256 tokens.",
                )
            payload = jwt.decode(token, settings.supabase_jwt_secret, **verify_kwargs)
            return payload

        elif alg in ("RS256", "ES256"):
            # Modern verification using JWKS (Asymmetric algorithms)
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(token, signing_key.key, **verify_kwargs)
            return payload

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported token algorithm: {alg}",
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer"
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e!s}"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
