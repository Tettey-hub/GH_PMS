from __future__ import annotations

from src.models.user import User
from src.services.refresh_token_service import RefreshTokenService
from src.services.user_service import UserService
from src.utils.security import create_access_token, create_refresh_token, decode_token, generate_token_id, verify_password


class AuthService:
    @staticmethod
    def authenticate(email: str, password: str) -> User | None:
        user = UserService.get_by_email(email)
        if user is None or user.status != "active":
            return None
        if not verify_password(password, user.password):
            return None
        return user

    @staticmethod
    def issue_tokens(user: User) -> dict[str, str | int]:
        if user.id is None:
            raise ValueError("User account is missing an ID")

        refresh_token_id = generate_token_id()
        access_token = create_access_token(user.id, user.officer_id, user.role)
        refresh_token = create_refresh_token(user.id, user.officer_id, user.role, refresh_token_id)
        RefreshTokenService.store_token(user.id, refresh_token, refresh_token_id)

        return {
            "token_type": "Bearer",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def refresh_session(refresh_token: str) -> tuple[User, dict[str, str | int]] | None:
        decoded = decode_token(refresh_token, expected_type="refresh")
        user_id = int(decoded["sub"])
        token_id = str(decoded["jti"])
        user = UserService.get_by_id(user_id)

        if user is None or user.status != "active" or user.id is None:
            return None
        if not RefreshTokenService.is_token_active(refresh_token, token_id, user.id):
            return None

        new_refresh_token_id = generate_token_id()
        new_access_token = create_access_token(user.id, user.officer_id, user.role)
        new_refresh_token = create_refresh_token(user.id, user.officer_id, user.role, new_refresh_token_id)
        RefreshTokenService.rotate_token(refresh_token, token_id, new_refresh_token_id)
        RefreshTokenService.store_token(user.id, new_refresh_token, new_refresh_token_id)

        return (
            user,
            {
                "token_type": "Bearer",
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
            },
        )

    @staticmethod
    def logout_user(user_id: int) -> int:
        return RefreshTokenService.revoke_user_tokens(user_id)
