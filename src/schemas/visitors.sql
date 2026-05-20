CREATE TABLE IF NOT EXISTS visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id VARCHAR(30) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    other_names VARCHAR(100) NULL,
    gender VARCHAR(10) NOT NULL,
    date_of_birth DATE NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    national_id VARCHAR(50) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(120) NULL,
    address TEXT NOT NULL,
    relationship_to_inmate VARCHAR(40) NOT NULL,
    occupation VARCHAR(100) NULL,
    photo VARCHAR(255) NULL,
    biometric_id VARCHAR(100) NULL,
    blacklist_status BOOLEAN NOT NULL DEFAULT FALSE,
    blacklist_reason TEXT NULL,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitors_created_by
        FOREIGN KEY (created_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_visitors_relationship CHECK (relationship_to_inmate IN ('parent', 'spouse', 'sibling', 'child', 'lawyer', 'religious_representative', 'friend', 'guardian', 'other')),
    CONSTRAINT chk_visitors_verification_status CHECK (verification_status IN ('VERIFIED', 'PENDING', 'FAILED')),
    INDEX idx_visitors_visitor_id (visitor_id),
    INDEX idx_visitors_national_id (national_id),
    INDEX idx_visitors_phone (phone),
    INDEX idx_visitors_blacklist_status (blacklist_status),
    INDEX idx_visitors_verification_status (verification_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id INT NOT NULL,
    inmate_id INT NOT NULL,
    requested_visit_date DATE NOT NULL,
    requested_time_slot VARCHAR(50) NOT NULL,
    purpose_of_visit TEXT NOT NULL,
    visit_type VARCHAR(20) NOT NULL,
    approval_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    reviewed_by INT NULL,
    review_notes TEXT NULL,
    approved_date DATE NULL,
    rescheduled_date DATE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitor_requests_visitor_id
        FOREIGN KEY (visitor_id) REFERENCES visitors(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_requests_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_requests_reviewed_by
        FOREIGN KEY (reviewed_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_visitor_requests_approval_status CHECK (approval_status IN ('PENDING', 'APPROVED', 'REJECTED', 'RESCHEDULED', 'UNDER_REVIEW')),
    CONSTRAINT chk_visitor_requests_visit_type CHECK (visit_type IN ('FAMILY', 'LEGAL', 'RELIGIOUS', 'MEDICAL', 'OFFICIAL')),
    INDEX idx_visitor_requests_visitor_id (visitor_id),
    INDEX idx_visitor_requests_inmate_id (inmate_id),
    INDEX idx_visitor_requests_visit_date (requested_visit_date),
    INDEX idx_visitor_requests_status (approval_status),
    INDEX idx_visitor_requests_visit_type (visit_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id INT NOT NULL,
    national_id_verified BOOLEAN NOT NULL DEFAULT FALSE,
    biometric_verified BOOLEAN NOT NULL DEFAULT FALSE,
    blacklist_checked BOOLEAN NOT NULL DEFAULT FALSE,
    security_screening_status VARCHAR(20) NOT NULL,
    verification_notes TEXT NULL,
    verified_by INT NOT NULL,
    verification_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitor_verifications_visitor_id
        FOREIGN KEY (visitor_id) REFERENCES visitors(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_verifications_verified_by
        FOREIGN KEY (verified_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_visitor_verifications_security_status CHECK (security_screening_status IN ('CLEARED', 'FLAGGED', 'DENIED')),
    INDEX idx_visitor_verifications_visitor_id (visitor_id),
    INDEX idx_visitor_verifications_security_status (security_screening_status),
    INDEX idx_visitor_verifications_date (verification_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_request_id INT NOT NULL,
    visit_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    visit_duration_minutes INT NOT NULL,
    visit_room VARCHAR(80) NOT NULL,
    daily_capacity_slot INT NOT NULL,
    scheduling_status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    scheduled_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitor_schedules_request_id
        FOREIGN KEY (visitor_request_id) REFERENCES visitor_requests(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_schedules_scheduled_by
        FOREIGN KEY (scheduled_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_visitor_schedules_status CHECK (scheduling_status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'EXPIRED')),
    CONSTRAINT chk_visitor_schedules_time CHECK (end_time > start_time),
    CONSTRAINT chk_visitor_schedules_duration CHECK (visit_duration_minutes > 0),
    CONSTRAINT chk_visitor_schedules_capacity CHECK (daily_capacity_slot > 0),
    INDEX idx_visitor_schedules_request_id (visitor_request_id),
    INDEX idx_visitor_schedules_visit_date (visit_date),
    INDEX idx_visitor_schedules_room_time (visit_date, visit_room, start_time, end_time),
    INDEX idx_visitor_schedules_status (scheduling_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_checkins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_schedule_id INT NOT NULL,
    inmate_id INT NOT NULL,
    arrival_time DATETIME NOT NULL,
    exit_time DATETIME NULL,
    security_clearance_status VARCHAR(20) NOT NULL,
    belongings_checked BOOLEAN NOT NULL DEFAULT FALSE,
    handled_by INT NOT NULL,
    checkin_notes TEXT NULL,
    checkout_notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitor_checkins_schedule_id
        FOREIGN KEY (visitor_schedule_id) REFERENCES visitor_schedules(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_checkins_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_checkins_handled_by
        FOREIGN KEY (handled_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_visitor_checkins_security_status CHECK (security_clearance_status IN ('CLEARED', 'FLAGGED', 'DENIED')),
    CONSTRAINT chk_visitor_checkins_exit_time CHECK (exit_time IS NULL OR exit_time >= arrival_time),
    INDEX idx_visitor_checkins_schedule_id (visitor_schedule_id),
    INDEX idx_visitor_checkins_inmate_id (inmate_id),
    INDEX idx_visitor_checkins_arrival_time (arrival_time),
    INDEX idx_visitor_checkins_exit_time (exit_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_monitoring_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id INT NOT NULL,
    inmate_id INT NOT NULL,
    suspicious_activity TEXT NOT NULL,
    monitoring_level VARCHAR(20) NOT NULL,
    officer_notes TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    monitored_by INT NOT NULL,
    monitoring_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitor_monitoring_logs_visitor_id
        FOREIGN KEY (visitor_id) REFERENCES visitors(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_monitoring_logs_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_monitoring_logs_monitored_by
        FOREIGN KEY (monitored_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_visitor_monitoring_level CHECK (monitoring_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    INDEX idx_visitor_monitoring_logs_visitor_id (visitor_id),
    INDEX idx_visitor_monitoring_logs_inmate_id (inmate_id),
    INDEX idx_visitor_monitoring_logs_level (monitoring_level),
    INDEX idx_visitor_monitoring_logs_date (monitoring_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_violations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id INT NOT NULL,
    violation_type VARCHAR(80) NOT NULL,
    violation_description TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    violation_severity VARCHAR(20) NOT NULL,
    reported_by INT NOT NULL,
    violation_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitor_violations_visitor_id
        FOREIGN KEY (visitor_id) REFERENCES visitors(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visitor_violations_reported_by
        FOREIGN KEY (reported_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_visitor_violations_severity CHECK (violation_severity IN ('MINOR', 'MODERATE', 'MAJOR', 'CRITICAL')),
    INDEX idx_visitor_violations_visitor_id (visitor_id),
    INDEX idx_visitor_violations_type (violation_type),
    INDEX idx_visitor_violations_severity (violation_severity),
    INDEX idx_visitor_violations_date (violation_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
