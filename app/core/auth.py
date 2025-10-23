from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from .settings import config_settings

# 1. Define the scheme (This tells FastAPI where to look for the token)
# We use "/api/v1/auth/token" as the tokenUrl, which is where clients
# should request a new token if the API supported username/password login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# NOTE: In a real application, you would need to securely store the secret key
# and use a library like `python-jose` to decode the JWT token.

def require_auth_token(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Dependency function that requires a Bearer token and attempts to validate it.

    If no token is provided, OAuth2PasswordBearer automatically raises
    a 401 Unauthorized exception.
    """

    # Placeholder for token validation and user retrieval logic:
    # -----------------------------------------------------------

    # 1. Check if the token is valid (e.g., check expiry, signature)
    # 2. Extract the user ID or other claims from the token payload

    # For this example, we just check if the token is present (which the
    # Depends(oauth2_scheme) already handles for the HTTP header part).

    if not token or token not in config_settings.TOKENS:
        # This part is generally redundant because oauth2_scheme handles the
        # header check, but included for complete logic flow.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In a real app, you would return a User object here.
    # For demonstration, we just return the token.
    return token
