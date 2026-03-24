import logging
from uuid import UUID

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from config import settings
from contracts.shared import UserRole

logger = logging.getLogger("recruittech.auth")

# Supabase JWTs are signed with the project's JWT secret (not the anon key).
# Set SUPABASE_JWT_SECRET in .env to match your Supabase project's JWT secret.
# Default matches the standard local Supabase dev JWT secret.
SUPABASE_JWT_SECRET = settings.supabase_jwt_secret
ALGORITHM = "HS256"

security = HTTPBearer()


class CurrentUser(BaseModel):
    """Represents the authenticated user extracted from JWT."""

    id: UUID
    email: str
    role: UserRole


def decode_supabase_jwt(token: str) -> dict:
    """Decode and validate a Supabase JWT token.

    Supabase JWTs contain:
    - sub: user UUID
    - email: user email
    - user_metadata: { role: "talent_partner" | "client" | "admin" }
    """
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> CurrentUser:
    """FastAPI dependency: extract and validate current user from JWT.

    Usage in routes:
        @router.get("/something")
        async def something(user: CurrentUser = Depends(get_current_user)):
            ...
    """
    payload = decode_supabase_jwt(credentials.credentials)

    user_id = payload.get("sub")
    email = payload.get("email", "")
    user_metadata = payload.get("user_metadata", {})
    role_str = user_metadata.get("role", "talent_partner")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

    try:
        role = UserRole(role_str)
    except ValueError:
        raise HTTPException(status_code=401, detail=f"Invalid role: {role_str}")

    return CurrentUser(id=UUID(user_id), email=email, role=role)


def require_role(*allowed_roles: UserRole):
    """Dependency factory: restrict endpoint to specific roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: CurrentUser = Depends(require_role(UserRole.admin))
        ):
            ...

    Multiple roles:
        @router.get("/partners-and-admins")
        async def endpoint(
            user: CurrentUser = Depends(require_role(UserRole.talent_partner, UserRole.admin))
        ):
            ...
    """

    async def role_checker(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}",
            )
        return user

    return role_checker


# Convenience dependencies for common role combinations
require_admin = require_role(UserRole.admin)
require_talent_partner = require_role(UserRole.talent_partner, UserRole.admin)
require_client = require_role(UserRole.client, UserRole.admin)
require_any_authenticated = require_role(
    UserRole.talent_partner, UserRole.client, UserRole.admin
)
