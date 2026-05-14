CREATE TABLE IF NOT EXISTS api_rate_limits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    scope VARCHAR(100) NOT NULL,
    identifier_hash CHAR(64) NOT NULL,
    window_start DATETIME NOT NULL,
    request_count INT NOT NULL DEFAULT 1,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_api_rate_limits_scope_identifier_window (scope, identifier_hash, window_start),
    INDEX idx_api_rate_limits_window_start (window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
