CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor_user_id INT NULL,
    target_user_id INT NULL,
    action VARCHAR(80) NOT NULL,
    status VARCHAR(20) NOT NULL,
    ip_hash CHAR(64) NULL,
    user_agent VARCHAR(255) NULL,
    metadata JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_logs_actor_user_id
        FOREIGN KEY (actor_user_id) REFERENCES users(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_audit_logs_target_user_id
        FOREIGN KEY (target_user_id) REFERENCES users(id)
        ON DELETE SET NULL,
    INDEX idx_audit_logs_actor_user_id (actor_user_id),
    INDEX idx_audit_logs_target_user_id (target_user_id),
    INDEX idx_audit_logs_action (action),
    INDEX idx_audit_logs_status (status),
    INDEX idx_audit_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
