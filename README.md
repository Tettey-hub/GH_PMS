# Prison Management System API

Flask API foundation for the Ghana Prison Service prison management system.

## Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Replace every placeholder in `.env` with local or deployment values.
5. Run the database connection check:

```powershell
python scripts\test_db.py
```

## Configuration

Application settings are loaded from environment variables, authorize_roles in `src/config/settings.py`.
Database connections are configured in `src/config/database_config.py` and use a lazy MySQL connection pool sized by `DB_POOL_SIZE`.

The real `.env` file must stay local and must not be committed.

## Add Admin JSON Payload

Endpoint: `POST /api/v1/auth/register`

Requires an authenticated `admin` or `supervisor` access token with `users_create` permission.

```json
{
  "officer_id": "OFF001",
  "first_name": "FirstName",
  "middle_name": "MiddleName",
  "last_name": "LastName",
  "gender": "male",
  "dob": "1990-01-01",
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "phone": "+233000000000",
  "national_id": "GHA-000000000-0",
  "address": "Residential address",
  "profile_image": "profile-image-path-or-url",
  "staff_id": "STAFF001",
  "badge_number": "BADGE001",
  "rank": "Officer title",
  "department": "Administration",
  "position": "Officer title",
  "employment_date": "2026-05-14",
  "branch": "Branch or facility name",
  "username": "username",
  "role": "admin",
  "status": "active",
  "shift": "morning",
  "date_joined": "2026-05-14"
}
```

Allowed values:

- `gender`: `male`, `female`
- `role`: `admin`, `officer`, `supervisor`, `medical_officer`, `records_officer`, `visitor_officer`
- `status`: `active`, `inactive`
- `shift`: `morning`, `afternoon`, `night`

## Login

Endpoint: `POST /api/v1/auth/login` (Accepts `email` or `username` for authentication)

### Login with Email

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

Or:

```json
{
  "username": "username",
  "password": "StrongPassword123!"
}
```

### Login with Identifier (Email or Username)

```json
{
  "identifier": "user@example.com",
  "password": "StrongPassword123!"
}
```

```json
{
  "identifier": "username",
  "password": "StrongPassword123!"
}
```

## Implementation Update Report

This report records the PMS updates completed so far in this phase.

### API Modules Added Or Updated

- User DTO validation was added for registration, login, and staff updates.
- Inmate Management was implemented with model, DTO, repository, service, controller, routes, schema, validations, search, status updates, release approval, transfer approval, and delete support.
- Inmate Transfer Management was implemented with professional workflow stages for request, review, legal verification, security assessment, medical clearance, transport assignment, movement authorization, execution, receiving confirmation, completion, cancellation, history, search, and reports.
- Inmate Release Management was implemented with lawful release workflow stages for eligibility review, legal verification, sentence validation, medical clearance, property clearance, identity verification, approval/rejection, document references, release execution, history, search, and reports.
- Arrest Warrant Management was implemented with model, DTO, repository, service, controller, routes, schema, validations, list, search, get, update, status update, and delete support.
- Medical and Health Management was implemented with medical entities, DTO validation, repository, service, controller, routes, schema, role-restricted APIs, audit logging, appointment/referral support, medication administration tracking, mental health records, inmate medical history, treatment history, and medical reports.
- Visitor Management was implemented with visitor entities, DTO validation, repository, service, controller, routes, schema, role-restricted APIs, audit logging, identity verification, blacklist checks, visit request approval workflow, visit scheduling, security screening, check-in/check-out tracking, monitoring logs, violation tracking, visitor history, search, and visitor reports.
- External Integration Management was implemented with court, NIA/Ghana Card, police database, biometric, API gateway, synchronization, and cloud backup integration records using a provider-independent adapter layer, secure audit logging, encrypted sensitive fields, HTTPS validation, optional signed requests, IP allowlisting, and retry-safe synchronization logging.
- Rehabilitation and Reintegration Management was implemented with vocational training enrollment, counseling sessions, behavioral assessments, religious participation, work assignments, skill certifications, post-release follow-up tracking, inmate rehabilitation history, reports, validation, role-restricted APIs, and audit logging.
- `scripts/create_tables.py` was updated so `arrest_warrants` is created before `inmates`.
- `scripts/create_tables.py` was updated to create the medical tables after `users` and `inmates`.
- `scripts/create_tables.py` was updated to create visitor tables after `users` and `inmates`.
- `scripts/create_tables.py` was updated to create external integration tables after `users`, `inmates`, and `visitors`.
- `scripts/create_tables.py` was updated to create rehabilitation tables after `users` and `inmates`.
- `main.py` registers the inmate, arrest warrant, medical, visitor, external integration, and rehabilitation APIs under `/api/v1`.

### Interactive Test Menu Updates

The admin tester in `scripts/test_auth.py` now includes:

- Manage Users
- Inmate Management
- Manage Warrant
- Court and Sentence Management
- Medical Management
- Visitor Management
- Housing and Movement Management
- Rehabilitation Management
- Notifications
- Reporting and Analytics
- System Administration

### Manage Warrant Test Menu

The warrant test menu now contains only warrant-related options:

- View all warrants
- View warrant by
- Edit Warrant
- Delete warrant
- Back

`View all warrants` supports skip, female, and male filtering. `View warrant by` supports gender selection followed by warrant status or sentence type filtering. The warrant table includes a `Status` column.

Valid warrant status filters:

- `pending`
- `executed`
- `cancelled`

Valid warrant sentence type filters:

- `remand`
- `convicted`
- `life`
- `death`

### Medical Management Test Menu

Medical Management now manages inmate health records and healthcare services using the real `/api/v1/medical/*` API routes.

Implemented medical tester sections:

- Medical Registration
- Medical Screening
- Treatment Management
- Medication Management
- Appointment Scheduling
- Mental Health Management
- Medical Reports

### Visitor Management

Visitor Management manages visitor registration, identity verification, visit requests, approvals, scheduling, check-in/check-out, monitoring, violations, blacklist handling, and visitor reports using the real `/api/v1/visitors/*` API routes.

### Rehabilitation Management

Rehabilitation Management manages inmate skill development, counseling, behavior tracking, religious participation, work assignments, certifications, post-release follow-up, inmate rehabilitation history, and rehabilitation reports using the real `/api/v1/rehabilitation/*` API routes.

Implemented rehabilitation tester sections:

- Vocational Training Registration
- Counseling Sessions
- Behavioral Improvement Tracking
- Religious Participation
- Work Assignments
- Skill Certification
- Post-Release Follow-up
- Rehabilitation Reports

### Implemented And Remaining Grouped Menus

Medical Management is now implemented.

Visitor Management is now implemented.

Rehabilitation Management is now implemented.

Housing and Movement Management now includes grouped sections for block management, cell management, bed allocation, inmate housing, occupancy monitoring, special housing, and housing reports.

Notifications includes email alerts, visit reminders, court reminders, medical alerts, security alerts, transfer alerts, and emergency notifications.

External Integration Management is now implemented under `System Administration -> Configure system settings`, with court system integration, national ID integration, police database integration, biometric integration, API management, data synchronization, and cloud backup integration.

System Administration now keeps the external integration tester in `Configure system settings` with:

- Court system integration
- National ID integration
- Police database integration
- Biometric integration
- API management
- Data synchronization
- Cloud backup integration

## Arrest Warrant API JSON Inputs

Base path: `/api/v1/arrest-warrants`

### Create Arrest Warrant

Endpoint: `POST /api/v1/arrest-warrants`

```json
{
  "warrant_number": "WRT-2026-0001",
  "case_number": "CASE-2026-0001",
  "first_name": "FirstName",
  "last_name": "LastName",
  "other_names": "Other Names",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "nationality": "Ghanaian",
  "national_id": "GHA-000000000-0",
  "offense": "Offense name",
  "offense_description": "Offense description",
  "arrest_date": "2026-05-01",
  "arresting_officer": "Officer Name",
  "arresting_agency": "Police Service",
  "court": "Court Name",
  "judge": "Judge Name",
  "sentence_type": "remand",
  "sentence_duration": "6 months",
  "status": "pending",
  "issued_date": "2026-05-01"
}
```

Allowed values:

- `gender`: `male`, `female`
- `sentence_type`: `remand`, `convicted`, `life`, `death`
- `status`: `pending`, `executed`, `cancelled`

### Update Arrest Warrant

Endpoint: `PATCH /api/v1/arrest-warrants/{warrant_db_id}`

Send only fields that should change.

```json
{
  "court": "Updated Court Name",
  "judge": "Updated Judge Name",
  "sentence_type": "convicted",
  "sentence_duration": "2 years",
  "status": "executed"
}
```

### Update Arrest Warrant Status

Endpoint: `PATCH /api/v1/arrest-warrants/{warrant_db_id}/status`

```json
{
  "status": "executed"
}
```

### Warrant List Filters

Endpoint: `GET /api/v1/arrest-warrants`

Supported query fields include:

```json
{
  "gender": "female",
  "nationality": "Ghanaian",
  "arrest_date": "2026-05-01",
  "issued_date": "2026-05-01",
  "status": "pending",
  "sentence_type": "remand",
  "limit": 20,
  "offset": 0
}
```

## Medical And Health Management API JSON Inputs

Base path: `/api/v1/medical`

Medical endpoints require an authenticated `admin` or `medical_officer` access token with the required medical permission.

### Create Inmate Medical Profile

Endpoint: `POST /api/v1/medical/profiles`

```json
{
  "inmate_id": 1,
  "blood_group": "O+",
  "genotype": "AA",
  "allergies": "Penicillin allergy",
  "chronic_illnesses": "Asthma",
  "disability_status": "none",
  "disability_description": null,
  "emergency_medical_notes": "Requires inhaler access during asthma attacks",
  "current_medications": "Salbutamol inhaler",
  "primary_physician": "Dr. Medical Officer"
}
```

Allowed values:

- `blood_group`: `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`
- `genotype`: `AA`, `AS`, `SS`, `AC`, `SC`
- `disability_status`: `none`, `temporary`, `permanent`, `unknown`

### Update Inmate Medical Profile

Endpoint: `PATCH /api/v1/medical/profiles/{inmate_db_id}`

Send only fields that should change.

```json
{
  "allergies": "Penicillin and aspirin allergy",
  "chronic_illnesses": "Asthma, hypertension",
  "current_medications": "Salbutamol inhaler, amlodipine",
  "primary_physician": "Dr. Updated Medical Officer"
}
```

### Record Medical Screening

Endpoint: `POST /api/v1/medical/screenings`

```json
{
  "inmate_id": 1,
  "screening_date": "2026-05-19",
  "screening_type": "admission",
  "temperature": "36.8",
  "blood_pressure": "120/80",
  "weight_kg": "72.4",
  "height_cm": "175.5",
  "infectious_disease_status": "none",
  "malaria_status": "negative",
  "drug_test_status": "negative",
  "mental_health_status": "stable",
  "screening_notes": "Admission screening completed"
}
```

Allowed values:

- `screening_type`: `admission`, `periodic`, `emergency`, `referral`, `release`
- `infectious_disease_status`: `none`, `suspected`, `confirmed`, `under_treatment`, `recovered`
- `malaria_status`: `not_tested`, `negative`, `positive`, `treated`
- `drug_test_status`: `not_tested`, `negative`, `positive`, `inconclusive`
- `mental_health_status`: `stable`, `monitoring_required`, `urgent_review`, `referred`

### Create Diagnosis

Endpoint: `POST /api/v1/medical/diagnoses`

```json
{
  "inmate_id": 1,
  "diagnosis_name": "Uncomplicated malaria",
  "diagnosis_type": "infectious",
  "diagnosis_date": "2026-05-19",
  "severity_level": "moderate",
  "diagnosis_notes": "Positive malaria test with fever and headache"
}
```

Allowed values:

- `diagnosis_type`: `acute`, `chronic`, `infectious`, `injury`, `mental_health`, `other`
- `severity_level`: `low`, `moderate`, `high`, `critical`

### Create Treatment Plan

Endpoint: `POST /api/v1/medical/treatment-plans`

```json
{
  "inmate_id": 1,
  "diagnosis_id": 1,
  "treatment_plan": "Start antimalarial treatment and monitor temperature twice daily",
  "treatment_start_date": "2026-05-19",
  "treatment_end_date": "2026-05-26",
  "treatment_status": "active"
}
```

Allowed values:

- `treatment_status`: `planned`, `active`, `completed`, `cancelled`, `referred`

### Create Prescription

Endpoint: `POST /api/v1/medical/prescriptions`

```json
{
  "inmate_id": 1,
  "medication_name": "Artemether lumefantrine",
  "dosage": "20/120mg",
  "frequency": "Twice daily",
  "duration": "3 days",
  "prescription_notes": "Administer after meals",
  "prescribed_date": "2026-05-19"
}
```

### Record Medication Administration

Endpoint: `POST /api/v1/medical/medication-administrations`

```json
{
  "prescription_id": 1,
  "administration_time": "2026-05-19T08:30:00",
  "administration_notes": "Dose administered after breakfast"
}
```

### Schedule Medical Appointment Or Referral

Endpoint: `POST /api/v1/medical/appointments`

```json
{
  "inmate_id": 1,
  "appointment_type": "external_referral",
  "appointment_date": "2026-05-20",
  "appointment_time": "10:00",
  "facility_name": "Korle Bu Teaching Hospital",
  "doctor_name": "Specialist Doctor",
  "referral_status": "pending",
  "appointment_status": "scheduled",
  "emergency_case": false,
  "notes": "Specialist review requested"
}
```

Allowed values:

- `appointment_type`: `infirmary`, `prison_hospital_referral`, `external_referral`, `emergency`
- `referral_status`: `not_required`, `pending`, `approved`, `completed`, `cancelled`
- `appointment_status`: `scheduled`, `completed`, `missed`, `cancelled`, `referred`

Referral facilities are configured with `MEDICAL_REFERRAL_FACILITIES` in the environment. Current example facilities are Nsawam Prison Hospital, Korle Bu Teaching Hospital, and Komfo Anokye Teaching Hospital.

### Create Mental Health Record

Endpoint: `POST /api/v1/medical/mental-health-records`

```json
{
  "inmate_id": 1,
  "psychological_assessment": "Initial assessment completed; inmate is calm and oriented",
  "counseling_notes": "Follow-up counseling recommended in two weeks",
  "suicide_risk_level": "low",
  "behavioral_observations": "No immediate risk indicators observed",
  "assessment_date": "2026-05-19"
}
```

Allowed values:

- `suicide_risk_level`: `low`, `moderate`, `high`, `critical`

### Retrieve Inmate Medical History

Endpoint: `GET /api/v1/medical/inmates/{inmate_db_id}/history`

Returns:

```json
{
  "profile": {},
  "screenings": [],
  "diagnoses": [],
  "treatment_plans": [],
  "prescriptions": [],
  "medication_administration_logs": [],
  "appointments": [],
  "mental_health_records": []
}
```

### Retrieve Inmate Treatment History

Endpoint: `GET /api/v1/medical/inmates/{inmate_db_id}/treatments`

Returns diagnoses, treatment plans, prescriptions, and medication administration logs for the inmate.

### Generate Medical Reports

Endpoint: `GET /api/v1/medical/reports`

Report sections:

- `disease_outbreak_monitoring`
- `medication_reports`
- `appointment_reports`
- `chronic_illness_statistics`
- `mental_health_monitoring`
- `treatment_progress_reports`

### List Referral Facilities

Endpoint: `GET /api/v1/medical/referral-facilities`

```json
{
  "referral_facilities": [
    "Nsawam Prison Hospital",
    "Korle Bu Teaching Hospital",
    "Komfo Anokye Teaching Hospital"
  ]
}
```

## Visitor Management API JSON Inputs

Base path: `/api/v1/visitors`

Visitor endpoints require an authenticated `admin`, `visitor_officer`, or authorized security `officer` access token with the required visits permission.

### Register Visitor

Endpoint: `POST /api/v1/visitors`

```json
{
  "visitor_id": "VIS-2026-0001",
  "first_name": "FirstName",
  "last_name": "LastName",
  "other_names": "Other Names",
  "gender": "female",
  "date_of_birth": "1985-01-01",
  "nationality": "Ghanaian",
  "national_id": "GHA-000000000-0",
  "phone": "+233000000000",
  "email": "visitor@example.com",
  "address": "Residential address",
  "relationship_to_inmate": "parent",
  "occupation": "Trader",
  "photo": "uploads/visitors/visitor-photo.jpg",
  "biometric_id": "BIO-VIS-2026-0001"
}
```

Allowed values:

- `relationship_to_inmate`: `parent`, `spouse`, `sibling`, `child`, `lawyer`, `religious_representative`, `friend`, `guardian`, `other`

### Update Visitor Profile

Endpoint: `PATCH /api/v1/visitors/{visitor_db_id}`

Send only fields that should change.

```json
{
  "phone": "+233000000001",
  "address": "Updated residential address",
  "relationship_to_inmate": "guardian",
  "occupation": "Teacher"
}
```

### Verify Visitor Identity

Endpoint: `POST /api/v1/visitors/verifications`

```json
{
  "visitor_id": 1,
  "national_id_verified": true,
  "biometric_verified": true,
  "blacklist_checked": true,
  "security_screening_status": "CLEARED",
  "verification_notes": "National ID, biometric record, and blacklist screening completed",
  "verification_date": "2026-05-19"
}
```

Allowed values:

- `security_screening_status`: `CLEARED`, `FLAGGED`, `DENIED`

### Submit Visit Request

Endpoint: `POST /api/v1/visitors/requests`

```json
{
  "visitor_id": 1,
  "inmate_id": 1,
  "requested_visit_date": "2026-05-20",
  "requested_time_slot": "09:00-09:30",
  "purpose_of_visit": "Family welfare visit",
  "visit_type": "FAMILY"
}
```

Allowed values:

- `visit_type`: `FAMILY`, `LEGAL`, `RELIGIOUS`, `MEDICAL`, `OFFICIAL`

### Review Visit Request

Endpoint: `PATCH /api/v1/visitors/requests/{request_id}/review`

```json
{
  "review_notes": "Request placed under review pending final security clearance"
}
```

### Approve Visit Request

Endpoint: `PATCH /api/v1/visitors/requests/{request_id}/approve`

```json
{
  "approved_date": "2026-05-19",
  "review_notes": "Visitor verification completed and request approved"
}
```

Approval requires completed visitor verification and a non-blacklisted visitor.

### Reject Visit Request

Endpoint: `PATCH /api/v1/visitors/requests/{request_id}/reject`

```json
{
  "review_notes": "Visit request rejected because visitor verification failed"
}
```

Rejected requests require `review_notes`.

### Reschedule Visit Request

Endpoint: `PATCH /api/v1/visitors/requests/{request_id}/reschedule`

```json
{
  "rescheduled_date": "2026-05-22",
  "review_notes": "Original requested slot is unavailable"
}
```

### Create Visit Schedule

Endpoint: `POST /api/v1/visitors/schedules`

```json
{
  "visitor_request_id": 1,
  "visit_date": "2026-05-20",
  "start_time": "09:00",
  "end_time": "09:30",
  "visit_duration_minutes": 30,
  "visit_room": "Visit Room A",
  "daily_capacity_slot": 1
}
```

Scheduling requires an approved visit request. Overlapping room schedules and duplicate daily capacity slots are rejected.

### Check In Visitor

Endpoint: `POST /api/v1/visitors/checkins`

```json
{
  "visitor_schedule_id": 1,
  "inmate_id": 1,
  "arrival_time": "2026-05-20T08:55:00",
  "security_clearance_status": "CLEARED",
  "belongings_checked": true,
  "checkin_notes": "Visitor cleared at main gate"
}
```

Check-in requires a scheduled visit, matching inmate, cleared security screening, and completed belongings inspection.

### Check Out Visitor

Endpoint: `PATCH /api/v1/visitors/checkins/{checkin_id}/checkout`

```json
{
  "exit_time": "2026-05-20T09:35:00",
  "checkout_notes": "Visitor exited without incident"
}
```

`exit_time` cannot be earlier than `arrival_time`.

### Monitor Visitor Activity

Endpoint: `POST /api/v1/visitors/monitoring`

```json
{
  "visitor_id": 1,
  "inmate_id": 1,
  "suspicious_activity": "Repeated attempts to discuss restricted information",
  "monitoring_level": "HIGH",
  "officer_notes": "Conversation was redirected and logged",
  "action_taken": "Continued monitoring recommended",
  "monitoring_date": "2026-05-20"
}
```

Allowed values:

- `monitoring_level`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

### Record Visitor Violation

Endpoint: `POST /api/v1/visitors/violations`

```json
{
  "visitor_id": 1,
  "violation_type": "Contraband attempt",
  "violation_description": "Visitor attempted to bring prohibited items into the facility",
  "action_taken": "Visit terminated and incident escalated",
  "violation_severity": "CRITICAL",
  "violation_date": "2026-05-20"
}
```

Allowed values:

- `violation_severity`: `MINOR`, `MODERATE`, `MAJOR`, `CRITICAL`

Critical violations automatically mark the visitor as blacklisted.

### Blacklist Visitor

Endpoint: `PATCH /api/v1/visitors/{visitor_db_id}/blacklist`

```json
{
  "blacklist_reason": "Security violation confirmed after review"
}
```

### Retrieve Visitor History

Endpoint: `GET /api/v1/visitors/{visitor_db_id}/history`

Returns visitor profile, visit requests, verifications, monitoring logs, and violations.

### Search Visitors

Endpoint: `GET /api/v1/visitors`

Supported query fields include:

```json
{
  "q": "VIS-2026-0001",
  "relationship_to_inmate": "parent",
  "verification_status": "VERIFIED",
  "blacklist_status": false,
  "limit": 20,
  "offset": 0
}
```

### Generate Visitor Reports

Endpoint: `GET /api/v1/visitors/reports`

Report sections:

- `daily_visitor_reports`
- `visitor_violation_reports`
- `suspicious_visitor_reports`
- `blacklist_reports`
- `visitation_frequency_reports`
- `inmate_visitation_reports`

## Rehabilitation And Reintegration API JSON Inputs

Base path: `/api/v1/rehabilitation`

Rehabilitation endpoints require an authenticated `admin`, `rehabilitation_officer`, `counselor`, or authorized prison `officer` access token with the required records permission. Prison officers have limited read access through the protected history and report endpoints.

### Enroll Inmate In Vocational Program

Endpoint: `POST /api/v1/rehabilitation/vocational-training`

```json
{
  "inmate_id": 1,
  "program_name": "Carpentry",
  "skill_category": "Furniture making",
  "training_center": "Facility Vocational Workshop",
  "instructor_name": "Instructor Name",
  "enrollment_date": "2026-05-20",
  "completion_status": "ENROLLED",
  "progress_percentage": 0,
  "assessment_score": null,
  "certification_eligible": false
}
```

Allowed values:

- `program_name`: `Carpentry`, `Welding`, `Tailoring`, `Agriculture`, `ICT Training`, `Plumbing`, `Electrical Installation`, `Art & Craft`
- `completion_status`: `ENROLLED`, `IN_PROGRESS`, `COMPLETED`, `WITHDRAWN`

Active duplicate enrollment for the same inmate and vocational program is rejected.

### Schedule Counseling Session

Endpoint: `POST /api/v1/rehabilitation/counseling-sessions`

```json
{
  "inmate_id": 1,
  "counselor_name": "Counselor Name",
  "session_type": "Individual Counseling",
  "session_date": "2026-05-20",
  "session_notes": "Initial rehabilitation counseling session completed",
  "behavioral_observation": "Inmate was cooperative and engaged",
  "risk_level": "LOW",
  "follow_up_required": true
}
```

Allowed values:

- `session_type`: `Individual Counseling`, `Group Therapy`, `Trauma Counseling`, `Addiction Recovery`, `Anger Management`
- `risk_level`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

### Record Behavioral Assessment

Endpoint: `POST /api/v1/rehabilitation/behavioral-assessments`

```json
{
  "inmate_id": 1,
  "behavior_score": 82,
  "behavior_category": "Excellent",
  "observation_notes": "Consistent positive behavior and active participation in programs",
  "incident_count": 0,
  "improvement_level": "Significant improvement",
  "assessment_date": "2026-05-20"
}
```

Allowed values:

- `behavior_category`: `Excellent`, `Good`, `Fair`, `Poor`, `Violent`

Behavior scores must be between `0` and `100` and must be consistent with the selected behavior category.

### Assign Religious Participation Activity

Endpoint: `POST /api/v1/rehabilitation/religious-participation`

```json
{
  "inmate_id": 1,
  "religion": "Christianity",
  "activity_type": "Bible Study",
  "participation_date": "2026-05-20",
  "attendance_status": "ATTENDED",
  "religious_leader": "Religious Leader Name",
  "notes": "Participated actively during the session"
}
```

Allowed values:

- `activity_type`: `Church Service`, `Islamic Prayer Session`, `Bible Study`, `Quran Study`, `Spiritual Counseling`
- `attendance_status`: `REGISTERED`, `ATTENDED`, `MISSED`

### Assign Work Duties

Endpoint: `POST /api/v1/rehabilitation/work-assignments`

```json
{
  "inmate_id": 1,
  "work_type": "Farming",
  "assignment_location": "Facility farm",
  "supervisor_name": "Supervisor Name",
  "start_date": "2026-05-20",
  "end_date": null,
  "performance_rating": 75,
  "attendance_record": "Present for assigned duties during the assessment period"
}
```

Allowed values:

- `work_type`: `Kitchen Duties`, `Farming`, `Cleaning Services`, `Maintenance Work`, `Construction Assistance`

`end_date` cannot be earlier than `start_date`, and `performance_rating` must be between `0` and `100` when supplied.

### Issue Skill Certification

Endpoint: `POST /api/v1/rehabilitation/skill-certifications`

```json
{
  "inmate_id": 1,
  "certification_name": "Carpentry Skills Certificate",
  "skill_area": "Carpentry",
  "issuing_authority": "Facility Training Authority",
  "issue_date": "2026-05-20",
  "certificate_number": "CERT-REHAB-2026-0001",
  "grade": "Basic",
  "validity_status": "VALID"
}
```

Allowed values:

- `grade`: `Basic`, `Intermediate`, `Advanced`, `Professional`
- `validity_status`: `VALID`, `EXPIRED`, `REVOKED`

`certificate_number` must be unique.

### Track Post-Release Follow-up

Endpoint: `POST /api/v1/rehabilitation/post-release-followups`

```json
{
  "inmate_id": 1,
  "release_date": "2026-05-20",
  "follow_up_date": "2026-06-20",
  "employment_status": "Apprenticeship placement secured",
  "housing_status": "Returned to verified family residence",
  "reintegration_score": 78,
  "recidivism_risk_level": "LOW",
  "notes": "First follow-up completed with positive reintegration indicators"
}
```

Allowed values:

- `recidivism_risk_level`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

`follow_up_date` cannot be earlier than `release_date`, and `reintegration_score` must be between `0` and `100`.

### Retrieve Inmate Rehabilitation History

Endpoint: `GET /api/v1/rehabilitation/inmates/{inmate_db_id}/history`

Returns:

```json
{
  "vocational_training": [],
  "counseling_sessions": [],
  "behavioral_assessments": [],
  "religious_participations": [],
  "work_assignments": [],
  "skill_certifications": [],
  "post_release_followups": []
}
```

### Generate Rehabilitation Reports

Endpoint: `GET /api/v1/rehabilitation/reports`

Report sections:

- `inmate_rehabilitation_progress_report`
- `vocational_training_performance_report`
- `counseling_effectiveness_report`
- `behavioral_improvement_report`
- `work_assignment_productivity_report`
- `post_release_reintegration_report`

## External Integration API JSON Inputs

Base path: `/api/v1/external-integrations`

External integration endpoints require an authenticated `admin` or `supervisor` access token with the required records permission. In the interactive tester, these workflows are located at `System Administration -> Configure system settings`.

Sensitive integration fields are encrypted before storage and redacted in API responses. External API endpoint references must use HTTPS. Provider operation calls fail closed unless a real provider adapter is configured.

Security-related environment options:

- `EXTERNAL_INTEGRATION_ENCRYPTION_KEY`: optional urlsafe base64 encoded 32-byte key for encryption. If omitted, the app secret is used as fallback key material.
- `EXTERNAL_INTEGRATION_HASH_KEY`: optional key material for response redaction hashes.
- `EXTERNAL_INTEGRATION_ALLOWED_IPS`: optional comma-separated source IP allowlist.
- `EXTERNAL_INTEGRATION_REQUIRE_SIGNATURE`: set to `true` to require signed integration requests.
- `EXTERNAL_INTEGRATION_REQUEST_SIGNING_SECRET`: shared HMAC secret for signed requests.

When request signing is enabled, write requests must include:

- `X-Integration-Signature`
- `X-Integration-Timestamp`
- `X-Integration-Nonce`

Signature message format:

```text
{timestamp}.{nonce}.{raw_request_body}
```

Signature algorithm:

```text
HMAC-SHA256
```

### Court System Integration

Endpoint: `POST /api/v1/external-integrations/court`

```json
{
  "inmate_id": 1,
  "external_case_reference": "ECMS-CASE-2026-0001",
  "court_name": "Accra High Court",
  "court_api_source": "https://court-api.example.gov.gh/ecms",
  "warrant_status": "VERIFIED",
  "hearing_date": "2026-05-25T09:30:00",
  "hearing_status": "SCHEDULED",
  "sentence_status": "CONFIRMED",
  "synchronization_status": "SYNCED",
  "last_synced_at": "2026-05-20T10:00:00"
}
```

Allowed values:

- `warrant_status`: `PENDING`, `VERIFIED`, `INVALID`, `EXPIRED`, `REVOKED`
- `hearing_status`: `PENDING`, `SCHEDULED`, `COMPLETED`, `ADJOURNED`, `CANCELLED`
- `sentence_status`: `PENDING`, `CONFIRMED`, `MODIFIED`, `BAIL_APPROVED`, `ACQUITTED`, `RELEASE_AUTHORIZED`
- `synchronization_status`: `PENDING`, `IN_PROGRESS`, `SYNCED`, `FAILED`, `RETRY_SCHEDULED`

### National ID Integration

Endpoint: `POST /api/v1/external-integrations/nia`

```json
{
  "inmate_id": 1,
  "national_id": "GHA-000000000-0",
  "verification_status": "VERIFIED",
  "biometric_match_status": "MATCHED",
  "demographic_sync_status": "SYNCED",
  "nia_reference_number": "NIA-REF-2026-0001",
  "last_verified_at": "2026-05-20T10:15:00"
}
```

Allowed values:

- `verification_status`: `PENDING`, `VERIFIED`, `FAILED`, `RETRY_SCHEDULED`
- `biometric_match_status`: `PENDING`, `MATCHED`, `NOT_MATCHED`, `NOT_AVAILABLE`
- `demographic_sync_status`: `PENDING`, `SYNCED`, `FAILED`, `NOT_REQUESTED`

### Police Database Integration

Endpoint: `POST /api/v1/external-integrations/police`

```json
{
  "inmate_id": 1,
  "police_reference_number": "GPS-CID-2026-0001",
  "criminal_record_status": "FOUND",
  "fingerprint_match_status": "MATCHED",
  "recidivism_status": "REPEAT_OFFENDER",
  "wanted_person_status": "CLEAR",
  "intelligence_notes": "Criminal history synchronized from authorized police source",
  "synchronization_status": "SYNCED",
  "last_synced_at": "2026-05-20T10:30:00"
}
```

Allowed values:

- `criminal_record_status`: `PENDING`, `FOUND`, `NOT_FOUND`, `FAILED`
- `fingerprint_match_status`: `PENDING`, `MATCHED`, `NOT_MATCHED`, `NOT_AVAILABLE`
- `recidivism_status`: `PENDING`, `REPEAT_OFFENDER`, `NO_MATCH`, `UNKNOWN`
- `wanted_person_status`: `PENDING`, `MATCHED`, `CLEAR`, `UNKNOWN`

### Biometric Integration

Endpoint: `POST /api/v1/external-integrations/biometrics`

Exactly one subject must be supplied: `inmate_id`, `visitor_id`, or `staff_id`.

```json
{
  "inmate_id": 1,
  "biometric_type": "FINGERPRINT",
  "biometric_reference_id": "BIO-INM-2026-0001",
  "enrollment_status": "ENROLLED",
  "verification_status": "VERIFIED",
  "captured_device": "Fingerprint scanner terminal",
  "captured_at": "2026-05-20T10:45:00"
}
```

Allowed values:

- `biometric_type`: `FINGERPRINT`, `FACIAL`, `WEBCAM`, `TERMINAL`
- `enrollment_status`: `PENDING`, `ENROLLED`, `FAILED`, `REVOKED`
- `verification_status`: `PENDING`, `VERIFIED`, `FAILED`, `NOT_REQUESTED`

### API Management

Endpoint: `POST /api/v1/external-integrations/apis`

`endpoint_reference` must be HTTPS and `encryption_enabled` must be `true`.

```json
{
  "integration_name": "ECMS Warrant Verification",
  "api_provider": "Judicial Service ECMS",
  "authentication_type": "OAUTH2",
  "endpoint_reference": "https://court-api.example.gov.gh/warrants",
  "api_status": "ACTIVE",
  "rate_limit_status": "NORMAL",
  "encryption_enabled": true,
  "last_health_check": "2026-05-20T11:00:00"
}
```

Allowed values:

- `authentication_type`: `OAUTH2`, `JWT`, `API_KEY`, `MFA`
- `api_status`: `ACTIVE`, `INACTIVE`, `DEGRADED`, `FAILED`
- `rate_limit_status`: `NORMAL`, `THROTTLED`, `EXCEEDED`, `DISABLED`

### Data Synchronization

Endpoint: `POST /api/v1/external-integrations/synchronizations`

```json
{
  "source_facility": "Nsawam",
  "target_server": "https://regional-sync.example.gov.gh",
  "synchronization_type": "BATCH",
  "synchronization_status": "SYNCED",
  "records_processed": 120,
  "records_failed": 0,
  "retry_count": 0,
  "last_attempt_at": "2026-05-20T11:15:00",
  "completed_at": "2026-05-20T11:20:00",
  "error_message": null
}
```

Allowed values:

- `synchronization_type`: `REAL_TIME`, `BATCH`, `OFFLINE`
- `synchronization_status`: `PENDING`, `IN_PROGRESS`, `SYNCED`, `FAILED`, `RETRY_SCHEDULED`

Completed synchronization requires `completed_at`. Failed synchronization requires `error_message`. Duplicate synchronization attempts for the same source, target, type, and attempt time are rejected.

### Cloud Backup Integration

Endpoint: `POST /api/v1/external-integrations/backups`

```json
{
  "backup_reference": "BACKUP-2026-0001",
  "backup_type": "INCREMENTAL",
  "backup_status": "COMPLETED",
  "storage_location": "https://government-cloud.example.gov.gh/pms/backups",
  "records_backed_up": 500,
  "backup_started_at": "2026-05-20T12:00:00",
  "backup_completed_at": "2026-05-20T12:10:00",
  "recovery_test_status": "PASSED"
}
```

Allowed values:

- `backup_type`: `FULL`, `INCREMENTAL`, `EMERGENCY_RECOVERY`, `RECOVERY_TEST`
- `backup_status`: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `RESTORED`
- `recovery_test_status`: `PENDING`, `PASSED`, `FAILED`, `NOT_TESTED`

### Provider Operations

Endpoint: `POST /api/v1/external-integrations/provider-operations`

```json
{
  "provider": "Judicial Service ECMS",
  "operation": "warrant_verification",
  "reference": "https://court-api.example.gov.gh/warrants/ECMS-CASE-2026-0001"
}
```

Allowed operations:

- `warrant_verification`
- `nia_verification`
- `police_synchronization`
- `biometric_verification`
- `health_check`
- `cloud_backup`

Provider operations require a configured real adapter. If no provider adapter is registered, the module returns a sanitized provider-not-configured response and records the blocked attempt in the audit log.

### External Integration Reports

Endpoint: `GET /api/v1/external-integrations/reports`

Report sections:

- `court_synchronization`
- `nia_verifications`
- `police_synchronization`
- `biometric_verifications`
- `api_gateway_health`
- `synchronization_resilience`
- `cloud_backup_status`

### List Integration Records

Endpoint: `GET /api/v1/external-integrations/{record_type}`

Supported `record_type` values:

- `court`
- `nia`
- `police`
- `biometrics`
- `apis`
- `synchronizations`
- `backups`

## Inmate API JSON Inputs

Base path: `/api/v1/inmates`

### Create Inmate

Endpoint: `POST /api/v1/inmates`

```json

#INMATE INFORMATION
{
  "inmate_id": "INM-2026-0001",
  "warrant_id": 1,
  "first_name": "FirstName",
  "last_name": "LastName",
  "other_names": "Other Names",
  "date_of_birth": "1990-01-01",
  "age": 36,
  "gender": "male",
  "nationality": "Ghanaian",
  "national_id": "GHA-000000000-0",
  "phone": "+233000000000",
  "address": "Residential address",
  "marital_status": "single",
  "photo": "uploads/inmates/inmate-photo.jpg",
  "fingerprint_id": "FP-2026-0001",
  "height_cm": "175.5",
  "weight_kg": "72.4",
  "eye_color": "brown",
  "hair_color": "black",
  "distinguishing_marks": "None",
  "religion": "Religion",
  "occupation": "Occupation",
  "education_level": "Education level",

  #NEXT OF KING INFORMATON

  "next_of_kin_name": "Next Of Kin",
  "next_of_kin_relation": "parent",
  "next_of_kin_contact": "+233000000001",
  "next_of_kin_address": "Next of kin address",

  #ARREST INFORMATION
  "case_number": "CASE-2026-0001",
  "offense": "Offense name",
  "offense_description": "Offense description",
  "arrest_date": "2026-05-01",
  "arresting_officer": "Officer Name",
  "arresting_agency": "Police Service",

  #SENTENCE INFORMATION
  "court": "Court Name",
  "judge": "Judge Name",
  "sentence_type": "remand",
  "sentence_duration": "6 months",
  "expected_release_date": "2026-11-01",
  "status": "active",
  "admission_date": "2026-05-02",
  "admission_time": "09:30",
  "admission_officer_id": 1
}
```

Allowed values:

- `gender`: `male`, `female`
- `marital_status`: `single`, `married`, `divorced`, `widowed`
- `next_of_kin_relation`: `spouse`, `parent`, `sibling`, `child`, `other`
- `sentence_type`: `remand`, `convicted`, `life`, `death`
- `status`: `active`, `released`, `transferred`, `deceased`

### Update Inmate

Endpoint: `PATCH /api/v1/inmates/{inmate_db_id}`

Send only fields that should change.

```json
{
  "phone": "+233000000002",
  "address": "Updated residential address",
  "marital_status": "married",
  "next_of_kin_name": "Updated Next Of Kin",
  "next_of_kin_relation": "spouse",
  "next_of_kin_contact": "+233000000003"
}
```

### Update Inmate Status

Endpoint: `PATCH /api/v1/inmates/{inmate_db_id}/status`

```json
{
  "status": "transferred"
}
```

### Approve Inmate Transfer

Endpoint: `PATCH /api/v1/inmates/{inmate_db_id}/approve-transfer`

```json
{}
```

### Approve Inmate Release

Endpoint: `PATCH /api/v1/inmates/{inmate_db_id}/approve-release`

```json
{}
```

### Inmate Search Filters

Endpoint: `GET /api/v1/inmates/search`

Supported query fields include:

```json
{
  "q": "INM-2026-0001",
  "gender": "male",
  "nationality": "Ghanaian",
  "admission_date": "2026-05-02",
  "arrest_date": "2026-05-01",
  "status": "active",
  "sentence_type": "remand",
  "limit": 20,
  "offset": 0
}
```
