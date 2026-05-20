CREATE TABLE IF NOT EXISTS court_integrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    external_case_reference VARCHAR(100) NOT NULL,
    court_name VARCHAR(150) NOT NULL,
    court_api_source VARCHAR(100) NOT NULL,
    warrant_status VARCHAR(40) NOT NULL,
    hearing_date DATETIME NULL,
    hearing_status VARCHAR(40) NOT NULL,
    sentence_status VARCHAR(40) NOT NULL,
    synchronization_status VARCHAR(30) NOT NULL,
    last_synced_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_court_integrations_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_court_integrations_warrant_status CHECK (warrant_status IN ('PENDING', 'VERIFIED', 'INVALID', 'EXPIRED', 'REVOKED')),
    CONSTRAINT chk_court_integrations_hearing_status CHECK (hearing_status IN ('PENDING', 'SCHEDULED', 'COMPLETED', 'ADJOURNED', 'CANCELLED')),
    CONSTRAINT chk_court_integrations_sentence_status CHECK (sentence_status IN ('PENDING', 'CONFIRMED', 'MODIFIED', 'BAIL_APPROVED', 'ACQUITTED', 'RELEASE_AUTHORIZED')),
    CONSTRAINT chk_court_integrations_sync_status CHECK (synchronization_status IN ('PENDING', 'IN_PROGRESS', 'SYNCED', 'FAILED', 'RETRY_SCHEDULED')),
    INDEX idx_court_integrations_inmate_id (inmate_id),
    INDEX idx_court_integrations_case_reference (external_case_reference),
    INDEX idx_court_integrations_sync_status (synchronization_status),
    INDEX idx_court_integrations_last_synced_at (last_synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS nia_integrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    national_id VARCHAR(50) NOT NULL,
    verification_status VARCHAR(30) NOT NULL,
    biometric_match_status VARCHAR(30) NOT NULL,
    demographic_sync_status VARCHAR(30) NOT NULL,
    nia_reference_number VARCHAR(100) NULL,
    last_verified_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_nia_integrations_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_nia_integrations_verification_status CHECK (verification_status IN ('PENDING', 'VERIFIED', 'FAILED', 'RETRY_SCHEDULED')),
    CONSTRAINT chk_nia_integrations_biometric_status CHECK (biometric_match_status IN ('PENDING', 'MATCHED', 'NOT_MATCHED', 'NOT_AVAILABLE')),
    CONSTRAINT chk_nia_integrations_demographic_status CHECK (demographic_sync_status IN ('PENDING', 'SYNCED', 'FAILED', 'NOT_REQUESTED')),
    INDEX idx_nia_integrations_inmate_id (inmate_id),
    INDEX idx_nia_integrations_national_id (national_id),
    INDEX idx_nia_integrations_verification_status (verification_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS police_integrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    police_reference_number VARCHAR(100) NOT NULL,
    criminal_record_status VARCHAR(30) NOT NULL,
    fingerprint_match_status VARCHAR(30) NOT NULL,
    recidivism_status VARCHAR(30) NOT NULL,
    wanted_person_status VARCHAR(30) NOT NULL,
    intelligence_notes TEXT NULL,
    synchronization_status VARCHAR(30) NOT NULL,
    last_synced_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_police_integrations_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_police_integrations_record_status CHECK (criminal_record_status IN ('PENDING', 'FOUND', 'NOT_FOUND', 'FAILED')),
    CONSTRAINT chk_police_integrations_fingerprint_status CHECK (fingerprint_match_status IN ('PENDING', 'MATCHED', 'NOT_MATCHED', 'NOT_AVAILABLE')),
    CONSTRAINT chk_police_integrations_recidivism_status CHECK (recidivism_status IN ('PENDING', 'REPEAT_OFFENDER', 'NO_MATCH', 'UNKNOWN')),
    CONSTRAINT chk_police_integrations_wanted_status CHECK (wanted_person_status IN ('PENDING', 'MATCHED', 'CLEAR', 'UNKNOWN')),
    CONSTRAINT chk_police_integrations_sync_status CHECK (synchronization_status IN ('PENDING', 'IN_PROGRESS', 'SYNCED', 'FAILED', 'RETRY_SCHEDULED')),
    INDEX idx_police_integrations_inmate_id (inmate_id),
    INDEX idx_police_integrations_reference (police_reference_number),
    INDEX idx_police_integrations_sync_status (synchronization_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS biometric_integrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NULL,
    visitor_id INT NULL,
    staff_id INT NULL,
    biometric_type VARCHAR(30) NOT NULL,
    biometric_reference_id VARCHAR(100) NOT NULL,
    enrollment_status VARCHAR(30) NOT NULL,
    verification_status VARCHAR(30) NOT NULL,
    captured_device VARCHAR(80) NOT NULL,
    captured_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_biometric_integrations_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_biometric_integrations_visitor_id
        FOREIGN KEY (visitor_id) REFERENCES visitors(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_biometric_integrations_staff_id
        FOREIGN KEY (staff_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_biometric_integrations_subject CHECK (
        (inmate_id IS NOT NULL AND visitor_id IS NULL AND staff_id IS NULL)
        OR (inmate_id IS NULL AND visitor_id IS NOT NULL AND staff_id IS NULL)
        OR (inmate_id IS NULL AND visitor_id IS NULL AND staff_id IS NOT NULL)
    ),
    CONSTRAINT chk_biometric_integrations_type CHECK (biometric_type IN ('FINGERPRINT', 'FACIAL', 'WEBCAM', 'TERMINAL')),
    CONSTRAINT chk_biometric_integrations_enrollment_status CHECK (enrollment_status IN ('PENDING', 'ENROLLED', 'FAILED', 'REVOKED')),
    CONSTRAINT chk_biometric_integrations_verification_status CHECK (verification_status IN ('PENDING', 'VERIFIED', 'FAILED', 'NOT_REQUESTED')),
    INDEX idx_biometric_integrations_inmate_id (inmate_id),
    INDEX idx_biometric_integrations_visitor_id (visitor_id),
    INDEX idx_biometric_integrations_staff_id (staff_id),
    INDEX idx_biometric_integrations_reference (biometric_reference_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS api_integrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    integration_name VARCHAR(100) NOT NULL UNIQUE,
    api_provider VARCHAR(100) NOT NULL,
    authentication_type VARCHAR(30) NOT NULL,
    endpoint_reference VARCHAR(255) NOT NULL,
    api_status VARCHAR(30) NOT NULL,
    rate_limit_status VARCHAR(30) NOT NULL,
    encryption_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_health_check DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_api_integrations_authentication_type CHECK (authentication_type IN ('OAUTH2', 'JWT', 'API_KEY', 'MFA')),
    CONSTRAINT chk_api_integrations_api_status CHECK (api_status IN ('ACTIVE', 'INACTIVE', 'DEGRADED', 'FAILED')),
    CONSTRAINT chk_api_integrations_rate_limit_status CHECK (rate_limit_status IN ('NORMAL', 'THROTTLED', 'EXCEEDED', 'DISABLED')),
    INDEX idx_api_integrations_provider (api_provider),
    INDEX idx_api_integrations_status (api_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS synchronization_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_facility VARCHAR(100) NOT NULL,
    target_server VARCHAR(150) NOT NULL,
    synchronization_type VARCHAR(20) NOT NULL,
    synchronization_status VARCHAR(30) NOT NULL,
    records_processed INT NOT NULL DEFAULT 0,
    records_failed INT NOT NULL DEFAULT 0,
    retry_count INT NOT NULL DEFAULT 0,
    last_attempt_at DATETIME NOT NULL,
    completed_at DATETIME NULL,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_synchronization_logs_type CHECK (synchronization_type IN ('REAL_TIME', 'BATCH', 'OFFLINE')),
    CONSTRAINT chk_synchronization_logs_status CHECK (synchronization_status IN ('PENDING', 'IN_PROGRESS', 'SYNCED', 'FAILED', 'RETRY_SCHEDULED')),
    CONSTRAINT chk_synchronization_logs_counts CHECK (records_processed >= 0 AND records_failed >= 0 AND retry_count >= 0),
    INDEX idx_synchronization_logs_facility (source_facility),
    INDEX idx_synchronization_logs_status (synchronization_status),
    INDEX idx_synchronization_logs_last_attempt (last_attempt_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cloud_backup_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    backup_reference VARCHAR(100) NOT NULL UNIQUE,
    backup_type VARCHAR(30) NOT NULL,
    backup_status VARCHAR(30) NOT NULL,
    storage_location VARCHAR(150) NOT NULL,
    records_backed_up INT NOT NULL DEFAULT 0,
    backup_started_at DATETIME NOT NULL,
    backup_completed_at DATETIME NULL,
    recovery_test_status VARCHAR(30) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cloud_backup_logs_type CHECK (backup_type IN ('FULL', 'INCREMENTAL', 'EMERGENCY_RECOVERY', 'RECOVERY_TEST')),
    CONSTRAINT chk_cloud_backup_logs_status CHECK (backup_status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'RESTORED')),
    CONSTRAINT chk_cloud_backup_logs_recovery_status CHECK (recovery_test_status IN ('PENDING', 'PASSED', 'FAILED', 'NOT_TESTED')),
    CONSTRAINT chk_cloud_backup_logs_records CHECK (records_backed_up >= 0),
    CONSTRAINT chk_cloud_backup_logs_completed_at CHECK (backup_completed_at IS NULL OR backup_completed_at >= backup_started_at),
    INDEX idx_cloud_backup_logs_reference (backup_reference),
    INDEX idx_cloud_backup_logs_status (backup_status),
    INDEX idx_cloud_backup_logs_started_at (backup_started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
