CREATE TABLE IF NOT EXISTS inmate_medical_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL UNIQUE,
    blood_group VARCHAR(5) NULL,
    genotype VARCHAR(5) NULL,
    allergies TEXT NULL,
    chronic_illnesses TEXT NULL,
    disability_status VARCHAR(20) NOT NULL DEFAULT 'none',
    disability_description TEXT NULL,
    emergency_medical_notes TEXT NULL,
    current_medications TEXT NULL,
    primary_physician VARCHAR(100) NULL,
    created_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_medical_profiles_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_medical_profiles_created_by
        FOREIGN KEY (created_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_medical_profiles_blood_group CHECK (blood_group IS NULL OR blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    CONSTRAINT chk_medical_profiles_genotype CHECK (genotype IS NULL OR genotype IN ('AA', 'AS', 'SS', 'AC', 'SC')),
    CONSTRAINT chk_medical_profiles_disability_status CHECK (disability_status IN ('none', 'temporary', 'permanent', 'unknown')),
    INDEX idx_medical_profiles_inmate_id (inmate_id),
    INDEX idx_medical_profiles_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS medical_screenings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    screening_date DATE NOT NULL,
    screening_type VARCHAR(30) NOT NULL,
    temperature DECIMAL(4,1) NULL,
    blood_pressure VARCHAR(20) NULL,
    weight_kg DECIMAL(5,1) NULL,
    height_cm DECIMAL(5,1) NULL,
    infectious_disease_status VARCHAR(30) NOT NULL,
    malaria_status VARCHAR(30) NOT NULL,
    drug_test_status VARCHAR(30) NOT NULL,
    mental_health_status VARCHAR(30) NOT NULL,
    screening_notes TEXT NULL,
    screened_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_medical_screenings_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_medical_screenings_screened_by
        FOREIGN KEY (screened_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_medical_screenings_type CHECK (screening_type IN ('admission', 'periodic', 'emergency', 'referral', 'release')),
    CONSTRAINT chk_medical_screenings_temperature CHECK (temperature IS NULL OR (temperature >= 30.0 AND temperature <= 45.0)),
    CONSTRAINT chk_medical_screenings_weight CHECK (weight_kg IS NULL OR (weight_kg >= 20.0 AND weight_kg <= 300.0)),
    CONSTRAINT chk_medical_screenings_height CHECK (height_cm IS NULL OR (height_cm >= 80.0 AND height_cm <= 250.0)),
    CONSTRAINT chk_medical_screenings_infectious CHECK (infectious_disease_status IN ('none', 'suspected', 'confirmed', 'under_treatment', 'recovered')),
    CONSTRAINT chk_medical_screenings_malaria CHECK (malaria_status IN ('not_tested', 'negative', 'positive', 'treated')),
    CONSTRAINT chk_medical_screenings_drug CHECK (drug_test_status IN ('not_tested', 'negative', 'positive', 'inconclusive')),
    CONSTRAINT chk_medical_screenings_mental CHECK (mental_health_status IN ('stable', 'monitoring_required', 'urgent_review', 'referred')),
    INDEX idx_medical_screenings_inmate_id (inmate_id),
    INDEX idx_medical_screenings_date (screening_date),
    INDEX idx_medical_screenings_type (screening_type),
    INDEX idx_medical_screenings_infectious (infectious_disease_status),
    INDEX idx_medical_screenings_malaria (malaria_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS diagnoses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    diagnosis_name VARCHAR(150) NOT NULL,
    diagnosis_type VARCHAR(40) NOT NULL,
    diagnosis_date DATE NOT NULL,
    severity_level VARCHAR(20) NOT NULL,
    diagnosis_notes TEXT NULL,
    diagnosed_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_diagnoses_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_diagnoses_diagnosed_by
        FOREIGN KEY (diagnosed_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_diagnoses_type CHECK (diagnosis_type IN ('acute', 'chronic', 'infectious', 'injury', 'mental_health', 'other')),
    CONSTRAINT chk_diagnoses_severity CHECK (severity_level IN ('low', 'moderate', 'high', 'critical')),
    INDEX idx_diagnoses_inmate_id (inmate_id),
    INDEX idx_diagnoses_name (diagnosis_name),
    INDEX idx_diagnoses_type (diagnosis_type),
    INDEX idx_diagnoses_date (diagnosis_date),
    INDEX idx_diagnoses_severity (severity_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS treatment_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    diagnosis_id INT NOT NULL,
    treatment_plan TEXT NOT NULL,
    treatment_start_date DATE NOT NULL,
    treatment_end_date DATE NULL,
    treatment_status VARCHAR(30) NOT NULL,
    attending_medical_officer INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_treatment_plans_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_treatment_plans_diagnosis_id
        FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_treatment_plans_officer
        FOREIGN KEY (attending_medical_officer) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_treatment_plans_status CHECK (treatment_status IN ('planned', 'active', 'completed', 'cancelled', 'referred')),
    CONSTRAINT chk_treatment_plans_dates CHECK (treatment_end_date IS NULL OR treatment_end_date >= treatment_start_date),
    INDEX idx_treatment_plans_inmate_id (inmate_id),
    INDEX idx_treatment_plans_diagnosis_id (diagnosis_id),
    INDEX idx_treatment_plans_status (treatment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    medication_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(80) NOT NULL,
    frequency VARCHAR(80) NOT NULL,
    duration VARCHAR(80) NOT NULL,
    prescription_notes TEXT NULL,
    prescribed_by INT NOT NULL,
    prescribed_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_prescriptions_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_prescriptions_prescribed_by
        FOREIGN KEY (prescribed_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    INDEX idx_prescriptions_inmate_id (inmate_id),
    INDEX idx_prescriptions_medication_name (medication_name),
    INDEX idx_prescriptions_prescribed_date (prescribed_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS medication_administration_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    administered_by INT NOT NULL,
    administration_time DATETIME NOT NULL,
    administration_notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_med_admin_logs_prescription_id
        FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_med_admin_logs_administered_by
        FOREIGN KEY (administered_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    INDEX idx_med_admin_logs_prescription_id (prescription_id),
    INDEX idx_med_admin_logs_administered_by (administered_by),
    INDEX idx_med_admin_logs_time (administration_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS medical_appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    appointment_type VARCHAR(40) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    facility_name VARCHAR(150) NOT NULL,
    doctor_name VARCHAR(100) NULL,
    referral_status VARCHAR(30) NOT NULL,
    appointment_status VARCHAR(30) NOT NULL,
    emergency_case BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT NULL,
    created_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_medical_appointments_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_medical_appointments_created_by
        FOREIGN KEY (created_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_medical_appointments_type CHECK (appointment_type IN ('infirmary', 'prison_hospital_referral', 'external_referral', 'emergency')),
    CONSTRAINT chk_medical_appointments_referral CHECK (referral_status IN ('not_required', 'pending', 'approved', 'completed', 'cancelled')),
    CONSTRAINT chk_medical_appointments_status CHECK (appointment_status IN ('scheduled', 'completed', 'missed', 'cancelled', 'referred')),
    INDEX idx_medical_appointments_inmate_id (inmate_id),
    INDEX idx_medical_appointments_date (appointment_date),
    INDEX idx_medical_appointments_type (appointment_type),
    INDEX idx_medical_appointments_referral (referral_status),
    INDEX idx_medical_appointments_status (appointment_status),
    INDEX idx_medical_appointments_emergency (emergency_case)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS mental_health_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inmate_id INT NOT NULL,
    psychological_assessment TEXT NOT NULL,
    counseling_notes TEXT NULL,
    suicide_risk_level VARCHAR(20) NOT NULL,
    behavioral_observations TEXT NULL,
    assessed_by INT NOT NULL,
    assessment_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_mental_health_records_inmate_id
        FOREIGN KEY (inmate_id) REFERENCES inmates(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_mental_health_records_assessed_by
        FOREIGN KEY (assessed_by) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_mental_health_suicide_risk CHECK (suicide_risk_level IN ('low', 'moderate', 'high', 'critical')),
    INDEX idx_mental_health_records_inmate_id (inmate_id),
    INDEX idx_mental_health_records_risk (suicide_risk_level),
    INDEX idx_mental_health_records_date (assessment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
