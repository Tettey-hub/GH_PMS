-- Permissions table: Define all available permissions in the system
CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_permissions_name (name),
    INDEX idx_permissions_module (module),
    INDEX idx_permissions_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Role-Permission mapping table: Define which roles have which permissions
CREATE TABLE IF NOT EXISTS role_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(20) NOT NULL,
    permission_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_role_permission (role, permission_id),
    CONSTRAINT fk_role_permissions_permission_id
        FOREIGN KEY (permission_id) REFERENCES permissions(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_role_permissions_role CHECK (role IN ('admin', 'officer', 'supervisor', 'medical_officer', 'records_officer', 'visitor_officer')),
    INDEX idx_role_permissions_role (role),
    INDEX idx_role_permissions_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default permissions
INSERT IGNORE INTO permissions (name, description, module, action) VALUES
-- User Management
('manage_users_module', 'Access user management module', 'users', 'manage'),
('users_create', 'Create new users', 'users', 'create'),
('users_read', 'View user details', 'users', 'read'),
('users_update', 'Update user information', 'users', 'update'),
('users_delete', 'Delete users', 'users', 'delete'),

-- Prison Management
('manage_prisons_module', 'Access prison management module', 'prisons', 'manage'),
('prisons_create', 'Create new prisons', 'prisons', 'create'),
('prisons_read', 'View prison details', 'prisons', 'read'),
('prisons_update', 'Update prison information', 'prisons', 'update'),
('prisons_delete', 'Delete prisons', 'prisons', 'delete'),

-- Visit Management
('manage_visits_module', 'Access visit management module', 'visits', 'manage'),
('visits_create', 'Schedule new visits', 'visits', 'create'),
('visits_read', 'View visit details', 'visits', 'read'),
('visits_update', 'Update visit information', 'visits', 'update'),
('visits_delete', 'Cancel/delete visits', 'visits', 'delete'),

-- Records Management
('manage_records_module', 'Access records management module', 'records', 'manage'),
('records_create', 'Create new records', 'records', 'create'),
('records_read', 'View records', 'records', 'read'),
('records_update', 'Update records', 'records', 'update'),
('records_delete', 'Delete records', 'records', 'delete'),

-- Incident Management
('manage_incidents_module', 'Access incident management module', 'incidents', 'manage'),
('incidents_create', 'Report new incidents', 'incidents', 'create'),
('incidents_read', 'View incident details', 'incidents', 'read'),
('incidents_update', 'Update incident information', 'incidents', 'update'),
('incidents_delete', 'Delete incidents', 'incidents', 'delete');

-- Set admin permissions (all modules + CRUD)
INSERT IGNORE INTO role_permissions (role, permission_id)
SELECT 'admin', id FROM permissions;

-- Set supervisor permissions (manage users, prisons, visits, records - read/update only)
INSERT IGNORE INTO role_permissions (role, permission_id)
SELECT 'supervisor', id FROM permissions
WHERE name IN (
    'manage_users_module', 'users_read', 'users_update',
    'manage_prisons_module', 'prisons_read', 'prisons_update',
    'manage_visits_module', 'visits_read', 'visits_update', 'visits_create',
    'manage_records_module', 'records_read', 'records_update',
    'manage_incidents_module', 'incidents_read', 'incidents_update', 'incidents_create'
);

-- Set officer permissions (read-only + create incidents)
INSERT IGNORE INTO role_permissions (role, permission_id)
SELECT 'officer', id FROM permissions
WHERE name IN (
    'users_read',
    'prisons_read',
    'visits_read', 'visits_create',
    'records_read',
    'manage_incidents_module', 'incidents_create', 'incidents_read'
);

-- Set medical officer permissions (records + incidents)
INSERT IGNORE INTO role_permissions (role, permission_id)
SELECT 'medical_officer', id FROM permissions
WHERE name IN (
    'manage_records_module', 'records_create', 'records_read', 'records_update',
    'manage_incidents_module', 'incidents_create', 'incidents_read'
);

-- Set records officer permissions (records management)
INSERT IGNORE INTO role_permissions (role, permission_id)
SELECT 'records_officer', id FROM permissions
WHERE name IN (
    'manage_records_module', 'records_create', 'records_read', 'records_update', 'records_delete'
);

-- Set visitor officer permissions (visits management)
INSERT IGNORE INTO role_permissions (role, permission_id)
SELECT 'visitor_officer', id FROM permissions
WHERE name IN (
    'manage_visits_module', 'visits_create', 'visits_read', 'visits_update', 'visits_delete'
);
