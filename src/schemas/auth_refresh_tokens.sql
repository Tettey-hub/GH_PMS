CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    jti VARCHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME NULL,
    replaced_by_jti VARCHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_auth_refresh_tokens_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    INDEX idx_auth_refresh_tokens_user_id (user_id),
    INDEX idx_auth_refresh_tokens_token_hash (token_hash),
    INDEX idx_auth_refresh_tokens_expires_at (expires_at),
    INDEX idx_auth_refresh_tokens_revoked_at (revoked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
