from __future__ import annotations

from flask import g, jsonify

from src.services.permission_service import PermissionService


def test_permission_check():
    """
    Test endpoint to check if current user has specific permission.
    
    Query Parameters:
        permission: The permission name to check (e.g., 'users_create')
    
    Returns:
        {
            "user_id": 1,
            "permission": "users_create",
            "has_permission": true,
            "all_permissions": ["users_create", "users_read", ...]
        }
    """
    from flask import request
    
    permission_name = request.args.get("permission", "").strip()
    if not permission_name:
        return jsonify({"error": "permission query parameter is required"}), 400

    user_id = g.current_user.id
    has_permission = PermissionService.user_has_permission(user_id, permission_name)
    all_permissions = sorted(PermissionService.get_user_permissions(user_id))

    return jsonify({
        "user_id": user_id,
        "user_role": g.current_user.role,
        "permission": permission_name,
        "has_permission": has_permission,
        "all_permissions": all_permissions,
    }), 200


def test_module_access():
    """
    Test endpoint to check if current user has access to a module.
    
    Query Parameters:
        module: The module name to check (e.g., 'users', 'prisons', 'visits')
    
    Returns:
        {
            "user_id": 1,
            "module": "users",
            "has_module_access": true,
            "module_permissions": ["users_create", "users_read", "users_update"]
        }
    """
    from flask import request
    
    module_name = request.args.get("module", "").strip()
    if not module_name:
        return jsonify({"error": "module query parameter is required"}), 400

    user_id = g.current_user.id
    has_module_access = PermissionService.user_has_module_access(user_id, module_name)
    all_permissions = PermissionService.get_user_permissions(user_id)
    module_permissions = sorted([p for p in all_permissions if p.startswith(f"{module_name}_")])

    return jsonify({
        "user_id": user_id,
        "user_role": g.current_user.role,
        "module": module_name,
        "has_module_access": has_module_access,
        "module_permissions": module_permissions,
    }), 200


def test_user_permissions():
    """
    Test endpoint to view all permissions for current user.
    
    Returns:
        {
            "user_id": 1,
            "user_role": "admin",
            "total_permissions": 25,
            "permissions_by_module": {
                "users": ["manage_users_module", "users_create", "users_read", ...],
                "prisons": [...],
                ...
            }
        }
    """
    user_id = g.current_user.id
    user_role = g.current_user.role
    all_permissions = PermissionService.get_user_permissions(user_id)
    
    # Group permissions by module
    permissions_by_module = {}
    for perm in all_permissions:
        parts = perm.split("_")
        if perm.endswith("_module"):
            module = perm.replace("manage_", "").replace("_module", "")
        else:
            module = parts[0]
        
        if module not in permissions_by_module:
            permissions_by_module[module] = []
        permissions_by_module[module].append(perm)
    
    # Sort permissions within each module
    for module in permissions_by_module:
        permissions_by_module[module].sort()

    return jsonify({
        "user_id": user_id,
        "user_role": user_role,
        "total_permissions": len(all_permissions),
        "permissions_by_module": permissions_by_module,
    }), 200


def test_role_permissions():
    """
    Test endpoint to view all permissions for a specific role.
    
    Query Parameters:
        role: The role name (e.g., 'admin', 'officer', 'supervisor')
    
    Returns:
        {
            "role": "officer",
            "total_permissions": 8,
            "permissions": ["incidents_create", "incidents_read", ...]
        }
    """
    from flask import request
    
    role_name = request.args.get("role", "").strip()
    if not role_name:
        return jsonify({"error": "role query parameter is required"}), 400

    valid_roles = {"admin", "officer", "supervisor", "medical_officer", "records_officer", "visitor_officer"}
    if role_name not in valid_roles:
        return jsonify({
            "error": f"Invalid role. Must be one of: {', '.join(sorted(valid_roles))}"
        }), 400

    role_permissions = sorted(PermissionService.get_role_permissions(role_name))

    return jsonify({
        "role": role_name,
        "total_permissions": len(role_permissions),
        "permissions": role_permissions,
    }), 200
