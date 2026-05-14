#!/usr/bin/env python
import sys
sys.path.insert(0, "C:\\Users\\User\\Desktop\\PMS")

try:
    # Try importing all modules
    from src.config.settings import settings
    print("✓ settings imports successfully")
    
    from src.config.database_config import database_config
    print("✓ database_config imports successfully")
    
    from src.utils.security import hash_identifier, hash_ip_address, hash_password
    print("✓ security module imports successfully")
    
    from src.services.audit_service import AuditService
    print("✓ audit_service imports successfully")
    
    print("\n✓ All core modules import without errors")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
