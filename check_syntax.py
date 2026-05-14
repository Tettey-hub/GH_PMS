#!/usr/bin/env python
import sys
import py_compile

files_to_check = [
    "main.py",
    "src/config/settings.py",
    "src/config/database_config.py",
    "src/utils/security.py",
    "src/services/audit_service.py",
    "src/services/account_lockout_service.py",
    "src/services/rate_limit_service.py",
    "src/services/refresh_token_service.py",
    "src/controllers/auth_controller.py",
    "src/middlewares/security_headers_middleware.py",
    "src/middlewares/error_handler.py",
    "src/middlewares/request_validation_middleware.py",
    "src/middlewares/maintenance_middleware.py",
]

errors = []
for file in files_to_check:
    try:
        py_compile.compile(file, doraise=True)
        print(f"✓ {file}")
    except py_compile.PyCompileError as e:
        print(f"✗ {file}: {e}")
        errors.append((file, e))

if errors:
    print(f"\n{len(errors)} file(s) have syntax errors")
    sys.exit(1)
else:
    print(f"\n✓ All {len(files_to_check)} files passed syntax check")
    sys.exit(0)
