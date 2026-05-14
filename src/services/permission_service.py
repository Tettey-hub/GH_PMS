from __future__ import annotations

from src.config.database_config import db_connection


class PermissionService:
    """Service for managing and checking user permissions."""

    @staticmethod
    def user_has_permission(user_id: int, permission_name: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: The ID of the user to check
            permission_name: The name of the permission (e.g., 'users_create')
        
        Returns:
            True if the user has the permission, False otherwise
        """
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM role_permissions rp
                INNER JOIN permissions p ON rp.permission_id = p.id
                INNER JOIN users u ON rp.role = u.role
                WHERE u.id = %s AND p.name = %s
                LIMIT 1
                """,
                (user_id, permission_name),
            )
            result = cursor.fetchone()
            cursor.close()

        return result is not None

    @staticmethod
    def user_has_module_access(user_id: int, module_name: str) -> bool:
        """
        Check if a user has access to a specific module.
        
        Args:
            user_id: The ID of the user to check
            module_name: The name of the module (e.g., 'users', 'prisons')
        
        Returns:
            True if the user has module access, False otherwise
        """
        module_permission = f"manage_{module_name}_module"
        return PermissionService.user_has_permission(user_id, module_permission)

    @staticmethod
    def get_user_permissions(user_id: int) -> set[str]:
        """
        Get all permissions for a specific user.
        
        Args:
            user_id: The ID of the user
        
        Returns:
            Set of permission names the user has
        """
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT DISTINCT p.name
                FROM role_permissions rp
                INNER JOIN permissions p ON rp.permission_id = p.id
                INNER JOIN users u ON rp.role = u.role
                WHERE u.id = %s
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            cursor.close()

        return {row[0] for row in rows}

    @staticmethod
    def get_role_permissions(role: str) -> set[str]:
        """
        Get all permissions for a specific role.
        
        Args:
            role: The name of the role (e.g., 'admin', 'officer')
        
        Returns:
            Set of permission names for the role
        """
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT DISTINCT p.name
                FROM role_permissions rp
                INNER JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role = %s
                """,
                (role,),
            )
            rows = cursor.fetchall()
            cursor.close()

        return {row[0] for row in rows}
