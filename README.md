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
- Arrest Warrant Management was implemented with model, DTO, repository, service, controller, routes, schema, validations, list, search, get, update, status update, and delete support.
- Medical and Health Management was implemented with medical entities, DTO validation, repository, service, controller, routes, schema, role-restricted APIs, audit logging, appointment/referral support, medication administration tracking, mental health records, inmate medical history, treatment history, and medical reports.
- `scripts/create_tables.py` was updated so `arrest_warrants` is created before `inmates`.
- `scripts/create_tables.py` was updated to create the medical tables after `users` and `inmates`.
- `main.py` registers the inmate, arrest warrant, and medical APIs under `/api/v1`.

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
- External Integration Management
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

### Grouped Coming-Soon Menus

Medical Management is now implemented.

Housing and Movement Management now includes grouped sections for block management, cell management, bed allocation, inmate housing, occupancy monitoring, special housing, and housing reports.

Rehabilitation Management includes vocational training, education tracking, counseling, behavior tracking, religious participation, work assignments, skill certification, post-release follow-up, and reports.

Notifications includes email alerts, visit reminders, court reminders, medical alerts, security alerts, transfer alerts, and emergency notifications.

External Integration Management includes court system integration, national ID integration, police database integration, biometric integration, API management, data synchronization, and cloud backup integration.

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
