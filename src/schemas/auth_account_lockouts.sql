CREATE TABLE IF NOT EXISTS auth_account_lockouts (
    identifier_hash CHAR(64) PRIMARY KEY,
    user_id INT NULL,
    failed_attempts INT NOT NULL DEFAULT 0,
    first_failed_at DATETIME NULL,
    last_failed_at DATETIME NULL,
    locked_until DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_auth_account_lockouts_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL,
    INDEX idx_auth_account_lockouts_user_id (user_id),
    INDEX idx_auth_account_lockouts_locked_until (locked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
