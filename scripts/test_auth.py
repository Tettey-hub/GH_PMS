from __future__ import annotations

import getpass
import sys
from pathlib import Path

from colorama import Fore, Style, init
from tabulate import tabulate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import app
from src.models.arrest_warrant import (
    ARREST_WARRANT_GENDERS,
    ARREST_WARRANT_SENTENCE_TYPES,
    ARREST_WARRANT_STATUSES,
)
from src.models.inmate import (
    INMATE_GENDERS,
    INMATE_MARITAL_STATUSES,
    INMATE_NEXT_OF_KIN_RELATIONS,
    INMATE_RELEASE_TYPES,
    INMATE_SENTENCE_TYPES,
    INMATE_STATUSES,
    INMATE_TRANSFER_TYPES,
)
from src.models.medical import (
    APPOINTMENT_STATUSES,
    APPOINTMENT_TYPES,
    DIAGNOSIS_TYPES,
    DISABILITY_STATUSES,
    DRUG_TEST_STATUSES,
    INFECTIOUS_DISEASE_STATUSES,
    MALARIA_STATUSES,
    MEDICAL_BLOOD_GROUPS,
    MEDICAL_GENOTYPES,
    MENTAL_HEALTH_SCREENING_STATUSES,
    REFERRAL_STATUSES,
    SCREENING_TYPES,
    SEVERITY_LEVELS,
    SUICIDE_RISK_LEVELS,
    TREATMENT_STATUSES,
)


def main() -> int:
    init(autoreset=True)
    client = app.test_client()
    access_token: str | None = None
    refresh_token: str | None = None
    current_user: dict | None = None

    while True:
        if current_user is None:
            print_logged_out_menu()
        else:
            print_logged_in_menu(current_user)

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()

        if current_user is None:
            if choice == "1":
                access_token, refresh_token, current_user = login(client)
            elif choice == "2":
                print(f"{Fore.CYAN}Goodbye.{Style.RESET_ALL}")
                return 0
            else:
                print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")
        elif choice == "1":
            manage_users(client, access_token)
        elif choice == "2":
            manage_inmates(client, access_token)
        elif choice == "3":
            manage_arrest_warrants(client, access_token)
        elif choice == "4":
            show_coming_soon_menu("Court and Sentence Management", [
                "Create court records",
                "Edit sentence records",
                "Approve sentence modifications",
                "Access legal documents",
                "Generate legal reports",
            ])
        elif choice == "5":
            manage_medical_management(client, access_token)
        elif choice == "6":
            show_coming_soon_menu("Visitor Management", [
                "Approve/reject visitor requests",
                "View visitor logs",
                "Blacklist visitors",
            ])
        elif choice == "7":
            show_housing_and_movement_menu()
        elif choice == "8":
            show_coming_soon_menu("Rehabilitation Management", [
                "Vocational training registration",
                "Educational program tracking",
                "Counseling sessions",
                "Behavioral improvement tracking",
                "Religious participation",
                "Work assignments",
                "Skill certification",
                "Post-release follow-up",
                "Rehabilitation reports",
            ])
        elif choice == "9":
            show_coming_soon_menu("Notifications", [
                "Email alerts",
                "Visit reminders",
                "Court reminders",
                "Medical alerts",
                "Security alerts",
                "Transfer alerts",
                "Emergency notifications",
            ])
        elif choice == "10":
            show_coming_soon_menu("External Integration Management", [
                "Court system integration",
                "National ID integration",
                "Police database integration",
                "Biometric integration",
                "API management",
                "Data synchronization",
                "Cloud backup integration",
            ])
        elif choice == "11":
            show_coming_soon_menu("Reporting and Analytics", [
                "Generate reports",
                "Access analytics dashboard",
                "Export reports",
                "View prison statistics",
            ])
        elif choice == "12":
            show_coming_soon_menu("System Administration", [
                "Configure system settings",
                "Manage roles",
                "Access audit logs",
                "Manage backups",
                "Monitor system activities",
            ])
        elif choice == "13":
            access_token, refresh_token, current_user = logout(client, access_token, refresh_token, current_user)
        elif choice == "14":
            print(f"{Fore.CYAN}Goodbye.{Style.RESET_ALL}")
            return 0
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def print_logged_out_menu() -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Welcome admin{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Login")
    print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Exit")


def print_logged_in_menu(current_user: dict) -> None:
    active_name = current_user.get("full_name") or current_user.get("email") or "Active User"
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{active_name}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Manage Users")
    print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Inmate Management")
    print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Manage Warrant")
    print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Court and Sentence Management")
    print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Medical Management")
    print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Visitor Management")
    print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Housing and Movement Management")
    print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Rehabilitation Management")
    print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Notifications")
    print(f"{Fore.YELLOW}10.{Style.RESET_ALL} External Integration Management")
    print(f"{Fore.YELLOW}11.{Style.RESET_ALL} Reporting and Analytics")
    print(f"{Fore.YELLOW}12.{Style.RESET_ALL} System Administration")
    print(f"{Fore.YELLOW}13.{Style.RESET_ALL} Log Out")
    print(f"{Fore.YELLOW}14.{Style.RESET_ALL} Exit")


def show_coming_soon_menu(title: str, actions: list[str]) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        for index, action in enumerate(actions, start=1):
            print(f"{Fore.YELLOW}{index}.{Style.RESET_ALL} {action}")
        print(f"{Fore.YELLOW}{len(actions) + 1}.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == str(len(actions) + 1):
            return
        if choice.isdigit() and 1 <= int(choice) <= len(actions):
            print(f"{Fore.YELLOW}{actions[int(choice) - 1]}:{Style.RESET_ALL} Coming soon.")
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_medical_management(client, access_token: str | None) -> None:
    if not access_token:
        print(f"{Fore.YELLOW}Login as an admin or medical officer before using Medical Management.{Style.RESET_ALL}")
        return

    sections = [
        ("Medical Registration", manage_medical_registration),
        ("Medical Screening", manage_medical_screening),
        ("Treatment Management", manage_treatment_management),
        ("Medication Management", manage_medication_management),
        ("Appointment Scheduling", manage_appointment_scheduling),
        ("Mental Health Management", manage_mental_health_management),
        ("Medical Reports", manage_medical_reports),
    ]

    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Medical Management{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Manages inmate health records and healthcare services.{Style.RESET_ALL}")
        for index, (section_title, _) in enumerate(sections, start=1):
            print(f"{Fore.YELLOW}{index}.{Style.RESET_ALL} {section_title}")
        print(f"{Fore.YELLOW}{len(sections) + 1}.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == str(len(sections) + 1):
            return
        if choice.isdigit() and 1 <= int(choice) <= len(sections):
            _, handler = sections[int(choice) - 1]
            handler(client, access_token)
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_medical_registration(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Medical Registration{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Create inmate medical profile")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Update inmate medical profile")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} View inmate medical history")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            create_medical_profile(client, access_token)
        elif choice == "2":
            update_medical_profile(client, access_token)
        elif choice == "3":
            view_inmate_medical_history(client, access_token)
        elif choice == "4":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_medical_screening(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Medical Screening{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Record screening")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View inmate medical history")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            record_medical_screening(client, access_token)
        elif choice == "2":
            view_inmate_medical_history(client, access_token)
        elif choice == "3":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_treatment_management(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Treatment Management{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Create diagnosis")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Create treatment plan")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Create prescription")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} View inmate treatment history")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            create_medical_diagnosis(client, access_token)
        elif choice == "2":
            create_treatment_plan(client, access_token)
        elif choice == "3":
            create_prescription(client, access_token)
        elif choice == "4":
            view_inmate_treatment_history(client, access_token)
        elif choice == "5":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_medication_management(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Medication Management{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Create prescription")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Record medication administration")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} View inmate treatment history")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            create_prescription(client, access_token)
        elif choice == "2":
            record_medication_administration(client, access_token)
        elif choice == "3":
            view_inmate_treatment_history(client, access_token)
        elif choice == "4":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_appointment_scheduling(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Appointment Scheduling{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Schedule medical appointment")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View referral facilities")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} View inmate medical history")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            schedule_medical_appointment(client, access_token)
        elif choice == "2":
            view_referral_facilities(client, access_token)
        elif choice == "3":
            view_inmate_medical_history(client, access_token)
        elif choice == "4":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_mental_health_management(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Mental Health Management{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Create mental health record")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View inmate medical history")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            create_mental_health_record(client, access_token)
        elif choice == "2":
            view_inmate_medical_history(client, access_token)
        elif choice == "3":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_medical_reports(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Medical Reports{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Generate medical reports")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View inmate medical history")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} View inmate treatment history")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            view_medical_reports(client, access_token)
        elif choice == "2":
            view_inmate_medical_history(client, access_token)
        elif choice == "3":
            view_inmate_treatment_history(client, access_token)
        elif choice == "4":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def create_medical_profile(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Create Medical Profile{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "blood_group": prompt_optional_exact_choice("Blood group", sorted(MEDICAL_BLOOD_GROUPS)),
        "genotype": prompt_optional_exact_choice("Genotype", sorted(MEDICAL_GENOTYPES)),
        "allergies": prompt_optional("Allergies"),
        "chronic_illnesses": prompt_optional("Chronic illnesses"),
        "disability_status": prompt_choice("Disability status", sorted(DISABILITY_STATUSES)),
        "disability_description": prompt_optional("Disability description"),
        "emergency_medical_notes": prompt_optional("Emergency medical notes"),
        "current_medications": prompt_optional("Current medications"),
        "primary_physician": prompt_optional("Primary physician"),
    })
    _post_medical_record(client, access_token, "/api/v1/medical/profiles", payload, "medical_profile", "Medical profile created")


def update_medical_profile(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Update Medical Profile{Style.RESET_ALL}")
    inmate_id = prompt_required_int("Inmate database ID")
    print(f"{Fore.WHITE}Leave a field blank to keep the current value.{Style.RESET_ALL}")
    payload = clean_payload({
        "blood_group": prompt_optional_exact_choice("Blood group", sorted(MEDICAL_BLOOD_GROUPS)),
        "genotype": prompt_optional_exact_choice("Genotype", sorted(MEDICAL_GENOTYPES)),
        "allergies": prompt_optional("Allergies"),
        "chronic_illnesses": prompt_optional("Chronic illnesses"),
        "disability_status": prompt_optional_choice("Disability status", sorted(DISABILITY_STATUSES)),
        "disability_description": prompt_optional("Disability description"),
        "emergency_medical_notes": prompt_optional("Emergency medical notes"),
        "current_medications": prompt_optional("Current medications"),
        "primary_physician": prompt_optional("Primary physician"),
    })
    if not payload:
        print(f"{Fore.YELLOW}No profile changes provided.{Style.RESET_ALL}")
        return
    response = client.patch(
        f"/api/v1/medical/profiles/{inmate_id}",
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Medical profile update failed", body)
        return
    print(f"{Fore.GREEN}Medical profile updated.{Style.RESET_ALL}")
    print_medical_details(body.get("medical_profile", {}))


def record_medical_screening(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Record Medical Screening{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "screening_date": prompt_required("Screening date (YYYY-MM-DD)"),
        "screening_type": prompt_choice("Screening type", sorted(SCREENING_TYPES)),
        "temperature": prompt_optional("Temperature"),
        "blood_pressure": prompt_optional("Blood pressure (120/80 format)"),
        "weight_kg": prompt_optional("Weight KG"),
        "height_cm": prompt_optional("Height CM"),
        "infectious_disease_status": prompt_choice("Infectious disease status", sorted(INFECTIOUS_DISEASE_STATUSES)),
        "malaria_status": prompt_choice("Malaria status", sorted(MALARIA_STATUSES)),
        "drug_test_status": prompt_choice("Drug test status", sorted(DRUG_TEST_STATUSES)),
        "mental_health_status": prompt_choice("Mental health status", sorted(MENTAL_HEALTH_SCREENING_STATUSES)),
        "screening_notes": prompt_optional("Screening notes"),
    })
    _post_medical_record(client, access_token, "/api/v1/medical/screenings", payload, "screening", "Medical screening recorded")


def create_medical_diagnosis(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Create Diagnosis{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "diagnosis_name": prompt_required("Diagnosis name"),
        "diagnosis_type": prompt_choice("Diagnosis type", sorted(DIAGNOSIS_TYPES)),
        "diagnosis_date": prompt_required("Diagnosis date (YYYY-MM-DD)"),
        "severity_level": prompt_choice("Severity level", sorted(SEVERITY_LEVELS)),
        "diagnosis_notes": prompt_optional("Diagnosis notes"),
    })
    _post_medical_record(client, access_token, "/api/v1/medical/diagnoses", payload, "diagnosis", "Diagnosis created")


def create_treatment_plan(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Create Treatment Plan{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "diagnosis_id": prompt_required_int("Diagnosis ID"),
        "treatment_plan": prompt_required("Treatment plan"),
        "treatment_start_date": prompt_required("Treatment start date (YYYY-MM-DD)"),
        "treatment_end_date": prompt_optional("Treatment end date (YYYY-MM-DD)"),
        "treatment_status": prompt_choice("Treatment status", sorted(TREATMENT_STATUSES)),
    })
    _post_medical_record(client, access_token, "/api/v1/medical/treatment-plans", payload, "treatment_plan", "Treatment plan created")


def create_prescription(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Create Prescription{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "medication_name": prompt_required("Medication name"),
        "dosage": prompt_required("Dosage"),
        "frequency": prompt_required("Frequency"),
        "duration": prompt_required("Duration"),
        "prescription_notes": prompt_optional("Prescription notes"),
        "prescribed_date": prompt_required("Prescribed date (YYYY-MM-DD)"),
    })
    _post_medical_record(client, access_token, "/api/v1/medical/prescriptions", payload, "prescription", "Prescription created")


def record_medication_administration(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Record Medication Administration{Style.RESET_ALL}")
    payload = clean_payload({
        "prescription_id": prompt_required_int("Prescription ID"),
        "administration_time": prompt_required("Administration time (YYYY-MM-DDTHH:MM:SS)"),
        "administration_notes": prompt_optional("Administration notes"),
    })
    _post_medical_record(
        client,
        access_token,
        "/api/v1/medical/medication-administrations",
        payload,
        "medication_administration_log",
        "Medication administration recorded",
    )


def schedule_medical_appointment(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Schedule Medical Appointment{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "appointment_type": prompt_choice("Appointment type", sorted(APPOINTMENT_TYPES)),
        "appointment_date": prompt_required("Appointment date (YYYY-MM-DD)"),
        "appointment_time": prompt_required("Appointment time (HH:MM)"),
        "facility_name": prompt_required("Facility name"),
        "doctor_name": prompt_optional("Doctor name"),
        "referral_status": prompt_choice("Referral status", sorted(REFERRAL_STATUSES)),
        "appointment_status": prompt_choice("Appointment status", sorted(APPOINTMENT_STATUSES)),
        "emergency_case": prompt_bool("Emergency case"),
        "notes": prompt_optional("Notes"),
    })
    _post_medical_record(client, access_token, "/api/v1/medical/appointments", payload, "appointment", "Medical appointment scheduled")


def create_mental_health_record(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Create Mental Health Record{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "psychological_assessment": prompt_required("Psychological assessment"),
        "counseling_notes": prompt_optional("Counseling notes"),
        "suicide_risk_level": prompt_choice("Suicide risk level", sorted(SUICIDE_RISK_LEVELS)),
        "behavioral_observations": prompt_optional("Behavioral observations"),
        "assessment_date": prompt_required("Assessment date (YYYY-MM-DD)"),
    })
    _post_medical_record(client, access_token, "/api/v1/medical/mental-health-records", payload, "mental_health_record", "Mental health record created")


def view_inmate_medical_history(client, access_token: str) -> None:
    inmate_id = prompt_required_int("Inmate database ID")
    response = client.get(
        f"/api/v1/medical/inmates/{inmate_id}/history",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Medical history lookup failed", body)
        return
    print_medical_history(body.get("medical_history", {}))


def view_inmate_treatment_history(client, access_token: str) -> None:
    inmate_id = prompt_required_int("Inmate database ID")
    response = client.get(
        f"/api/v1/medical/inmates/{inmate_id}/treatments",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Treatment history lookup failed", body)
        return
    print_medical_history(body.get("treatment_history", {}))


def view_medical_reports(client, access_token: str) -> None:
    response = client.get(
        "/api/v1/medical/reports",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Medical reports failed", body)
        return
    print_medical_history(body.get("medical_reports", {}))


def view_referral_facilities(client, access_token: str) -> None:
    response = client.get(
        "/api/v1/medical/referral-facilities",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Referral facilities lookup failed", body)
        return
    facilities = body.get("referral_facilities")
    if not isinstance(facilities, list) or not facilities:
        print(f"{Fore.YELLOW}No referral facilities configured.{Style.RESET_ALL}")
        return
    print(tabulate([[facility] for facility in facilities], headers=["Referral Facility"], tablefmt="grid"))


def _post_medical_record(client, access_token: str, endpoint: str, payload: dict[str, object], response_key: str, success_label: str) -> None:
    response = client.post(
        endpoint,
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 201:
        print_api_error(f"{success_label} failed", body)
        return
    print(f"{Fore.GREEN}{success_label}.{Style.RESET_ALL}")
    print_medical_details(body.get(response_key, {}))


def print_medical_details(record: object) -> None:
    if not isinstance(record, dict):
        print(f"{Fore.YELLOW}No record details returned.{Style.RESET_ALL}")
        return
    rows = [[field, value] for field, value in record.items()]
    print(tabulate(rows, headers=["Field", "Value"], tablefmt="grid"))


def print_record_details(record: object) -> None:
    if not isinstance(record, dict):
        print(f"{Fore.YELLOW}No record details returned.{Style.RESET_ALL}")
        return
    rows = [[field, value] for field, value in record.items()]
    print(tabulate(rows, headers=["Field", "Value"], tablefmt="grid"))


def print_record_list(title: str, records: object) -> None:
    if not isinstance(records, list):
        print(f"{Fore.RED}{title}:{Style.RESET_ALL} invalid response.")
        return
    if not records:
        print(f"{Fore.YELLOW}No {title.lower()} found.{Style.RESET_ALL}")
        return
    print(f"\n{Fore.GREEN}{title} ({len(records)}){Style.RESET_ALL}")
    print(tabulate(records, headers="keys", tablefmt="grid"))


def print_medical_history(history: object) -> None:
    if not isinstance(history, dict):
        print(f"{Fore.RED}Invalid medical response.{Style.RESET_ALL}")
        return
    for section, value in history.items():
        print(f"\n{Fore.GREEN}{section.replace('_', ' ').title()}{Style.RESET_ALL}")
        if isinstance(value, list):
            if not value:
                print(f"{Fore.YELLOW}No records found.{Style.RESET_ALL}")
            else:
                print(tabulate(value, headers="keys", tablefmt="grid"))
        elif isinstance(value, dict):
            print_medical_details(value)
        elif value is None:
            print(f"{Fore.YELLOW}No record found.{Style.RESET_ALL}")
        else:
            print(value)


def show_housing_and_movement_menu() -> None:
    sections = [
        ("Block Management", [
            "Create prison blocks",
            "Block categorization",
            "Security-level assignment",
        ]),
        ("Cell Management", [
            "Create cells",
            "Cell capacity definition",
            "Cell condition tracking",
        ]),
        ("Bed Allocation", [
            "Assign beds",
            "Bed occupancy tracking",
            "Bed reassignment",
        ]),
        ("Inmate Housing", [
            "Assign inmate to cell",
            "Transfer inmate between cells",
            "Isolation housing",
        ]),
        ("Occupancy Monitoring", [
            "Available spaces",
            "Monitor occupancy",
        ]),
        ("Special Housing", [
            "High-risk inmates",
            "Medical isolation",
            "Juvenile segregation",
        ]),
        ("Housing Reports", [
            "Occupancy reports",
            "Housing transfer reports",
            "Overcrowding reports",
        ]),
    ]

    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Housing and Movement Management{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Handles prison accommodation allocation and occupancy monitoring.{Style.RESET_ALL}")
        for index, (section_title, _) in enumerate(sections, start=1):
            print(f"{Fore.YELLOW}{index}.{Style.RESET_ALL} {section_title}")
        print(f"{Fore.YELLOW}{len(sections) + 1}.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == str(len(sections) + 1):
            return
        if choice.isdigit() and 1 <= int(choice) <= len(sections):
            section_title, actions = sections[int(choice) - 1]
            show_coming_soon_menu(section_title, actions)
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def login(client) -> tuple[str | None, str | None, dict | None]:
    login_value = input(f"{Fore.CYAN}Email or username:{Style.RESET_ALL} ").strip()
    password = getpass.getpass(f"{Fore.CYAN}Password:{Style.RESET_ALL} ")
    login_field = "email" if "@" in login_value else "username"

    response = client.post(
        "/api/v1/auth/login",
        json={login_field: login_value, "password": password},
        headers={"Host": "localhost"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Login failed:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        return None, None, None

    access_token = body.get("access_token")
    refresh_token = body.get("refresh_token") or extract_refresh_token(response)
    user = body.get("user")
    if not isinstance(access_token, str) or not isinstance(refresh_token, str) or not isinstance(user, dict):
        print(f"{Fore.RED}Login failed:{Style.RESET_ALL} invalid auth response.")
        return None, None, None

    print(f"{Fore.GREEN}Login successful:{Style.RESET_ALL} {user.get('full_name')} ({user.get('officer_id')})")
    return access_token, refresh_token, user


def logout(
    client,
    access_token: str | None,
    refresh_token: str | None,
    current_user: dict | None,
) -> tuple[None, None, None]:
    if not access_token:
        print(f"{Fore.YELLOW}No active login session.{Style.RESET_ALL}")
        return None, None, None

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Logout failed:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        return None, None, None

    name = current_user.get("full_name") if current_user else "current user"
    revoked_count = body.get("revoked_refresh_tokens", 0)
    print(f"{Fore.GREEN}Logged out:{Style.RESET_ALL} {name} ({revoked_count} refresh token(s) revoked)")
    return None, None, None


def extract_refresh_token(response) -> str | None:
    cookie_header = response.headers.get("Set-Cookie", "")
    if not cookie_header.startswith("refresh_token="):
        return None
    return cookie_header.split(";", 1)[0].split("=", 1)[1]


def manage_users(client, access_token: str | None) -> None:
    if not access_token:
        print(f"{Fore.YELLOW}Login before managing users.{Style.RESET_ALL}")
        return

    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Manage Users{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Admin Users")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Duty Scheduling")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Attendance Tracking")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Leave Management")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Performance Evaluation")
        print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Staff Disciplinary Records")
        print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Staff Training")
        print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            manage_admin_users(client, access_token)
        elif choice == "2":
            print(f"{Fore.YELLOW}Duty Scheduling:{Style.RESET_ALL} Coming soon.")
        elif choice == "3":
            print(f"{Fore.YELLOW}Attendance Tracking:{Style.RESET_ALL} Coming soon.")
        elif choice == "4":
            print(f"{Fore.YELLOW}Leave Management:{Style.RESET_ALL} Coming soon.")
        elif choice == "5":
            print(f"{Fore.YELLOW}Performance Evaluation:{Style.RESET_ALL} Coming soon.")
        elif choice == "6":
            print(f"{Fore.YELLOW}Staff Disciplinary Records:{Style.RESET_ALL} Coming soon.")
        elif choice == "7":
            print(f"{Fore.YELLOW}Staff Training:{Style.RESET_ALL} Coming soon.")
        elif choice == "8":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def manage_admin_users(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Admin Users{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Add Admin")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View All Staffs")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} View Specific Staff")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Update Staff")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Delete Staff")
        print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Reset Password")
        print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Activate/Deactivate Account")
        print(f"{Fore.YELLOW}8.{Style.RESET_ALL} View User Logs")
        print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            add_admin(client, access_token)
        elif choice == "2":
            show_all_staffs(client, access_token)
        elif choice == "3":
            show_specific_staff(client, access_token)
        elif choice == "4":
            update_staff(client, access_token)
        elif choice == "5":
            delete_staff(client, access_token)
        elif choice == "6":
            reset_staff_password(client, access_token)
        elif choice == "7":
            set_staff_account_status(client, access_token)
        elif choice == "8":
            print(f"{Fore.YELLOW}View user logs:{Style.RESET_ALL} Coming soon.")
        elif choice == "9":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def show_all_staffs(client, access_token: str) -> None:
    response = client.get(
        "/api/v1/auth/users",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Failed to load staffs:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        missing_permissions = body.get("missing_permissions")
        if isinstance(missing_permissions, list):
            print(f"{Fore.YELLOW}Missing permissions:{Style.RESET_ALL} {', '.join(missing_permissions)}")
        return

    users = body.get("users")
    if not isinstance(users, list):
        print(f"{Fore.RED}Failed to load staffs:{Style.RESET_ALL} invalid response.")
        return

    if not users:
        print(f"{Fore.YELLOW}No staffs found.{Style.RESET_ALL}")
        return

    rows = []
    for user in users:
        if not isinstance(user, dict):
            continue
        rows.append([
            user.get("id"),
            user.get("staff_id") or "",
            user.get("officer_id") or "",
            user.get("full_name") or "",
            user.get("email") or "",
            user.get("department") or "",
            user.get("position") or user.get("rank") or "",
            user.get("role") or "",
            user.get("status") or "",
        ])

    print(f"\n{Fore.GREEN}All Staffs ({body.get('total', len(rows))}){Style.RESET_ALL}")
    print(tabulate(
        rows,
        headers=["ID", "Staff ID", "Officer ID", "Name", "Email", "Department", "Position", "Role", "Status"],
        tablefmt="grid",
    ))


def show_specific_staff(client, access_token: str) -> None:
    lookup = prompt_staff_lookup()
    response = client.get(
        "/api/v1/auth/users/staff",
        query_string=lookup,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Failed to load staff:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        return

    user = body.get("user")
    if not isinstance(user, dict):
        print(f"{Fore.RED}Failed to load staff:{Style.RESET_ALL} invalid response.")
        return
    print_staff_details(user)


def update_staff(client, access_token: str) -> None:
    lookup = prompt_staff_lookup()
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Update Staff{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Leave a field blank to keep the current value.{Style.RESET_ALL}")
    updates = {
        "first_name": prompt_optional("First name"),
        "middle_name": prompt_optional("Middle name"),
        "last_name": prompt_optional("Last name"),
        "gender": prompt_optional("Gender"),
        "dob": prompt_optional("Date of birth (YYYY-MM-DD)"),
        "email": prompt_optional("Email address"),
        "phone": prompt_optional("Phone number"),
        "national_id": prompt_optional("National ID number"),
        "address": prompt_optional("Residential address"),
        "profile_image": prompt_optional("Profile image path"),
        "rank": prompt_optional("Rank / title"),
        "department": prompt_optional("Department"),
        "position": prompt_optional("Position"),
        "employment_date": prompt_optional("Employment date (YYYY-MM-DD)"),
        "branch": prompt_optional("Branch / Facility"),
        "role": prompt_optional("Role"),
        "status": prompt_optional("Status"),
        "shift": prompt_optional("Shift"),
        "date_joined": prompt_optional("Date joined (YYYY-MM-DD)"),
    }
    updates = {field: value for field, value in updates.items() if value not in {None, ""}}
    if not updates:
        print(f"{Fore.YELLOW}No updates entered.{Style.RESET_ALL}")
        return

    response = client.patch(
        "/api/v1/auth/users/staff",
        query_string=lookup,
        json=updates,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Update failed:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        errors = body.get("errors")
        if isinstance(errors, dict):
            for field, message in errors.items():
                print(f"{Fore.YELLOW}{field}:{Style.RESET_ALL} {message}")
        return

    print(f"{Fore.GREEN}Staff updated successfully.{Style.RESET_ALL}")
    user = body.get("user")
    if isinstance(user, dict):
        print_staff_details(user)


def delete_staff(client, access_token: str) -> None:
    lookup = prompt_staff_lookup()
    confirm = input(f"{Fore.RED}Type DELETE to confirm staff deletion:{Style.RESET_ALL} ").strip()
    if confirm != "DELETE":
        print(f"{Fore.YELLOW}Delete cancelled.{Style.RESET_ALL}")
        return

    response = client.delete(
        "/api/v1/auth/users/staff",
        query_string=lookup,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Delete failed:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        return

    user = body.get("user", {})
    print(f"{Fore.GREEN}Staff deleted:{Style.RESET_ALL} {user.get('full_name')} ({user.get('officer_id')})")


def reset_staff_password(client, access_token: str) -> None:
    lookup = prompt_staff_lookup()
    password = prompt_password()
    response = client.patch(
        "/api/v1/auth/users/staff",
        query_string=lookup,
        json={"password": password},
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Password reset failed:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        errors = body.get("errors")
        if isinstance(errors, dict):
            for field, message in errors.items():
                print(f"{Fore.YELLOW}{field}:{Style.RESET_ALL} {message}")
        return

    user = body.get("user", {})
    print(f"{Fore.GREEN}Password reset successful:{Style.RESET_ALL} {user.get('full_name')} ({user.get('officer_id')})")


def set_staff_account_status(client, access_token: str) -> None:
    lookup = prompt_staff_lookup()
    status = prompt_choice("Account status", ["active", "inactive", "suspended"])
    response = client.patch(
        "/api/v1/auth/users/staff",
        query_string=lookup,
        json={"status": status},
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Status update failed:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        errors = body.get("errors")
        if isinstance(errors, dict):
            for field, message in errors.items():
                print(f"{Fore.YELLOW}{field}:{Style.RESET_ALL} {message}")
        return

    user = body.get("user", {})
    print(f"{Fore.GREEN}Account status updated:{Style.RESET_ALL} {user.get('full_name')} -> {user.get('status')}")


def manage_arrest_warrants(client, access_token: str | None) -> None:
    if not access_token:
        print(f"{Fore.YELLOW}Login before managing arrest warrants.{Style.RESET_ALL}")
        return

    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Manage Warrant{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} View all warrants")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View warrant by")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Edit Warrant")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Delete warrant")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            show_all_warrants(client, access_token)
        elif choice == "2":
            show_warrants_by_filter(client, access_token)
        elif choice == "3":
            edit_warrant(client, access_token)
        elif choice == "4":
            delete_warrant(client, access_token)
        elif choice == "5":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def show_all_warrants(client, access_token: str) -> None:
    query = view_all_warrants_gender_filter()
    response = client.get(
        "/api/v1/arrest-warrants",
        query_string=query,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Failed to load warrants", body)
        return
    print_selected_warrant_filter(query)
    print_warrant_table(body)


def show_warrants_by_filter(client, access_token: str) -> None:
    query = view_warrant_by_filter()
    response = client.get(
        "/api/v1/arrest-warrants",
        query_string=query,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Failed to load warrants", body)
        return
    print_selected_warrant_filter(query)
    print_warrant_table(body)


def show_warrant_by_id(client, access_token: str) -> None:
    warrant_db_id = prompt_required_int("Warrant database ID")
    response = client.get(
        f"/api/v1/arrest-warrants/{warrant_db_id}",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Failed to load warrant", body)
        return
    warrant = body.get("arrest_warrant")
    if not isinstance(warrant, dict):
        print(f"{Fore.RED}Failed to load warrant:{Style.RESET_ALL} invalid response.")
        return
    print_warrant_details(warrant)


def edit_warrant(client, access_token: str) -> None:
    warrant_db_id = prompt_required_int("Warrant database ID")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Edit Warrant{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Leave a field blank to keep its current value.{Style.RESET_ALL}")
    updates = clean_payload({
        "warrant_number": prompt_optional("Warrant number"),
        "case_number": prompt_optional("Case number"),
        "first_name": prompt_optional("First name"),
        "last_name": prompt_optional("Last name"),
        "other_names": prompt_optional("Other names"),
        "date_of_birth": prompt_optional("Date of birth (YYYY-MM-DD)"),
        "gender": prompt_optional_choice("Gender", sorted(ARREST_WARRANT_GENDERS)),
        "nationality": prompt_optional("Nationality"),
        "national_id": prompt_optional("National ID"),
        "offense": prompt_optional("Offense"),
        "offense_description": prompt_optional("Offense description"),
        "arrest_date": prompt_optional("Arrest date (YYYY-MM-DD)"),
        "arresting_officer": prompt_optional("Arresting officer"),
        "arresting_agency": prompt_optional("Arresting agency"),
        "court": prompt_optional("Court"),
        "judge": prompt_optional("Judge"),
        "sentence_type": prompt_optional_choice("Sentence type", sorted(ARREST_WARRANT_SENTENCE_TYPES)),
        "sentence_duration": prompt_optional("Sentence duration"),
        "status": prompt_optional_choice("Status", sorted(ARREST_WARRANT_STATUSES)),
        "issued_date": prompt_optional("Issued date (YYYY-MM-DD)"),
    })
    if not updates:
        print(f"{Fore.YELLOW}No changes entered.{Style.RESET_ALL}")
        return

    response = client.patch(
        f"/api/v1/arrest-warrants/{warrant_db_id}",
        json=updates,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Warrant update failed", body)
        return

    warrant = body.get("arrest_warrant")
    if not isinstance(warrant, dict):
        print(f"{Fore.RED}Warrant update failed:{Style.RESET_ALL} invalid response.")
        return
    print(f"{Fore.GREEN}Warrant updated:{Style.RESET_ALL} {warrant.get('warrant_number')} ({warrant.get('case_number')})")
    print_warrant_details(warrant)


def delete_warrant(client, access_token: str) -> None:
    warrant_db_id = prompt_required_int("Warrant database ID")
    confirm = input(f"{Fore.RED}Type DELETE to confirm warrant deletion:{Style.RESET_ALL} ").strip()
    if confirm != "DELETE":
        print(f"{Fore.YELLOW}Delete cancelled.{Style.RESET_ALL}")
        return

    response = client.delete(
        f"/api/v1/arrest-warrants/{warrant_db_id}",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Delete failed", body)
        return
    warrant = body.get("arrest_warrant", {})
    print(f"{Fore.GREEN}Warrant deleted:{Style.RESET_ALL} {warrant.get('warrant_number')} ({warrant.get('case_number')})")


def optional_warrant_filters() -> dict[str, object]:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Optional Warrant Filters{Style.RESET_ALL}")
    return clean_payload({
        "gender": prompt_optional_choice("Gender", sorted(ARREST_WARRANT_GENDERS)),
        "nationality": prompt_optional("Nationality"),
        "arrest_date": prompt_optional("Arrest date (YYYY-MM-DD)"),
        "issued_date": prompt_optional("Issued date (YYYY-MM-DD)"),
        "status": prompt_optional_choice("Status", sorted(ARREST_WARRANT_STATUSES)),
        "sentence_type": prompt_optional_choice("Sentence type", sorted(ARREST_WARRANT_SENTENCE_TYPES)),
        "limit": prompt_optional_int("Limit"),
        "offset": prompt_optional_int("Offset"),
    })


def view_all_warrants_gender_filter() -> dict[str, object]:
    return _select_filter_option(
        "View all warrants",
        [
            ("female", {"gender": "female"}),
            ("male", {"gender": "male"}),
        ],
    )


def view_warrant_by_filter() -> dict[str, object]:
    query: dict[str, object] = {}

    gender_filter = _select_filter_option(
        "View warrant by",
        [
            ("female", {"gender": "female"}),
            ("male", {"gender": "male"}),
        ],
    )
    if not gender_filter:
        return query
    query.update(gender_filter)

    second_filter = _select_filter_option(
        "Filter By",
        [
            ("pending", {"status": "pending"}),
            ("executed", {"status": "executed"}),
            ("cancelled", {"status": "cancelled"}),
            ("convicted", {"sentence_type": "convicted"}),
            ("death", {"sentence_type": "death"}),
            ("life", {"sentence_type": "life"}),
            ("remand", {"sentence_type": "remand"}),
        ],
    )
    query.update(second_filter)
    return query


def print_selected_warrant_filter(query: dict[str, object]) -> None:
    if not query:
        print(f"{Fore.GREEN}Showing all warrants.{Style.RESET_ALL}")
        return
    labels = []
    for field, value in query.items():
        label = "Status" if field == "status" else "Sentence Type" if field == "sentence_type" else "Gender"
        labels.append(f"{label}: {value}")
    print(f"{Fore.GREEN}Showing warrants by {Style.RESET_ALL}{', '.join(labels)}")


def print_warrant_table(body: dict) -> None:
    warrants = body.get("arrest_warrants")
    if not isinstance(warrants, list):
        print(f"{Fore.RED}Failed to load warrants:{Style.RESET_ALL} invalid response.")
        return
    if not warrants:
        print(f"{Fore.YELLOW}No warrants found.{Style.RESET_ALL}")
        return

    rows = []
    for warrant in warrants:
        if not isinstance(warrant, dict):
            continue
        rows.append([
            warrant.get("id"),
            warrant.get("warrant_number") or "",
            warrant.get("case_number") or "",
            f"{warrant.get('first_name') or ''} {warrant.get('last_name') or ''}".strip(),
            warrant.get("offense") or "",
            warrant.get("status") or "",
            warrant.get("sentence_type") or "",
            warrant.get("issued_date") or "",
        ])

    print(f"\n{Fore.GREEN}Arrest Warrants ({body.get('total', len(rows))}){Style.RESET_ALL}")
    print(tabulate(
        rows,
        headers=["ID", "Warrant Number", "Case Number", "Name", "Offense", "Status", "Sentence Type", "Issued Date"],
        tablefmt="grid",
    ))


def print_warrant_details(warrant: dict) -> None:
    rows = [
        ["Database ID", warrant.get("id")],
        ["Warrant Number", warrant.get("warrant_number")],
        ["Case Number", warrant.get("case_number")],
        ["Name", f"{warrant.get('first_name') or ''} {warrant.get('last_name') or ''}".strip()],
        ["Other Names", warrant.get("other_names")],
        ["Date of Birth", warrant.get("date_of_birth")],
        ["Gender", warrant.get("gender")],
        ["Nationality", warrant.get("nationality")],
        ["National ID", warrant.get("national_id")],
        ["Offense", warrant.get("offense")],
        ["Offense Description", warrant.get("offense_description")],
        ["Arrest Date", warrant.get("arrest_date")],
        ["Arresting Officer", warrant.get("arresting_officer")],
        ["Arresting Agency", warrant.get("arresting_agency")],
        ["Court", warrant.get("court")],
        ["Judge", warrant.get("judge")],
        ["Sentence Type", warrant.get("sentence_type")],
        ["Sentence Duration", warrant.get("sentence_duration")],
        ["Status", warrant.get("status")],
        ["Issued Date", warrant.get("issued_date")],
        ["Created At", warrant.get("created_at")],
        ["Updated At", warrant.get("updated_at")],
    ]
    print(tabulate(rows, headers=["Field", "Value"], tablefmt="grid"))


def manage_inmates(client, access_token: str | None) -> None:
    if not access_token:
        print(f"{Fore.YELLOW}Login before managing inmates.{Style.RESET_ALL}")
        return

    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Inmate Management{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Admit inmates")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View all inmates")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Edit inmate records")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Delete inmate records")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} View inmate profiles")
        print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Search inmates")
        print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Update inmate status")
        print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Inmate Transfer Management")
        print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Inmate Release Management")
        print(f"{Fore.YELLOW}10.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            admit_inmate(client, access_token)
        elif choice == "2":
            show_all_inmates(client, access_token)
        elif choice == "3":
            update_inmate_record(client, access_token)
        elif choice == "4":
            delete_inmate_record(client, access_token)
        elif choice == "5":
            show_inmate_profile(client, access_token)
        elif choice == "6":
            search_inmates(client, access_token)
        elif choice == "7":
            set_inmate_status(client, access_token)
        elif choice == "8":
            manage_inmate_transfers(client, access_token)
        elif choice == "9":
            manage_inmate_releases(client, access_token)
        elif choice == "10":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def admit_inmate(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Admit inmates{Style.RESET_ALL}")

    print_section("Identification")
    inmate_id = prompt_required("Inmate ID")
    warrant_id = prompt_required_int("Arrest warrant ID")
    case_number = prompt_required("Case number")
    fingerprint_id = prompt_optional("Fingerprint ID")
    photo = prompt_optional("Photo path")

    print_section("Personal Information")
    first_name = prompt_required("First name")
    last_name = prompt_required("Last name")
    other_names = prompt_optional("Other names")
    date_of_birth = prompt_required("Date of birth (YYYY-MM-DD)")
    age = prompt_required_int("Age")
    gender = prompt_choice("Gender", sorted(INMATE_GENDERS))
    nationality = prompt_required("Nationality")
    national_id = prompt_optional("National ID")
    phone = prompt_optional("Phone")
    address = prompt_optional("Address")
    marital_status = prompt_choice("Marital status", sorted(INMATE_MARITAL_STATUSES))

    print_section("Physical Profile")
    height_cm = prompt_optional("Height in cm")
    weight_kg = prompt_optional("Weight in kg")
    eye_color = prompt_optional("Eye color")
    hair_color = prompt_optional("Hair color")
    distinguishing_marks = prompt_optional("Distinguishing marks")
    religion = prompt_optional("Religion")
    occupation = prompt_optional("Occupation")
    education_level = prompt_optional("Education level")

    print_section("Next of Kin")
    next_of_kin_name = prompt_required("Next of kin name")
    next_of_kin_relation = prompt_choice("Next of kin relation", sorted(INMATE_NEXT_OF_KIN_RELATIONS))
    next_of_kin_contact = prompt_optional("Next of kin contact")
    next_of_kin_address = prompt_optional("Next of kin address")

    print_section("Offense and Court")
    offense = prompt_required("Offense")
    offense_description = prompt_optional("Offense description")
    arrest_date = prompt_required("Arrest date (YYYY-MM-DD)")
    arresting_officer = prompt_required("Arresting officer")
    arresting_agency = prompt_required("Arresting agency")
    court = prompt_required("Court")
    judge = prompt_optional("Judge")
    sentence_type = prompt_choice("Sentence type", sorted(INMATE_SENTENCE_TYPES))
    sentence_duration = prompt_optional("Sentence duration")
    expected_release_date = prompt_optional("Expected release date (YYYY-MM-DD)")

    print_section("Admission")
    status = prompt_choice("Status", sorted(INMATE_STATUSES))
    admission_date = prompt_required("Admission date (YYYY-MM-DD)")
    admission_time = prompt_required("Admission time (HH:MM)")
    admission_officer_id = prompt_required_int("Admission officer user ID")

    payload = clean_payload({
        "inmate_id": inmate_id,
        "warrant_id": warrant_id,
        "first_name": first_name,
        "last_name": last_name,
        "other_names": other_names,
        "date_of_birth": date_of_birth,
        "age": age,
        "gender": gender,
        "nationality": nationality,
        "national_id": national_id,
        "phone": phone,
        "address": address,
        "marital_status": marital_status,
        "photo": photo,
        "fingerprint_id": fingerprint_id,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "eye_color": eye_color,
        "hair_color": hair_color,
        "distinguishing_marks": distinguishing_marks,
        "religion": religion,
        "occupation": occupation,
        "education_level": education_level,
        "next_of_kin_name": next_of_kin_name,
        "next_of_kin_relation": next_of_kin_relation,
        "next_of_kin_contact": next_of_kin_contact,
        "next_of_kin_address": next_of_kin_address,
        "case_number": case_number,
        "offense": offense,
        "offense_description": offense_description,
        "arrest_date": arrest_date,
        "arresting_officer": arresting_officer,
        "arresting_agency": arresting_agency,
        "court": court,
        "judge": judge,
        "sentence_type": sentence_type,
        "sentence_duration": sentence_duration,
        "expected_release_date": expected_release_date,
        "status": status,
        "admission_date": admission_date,
        "admission_time": admission_time,
        "admission_officer_id": admission_officer_id,
    })

    response = client.post(
        "/api/v1/inmates",
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 201:
        print_api_error("Admission failed", body)
        return

    inmate = body.get("inmate", {})
    print(f"{Fore.GREEN}Inmate admitted:{Style.RESET_ALL} {inmate.get('inmate_id')} - {inmate.get('first_name')} {inmate.get('last_name')}")


def show_all_inmates(client, access_token: str) -> None:
    query = view_all_inmates_filter()
    response = client.get(
        "/api/v1/inmates",
        query_string=query,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Failed to load inmates", body)
        return
    print_selected_inmate_filter(query)
    print_inmate_table(body)


def search_inmates(client, access_token: str) -> None:
    query = search_inmate_filters()
    response = client.get(
        "/api/v1/inmates/search",
        query_string=query,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Search failed", body)
        return
    print_selected_inmate_filter(query)
    print_inmate_table(body)


def show_inmate_profile(client, access_token: str) -> None:
    endpoint = prompt_inmate_lookup_endpoint()
    response = client.get(
        endpoint,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Failed to load inmate profile", body)
        return
    inmate = body.get("inmate")
    if not isinstance(inmate, dict):
        print(f"{Fore.RED}Failed to load inmate profile:{Style.RESET_ALL} invalid response.")
        return
    print_inmate_details(inmate)


def update_inmate_record(client, access_token: str) -> None:
    inmate_db_id = prompt_required_int("Inmate database ID")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Edit inmate records{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Leave a field blank to keep the current value.{Style.RESET_ALL}")

    updates = clean_payload({
        "inmate_id": prompt_optional("Inmate ID"),
        "warrant_id": prompt_optional_int("Arrest warrant ID"),
        "first_name": prompt_optional("First name"),
        "last_name": prompt_optional("Last name"),
        "other_names": prompt_optional("Other names"),
        "date_of_birth": prompt_optional("Date of birth (YYYY-MM-DD)"),
        "age": prompt_optional_int("Age"),
        "gender": prompt_optional_choice("Gender", sorted(INMATE_GENDERS)),
        "nationality": prompt_optional("Nationality"),
        "national_id": prompt_optional("National ID"),
        "phone": prompt_optional("Phone"),
        "address": prompt_optional("Address"),
        "marital_status": prompt_optional_choice("Marital status", sorted(INMATE_MARITAL_STATUSES)),
        "photo": prompt_optional("Photo path"),
        "fingerprint_id": prompt_optional("Fingerprint ID"),
        "height_cm": prompt_optional("Height in cm"),
        "weight_kg": prompt_optional("Weight in kg"),
        "eye_color": prompt_optional("Eye color"),
        "hair_color": prompt_optional("Hair color"),
        "distinguishing_marks": prompt_optional("Distinguishing marks"),
        "religion": prompt_optional("Religion"),
        "occupation": prompt_optional("Occupation"),
        "education_level": prompt_optional("Education level"),
        "next_of_kin_name": prompt_optional("Next of kin name"),
        "next_of_kin_relation": prompt_optional_choice("Next of kin relation", sorted(INMATE_NEXT_OF_KIN_RELATIONS)),
        "next_of_kin_contact": prompt_optional("Next of kin contact"),
        "next_of_kin_address": prompt_optional("Next of kin address"),
        "case_number": prompt_optional("Case number"),
        "offense": prompt_optional("Offense"),
        "offense_description": prompt_optional("Offense description"),
        "arrest_date": prompt_optional("Arrest date (YYYY-MM-DD)"),
        "arresting_officer": prompt_optional("Arresting officer"),
        "arresting_agency": prompt_optional("Arresting agency"),
        "court": prompt_optional("Court"),
        "judge": prompt_optional("Judge"),
        "sentence_type": prompt_optional_choice("Sentence type", sorted(INMATE_SENTENCE_TYPES)),
        "sentence_duration": prompt_optional("Sentence duration"),
        "expected_release_date": prompt_optional("Expected release date (YYYY-MM-DD)"),
        "status": prompt_optional_choice("Status", sorted(INMATE_STATUSES)),
        "admission_date": prompt_optional("Admission date (YYYY-MM-DD)"),
        "admission_time": prompt_optional("Admission time (HH:MM)"),
        "admission_officer_id": prompt_optional_int("Admission officer user ID"),
    })

    if not updates:
        print(f"{Fore.YELLOW}No updates entered.{Style.RESET_ALL}")
        return

    response = client.patch(
        f"/api/v1/inmates/{inmate_db_id}",
        json=updates,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Update failed", body)
        return

    print(f"{Fore.GREEN}Inmate updated successfully.{Style.RESET_ALL}")
    inmate = body.get("inmate")
    if isinstance(inmate, dict):
        print_inmate_details(inmate)


def set_inmate_status(client, access_token: str) -> None:
    inmate_db_id = prompt_required_int("Inmate database ID")
    status = prompt_choice("Status", sorted(INMATE_STATUSES))
    response = client.patch(
        f"/api/v1/inmates/{inmate_db_id}/status",
        json={"status": status},
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Status update failed", body)
        return
    inmate = body.get("inmate", {})
    print(f"{Fore.GREEN}Inmate status updated:{Style.RESET_ALL} {inmate.get('inmate_id')} -> {inmate.get('status')}")


def manage_inmate_transfers(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Inmate Transfer Management{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Create transfer request")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Review transfer")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Legal verification")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Security assessment")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Medical clearance")
        print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Approve transfer")
        print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Reject transfer")
        print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Assign transportation")
        print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Authorize movement")
        print(f"{Fore.YELLOW}10.{Style.RESET_ALL} Execute transfer")
        print(f"{Fore.YELLOW}11.{Style.RESET_ALL} Confirm arrival")
        print(f"{Fore.YELLOW}12.{Style.RESET_ALL} Complete transfer")
        print(f"{Fore.YELLOW}13.{Style.RESET_ALL} Cancel transfer")
        print(f"{Fore.YELLOW}14.{Style.RESET_ALL} View transfer history")
        print(f"{Fore.YELLOW}15.{Style.RESET_ALL} Search transfers")
        print(f"{Fore.YELLOW}16.{Style.RESET_ALL} Transfer reports")
        print(f"{Fore.YELLOW}17.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            create_transfer_request(client, access_token)
        elif choice == "2":
            patch_transfer(client, access_token, "review", {})
        elif choice == "3":
            patch_transfer(client, access_token, "legal-verification", {"legal_verified": prompt_bool("Legal verified")})
        elif choice == "4":
            patch_transfer(client, access_token, "security-assessment", {"security_assessed": prompt_bool("Security assessed")})
        elif choice == "5":
            patch_transfer(client, access_token, "medical-clearance", {"medical_clearance": prompt_bool("Medical clearance")})
        elif choice == "6":
            patch_transfer(client, access_token, "approve", {})
        elif choice == "7":
            patch_transfer(client, access_token, "reject", {"reason": prompt_required("Rejection reason")})
        elif choice == "8":
            patch_transfer(client, access_token, "transportation", clean_payload({
                "escort_officers": prompt_required("Escort officers"),
                "transport_vehicle": prompt_required("Transport vehicle"),
                "route_details": prompt_optional("Route details"),
            }))
        elif choice == "9":
            patch_transfer(client, access_token, "authorize-movement", {})
        elif choice == "10":
            patch_transfer(client, access_token, "execute", {"departure_date": prompt_required("Departure date (YYYY-MM-DD)")})
        elif choice == "11":
            patch_transfer(client, access_token, "confirm-arrival", {
                "arrival_date": prompt_required("Arrival date (YYYY-MM-DD)"),
                "receiving_officer": prompt_required("Receiving officer"),
                "receiving_confirmation": prompt_bool("Receiving confirmation"),
            })
        elif choice == "12":
            patch_transfer(client, access_token, "complete", clean_payload({"transfer_completion_notes": prompt_optional("Completion notes")}))
        elif choice == "13":
            patch_transfer(client, access_token, "cancel", {"reason": prompt_required("Cancellation reason")})
        elif choice == "14":
            view_transfer_history(client, access_token)
        elif choice == "15":
            search_transfers(client, access_token)
        elif choice == "16":
            view_transfer_reports(client, access_token)
        elif choice == "17":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def create_transfer_request(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Create Transfer Request{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "current_facility": prompt_required("Current facility"),
        "destination_facility": prompt_required("Destination facility"),
        "transfer_type": prompt_exact_choice("Transfer type", sorted(INMATE_TRANSFER_TYPES)),
        "reason": prompt_required("Reason"),
        "security_level": prompt_required("Security level"),
        "urgency_level": prompt_required("Urgency level"),
        "requested_date": prompt_required("Requested date (YYYY-MM-DD)"),
    })
    response = client.post(
        "/api/v1/inmates/transfers",
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 201:
        print_api_error("Transfer request failed", body)
        return
    print(f"{Fore.GREEN}Transfer request created.{Style.RESET_ALL}")
    print_record_details(body.get("transfer", {}))


def patch_transfer(client, access_token: str, action: str, payload: dict[str, object]) -> None:
    transfer_id = prompt_required_int("Transfer ID")
    response = client.patch(
        f"/api/v1/inmates/transfers/{transfer_id}/{action}",
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Transfer workflow failed", body)
        return
    print(f"{Fore.GREEN}Transfer workflow updated.{Style.RESET_ALL}")
    print_record_details(body.get("transfer", {}))


def view_transfer_history(client, access_token: str) -> None:
    inmate_db_id = prompt_required_int("Inmate database ID")
    response = client.get(
        f"/api/v1/inmates/{inmate_db_id}/transfers",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Transfer history failed", body)
        return
    print_record_list("Transfers", body.get("transfers"))


def search_transfers(client, access_token: str) -> None:
    query = clean_payload({
        "inmate_id": prompt_optional_int("Inmate database ID"),
        "transfer_type": prompt_optional_exact_choice("Transfer type", sorted(INMATE_TRANSFER_TYPES)),
        "transfer_status": prompt_optional("Transfer status"),
        "facility": prompt_optional("Facility"),
        "date_from": prompt_optional("Requested date from (YYYY-MM-DD)"),
        "date_to": prompt_optional("Requested date to (YYYY-MM-DD)"),
        "approved_by": prompt_optional_int("Approved by user ID"),
    })
    response = client.get(
        "/api/v1/inmates/transfers",
        query_string=query,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Transfer search failed", body)
        return
    print_record_list("Transfers", body.get("transfers"))


def view_transfer_reports(client, access_token: str) -> None:
    response = client.get(
        "/api/v1/inmates/transfers/reports",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Transfer reports failed", body)
        return
    print_record_list("Transfer Reports", body.get("transfer_reports"))


def manage_inmate_releases(client, access_token: str) -> None:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Inmate Release Management{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Initiate release review")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Legal verification")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Sentence validation")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Medical clearance")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Property clearance")
        print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Identity verification")
        print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Approve release")
        print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Reject release")
        print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Generate release documents")
        print(f"{Fore.YELLOW}10.{Style.RESET_ALL} Execute inmate release")
        print(f"{Fore.YELLOW}11.{Style.RESET_ALL} View release history")
        print(f"{Fore.YELLOW}12.{Style.RESET_ALL} Search releases")
        print(f"{Fore.YELLOW}13.{Style.RESET_ALL} Release reports")
        print(f"{Fore.YELLOW}14.{Style.RESET_ALL} Back")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            initiate_release_review(client, access_token)
        elif choice == "2":
            patch_release(client, access_token, "legal-verification", {"legal_verified": prompt_bool("Legal verified")})
        elif choice == "3":
            patch_release(client, access_token, "sentence-validation", {"sentence_validated": prompt_bool("Sentence validated")})
        elif choice == "4":
            patch_release(client, access_token, "medical-clearance", clean_payload({
                "medical_cleared": prompt_bool("Medical cleared"),
                "medical_discharge_summary": prompt_optional("Medical discharge summary"),
            }))
        elif choice == "5":
            patch_release(client, access_token, "property-clearance", clean_payload({
                "property_cleared": prompt_bool("Property cleared"),
                "property_release_notes": prompt_optional("Property release notes"),
            }))
        elif choice == "6":
            patch_release(client, access_token, "identity-verification", {
                "identity_verified": prompt_bool("Identity verified"),
                "discharge_notes": prompt_required("Identity verification notes"),
            })
        elif choice == "7":
            patch_release(client, access_token, "approve", {})
        elif choice == "8":
            patch_release(client, access_token, "reject", {"reason": prompt_required("Rejection reason")})
        elif choice == "9":
            patch_release(client, access_token, "documents", clean_payload({
                "release_certificate_number": prompt_required("Release certificate number"),
                "discharge_notes": prompt_optional("Discharge notes"),
            }))
        elif choice == "10":
            patch_release(client, access_token, "execute", clean_payload({
                "release_date": prompt_required("Release date (YYYY-MM-DD)"),
                "release_time": prompt_required("Release time (HH:MM)"),
                "discharge_notes": prompt_optional("Discharge notes"),
            }))
        elif choice == "11":
            view_release_history(client, access_token)
        elif choice == "12":
            search_releases(client, access_token)
        elif choice == "13":
            view_release_reports(client, access_token)
        elif choice == "14":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def initiate_release_review(client, access_token: str) -> None:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Initiate Release Review{Style.RESET_ALL}")
    payload = clean_payload({
        "inmate_id": prompt_required_int("Inmate database ID"),
        "release_type": prompt_exact_choice("Release type", sorted(INMATE_RELEASE_TYPES)),
        "release_reason": prompt_required("Release reason"),
    })
    response = client.post(
        "/api/v1/inmates/releases",
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 201:
        print_api_error("Release review failed", body)
        return
    print(f"{Fore.GREEN}Release review initiated.{Style.RESET_ALL}")
    print_record_details(body.get("release", {}))


def patch_release(client, access_token: str, action: str, payload: dict[str, object]) -> None:
    release_id = prompt_required_int("Release ID")
    response = client.patch(
        f"/api/v1/inmates/releases/{release_id}/{action}",
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Release workflow failed", body)
        return
    print(f"{Fore.GREEN}Release workflow updated.{Style.RESET_ALL}")
    print_record_details(body.get("release", {}))


def view_release_history(client, access_token: str) -> None:
    inmate_db_id = prompt_required_int("Inmate database ID")
    response = client.get(
        f"/api/v1/inmates/{inmate_db_id}/releases",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Release history failed", body)
        return
    print_record_list("Releases", body.get("releases"))


def search_releases(client, access_token: str) -> None:
    query = clean_payload({
        "inmate_id": prompt_optional_int("Inmate database ID"),
        "release_type": prompt_optional_exact_choice("Release type", sorted(INMATE_RELEASE_TYPES)),
        "release_status": prompt_optional("Release status"),
        "date_from": prompt_optional("Release date from (YYYY-MM-DD)"),
        "date_to": prompt_optional("Release date to (YYYY-MM-DD)"),
        "approved_by": prompt_optional_int("Approved by user ID"),
    })
    response = client.get(
        "/api/v1/inmates/releases",
        query_string=query,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Release search failed", body)
        return
    print_record_list("Releases", body.get("releases"))


def view_release_reports(client, access_token: str) -> None:
    response = client.get(
        "/api/v1/inmates/releases/reports",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Release reports failed", body)
        return
    print_record_list("Release Reports", body.get("release_reports"))


def delete_inmate_record(client, access_token: str) -> None:
    inmate_db_id = prompt_required_int("Inmate database ID")
    confirm = input(f"{Fore.RED}Type DELETE to confirm inmate deletion:{Style.RESET_ALL} ").strip()
    if confirm != "DELETE":
        print(f"{Fore.YELLOW}Delete cancelled.{Style.RESET_ALL}")
        return

    response = client.delete(
        f"/api/v1/inmates/{inmate_db_id}",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}
    if response.status_code != 200:
        print_api_error("Delete failed", body)
        return
    inmate = body.get("inmate", {})
    print(f"{Fore.GREEN}Inmate deleted:{Style.RESET_ALL} {inmate.get('inmate_id')} - {inmate.get('first_name')} {inmate.get('last_name')}")


def prompt_inmate_lookup_endpoint() -> str:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Find Inmate By{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Database ID")
    print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Inmate ID")
    while True:
        choice = input(f"{Fore.CYAN}Select lookup option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            return f"/api/v1/inmates/{prompt_required_int('Inmate database ID')}"
        if choice == "2":
            return f"/api/v1/inmates/inmate-id/{prompt_required('Inmate ID')}"
        print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def view_all_inmates_filter() -> dict[str, object]:
    return _select_filter_option(
        "View all inmates",
        [
            ("female", {"gender": "female"}),
            ("male", {"gender": "male"}),
        ],
    )


def print_selected_inmate_filter(query: dict[str, object]) -> None:
    if not query:
        print(f"{Fore.GREEN}Showing all inmates.{Style.RESET_ALL}")
        return
    labels = []
    for field, value in query.items():
        label = "Status" if field == "status" else "Sentence Type" if field == "sentence_type" else "Gender"
        labels.append(f"{label}: {value}")
    print(f"{Fore.GREEN}Showing inmates by {Style.RESET_ALL}{', '.join(labels)}")


def search_inmate_filters() -> dict[str, object]:
    query: dict[str, object] = {}

    gender_filter = _select_filter_option(
        "Search inmates",
        [
            ("female", {"gender": "female"}),
            ("male", {"gender": "male"}),
        ],
    )
    if not gender_filter:
        return query
    query.update(gender_filter)

    second_filter = _select_filter_option(
        "Filter By",
        [
            ("active", {"status": "active"}),
            ("deceased", {"status": "deceased"}),
            ("released", {"status": "released"}),
            ("transferred", {"status": "transferred"}),
            ("convicted", {"sentence_type": "convicted"}),
            ("death", {"sentence_type": "death"}),
            ("life", {"sentence_type": "life"}),
            ("remand", {"sentence_type": "remand"}),
        ],
    )
    query.update(second_filter)
    return query


def _select_filter_option(title: str, filter_options: list[tuple[str, dict[str, str]]]) -> dict[str, str]:
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}0.{Style.RESET_ALL} Skip")
        for index, (label, _) in enumerate(filter_options, start=1):
            print(f"{Fore.YELLOW}{index}.{Style.RESET_ALL} {label}")

        choice = input(f"{Fore.CYAN}Select filter:{Style.RESET_ALL} ").strip()
        if choice in {"", "0"}:
            return {}
        if choice.isdigit():
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(filter_options):
                return dict(filter_options[selected_index][1])
        print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def optional_inmate_filters() -> dict[str, object]:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Optional Filters{Style.RESET_ALL}")
    filters = clean_payload({
        "gender": prompt_optional_choice("Gender", sorted(INMATE_GENDERS)),
        "nationality": prompt_optional("Nationality"),
        "admission_date": prompt_optional("Admission date (YYYY-MM-DD)"),
        "arrest_date": prompt_optional("Arrest date (YYYY-MM-DD)"),
        "status": prompt_optional_choice("Status", sorted(INMATE_STATUSES)),
        "sentence_type": prompt_optional_choice("Sentence type", sorted(INMATE_SENTENCE_TYPES)),
        "limit": prompt_optional_int("Limit"),
        "offset": prompt_optional_int("Offset"),
    })
    return filters


def print_inmate_table(body: dict) -> None:
    inmates = body.get("inmates")
    if not isinstance(inmates, list):
        print(f"{Fore.RED}Failed to load inmates:{Style.RESET_ALL} invalid response.")
        return
    if not inmates:
        print(f"{Fore.YELLOW}No inmates found.{Style.RESET_ALL}")
        return

    rows = []
    for inmate in inmates:
        if not isinstance(inmate, dict):
            continue
        rows.append([
            inmate.get("id"),
            inmate.get("inmate_id") or "",
            f"{inmate.get('first_name') or ''} {inmate.get('last_name') or ''}".strip(),
            inmate.get("case_number") or "",
            inmate.get("offense") or "",
            inmate.get("status") or "",
            inmate.get("sentence_type") or "",
            inmate.get("admission_date") or "",
        ])

    print(f"\n{Fore.GREEN}Inmates ({body.get('total', len(rows))}){Style.RESET_ALL}")
    print(tabulate(
        rows,
        headers=["ID", "Inmate ID", "Name", "Case Number", "Offense", "Status", "Sentence Type", "Admission Date"],
        tablefmt="grid",
    ))


def print_inmate_details(inmate: dict) -> None:
    rows = [
        ["Database ID", inmate.get("id")],
        ["Inmate ID", inmate.get("inmate_id")],
        ["Warrant ID", inmate.get("warrant_id")],
        ["Name", f"{inmate.get('first_name') or ''} {inmate.get('last_name') or ''}".strip()],
        ["Other Names", inmate.get("other_names")],
        ["Date of Birth", inmate.get("date_of_birth")],
        ["Age", inmate.get("age")],
        ["Gender", inmate.get("gender")],
        ["Nationality", inmate.get("nationality")],
        ["National ID", inmate.get("national_id")],
        ["Phone", inmate.get("phone")],
        ["Marital Status", inmate.get("marital_status")],
        ["Fingerprint ID", inmate.get("fingerprint_id")],
        ["Height CM", inmate.get("height_cm")],
        ["Weight KG", inmate.get("weight_kg")],
        ["Next of Kin", inmate.get("next_of_kin_name")],
        ["Next of Kin Relation", inmate.get("next_of_kin_relation")],
        ["Next of Kin Contact", inmate.get("next_of_kin_contact")],
        ["Case Number", inmate.get("case_number")],
        ["Offense", inmate.get("offense")],
        ["Arrest Date", inmate.get("arrest_date")],
        ["Arresting Officer", inmate.get("arresting_officer")],
        ["Arresting Agency", inmate.get("arresting_agency")],
        ["Court", inmate.get("court")],
        ["Judge", inmate.get("judge")],
        ["Sentence Type", inmate.get("sentence_type")],
        ["Sentence Duration", inmate.get("sentence_duration")],
        ["Expected Release Date", inmate.get("expected_release_date")],
        ["Status", inmate.get("status")],
        ["Admission Date", inmate.get("admission_date")],
        ["Admission Time", inmate.get("admission_time")],
        ["Admission Officer ID", inmate.get("admission_officer_id")],
        ["Created At", inmate.get("created_at")],
        ["Updated At", inmate.get("updated_at")],
    ]
    print(tabulate(rows, headers=["Field", "Value"], tablefmt="grid"))


def prompt_staff_lookup() -> dict[str, str]:
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Find Staff By{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Staff ID")
    print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Officer number")
    print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Badge number")
    print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Username")
    while True:
        choice = input(f"{Fore.CYAN}Select lookup option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            return {"staff_id": prompt_required("Staff ID")}
        if choice == "2":
            return {"officer_id": prompt_required("Officer number")}
        if choice == "3":
            return {"badge_number": prompt_required("Badge number")}
        if choice == "4":
            return {"username": prompt_required("Username")}
        print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def print_staff_details(user: dict) -> None:
    rows = [
        ["ID", user.get("id")],
        ["Staff ID", user.get("staff_id")],
        ["Officer ID", user.get("officer_id")],
        ["Badge Number", user.get("badge_number")],
        ["Username", user.get("username")],
        ["Name", user.get("full_name")],
        ["Gender", user.get("gender")],
        ["DOB", user.get("dob")],
        ["Email", user.get("email")],
        ["Phone", user.get("phone")],
        ["National ID", user.get("national_id")],
        ["Department", user.get("department")],
        ["Position", user.get("position") or user.get("rank")],
        ["Branch", user.get("branch")],
        ["Role", user.get("role")],
        ["Status", user.get("status")],
        ["Shift", user.get("shift")],
    ]
    print(tabulate(rows, headers=["Field", "Value"], tablefmt="grid"))


def add_admin(client, access_token: str | None) -> None:
    if not access_token:
        print(f"{Fore.YELLOW}Login as an admin or supervisor before adding an admin.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Add Admin{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Create system users such as prison officers, medical officers, records officers, and visitor officers.{Style.RESET_ALL}")
    print_section("Personal Information")
    first_name = prompt_required("First name")
    middle_name = prompt_optional("Middle name")
    last_name = prompt_required("Last name")
    gender = prompt_choice("Gender", ["male", "female"])
    dob = prompt_required("Date of birth (YYYY-MM-DD)")
    phone = prompt_optional("Phone number")
    email = prompt_required("Email address")
    national_id = prompt_required("National ID number")
    address = prompt_optional("Residential address")
    profile_image = prompt_optional("Profile image path")

    print_section("Employment Information")
    staff_id = prompt_required("Staff ID")
    officer_id = prompt_required("Officer ID (OFF001 format)")
    badge_number = prompt_required("Badge number")
    department = prompt_choice("Department", ["Prison", "Administration", "Medical", "Records", "Visitors", "Security"])
    position = prompt_required("Position")
    employment_date = prompt_required("Employment date (YYYY-MM-DD)")
    branch = prompt_required("Branch / Facility")
    shift = prompt_choice("Shift", ["morning", "afternoon", "night"])

    print_section("Account Information")
    username = prompt_required("Username")
    password = prompt_password()
    role = prompt_choice(
        "Role",
        ["admin", "officer", "supervisor", "medical_officer", "records_officer", "visitor_officer"],
    )
    status = prompt_choice("Account status", ["active", "inactive"])

    payload = {
        "officer_id": officer_id,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "gender": gender,
        "dob": dob,
        "email": email,
        "password": password,
        "phone": phone,
        "national_id": national_id,
        "address": address,
        "profile_image": profile_image,
        "staff_id": staff_id,
        "badge_number": badge_number,
        "rank": position,
        "department": department,
        "position": position,
        "employment_date": employment_date,
        "branch": branch,
        "username": username,
        "role": role,
        "status": status,
        "shift": shift,
        "date_joined": employment_date,
    }

    response = client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 201:
        print(f"{Fore.RED}Add admin failed:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        errors = body.get("errors")
        if isinstance(errors, dict):
            for field, message in errors.items():
                print(f"{Fore.YELLOW}{field}:{Style.RESET_ALL} {message}")
        return

    user = body.get("user", {})
    print(f"{Fore.GREEN}User created:{Style.RESET_ALL} {user.get('full_name')} ({user.get('officer_id')})")


def print_section(title: str) -> None:
    print(f"\n{Fore.BLUE}{Style.BRIGHT}{title}{Style.RESET_ALL}")


def prompt_required(label: str) -> str:
    while True:
        value = input(f"{Fore.CYAN}{label}:{Style.RESET_ALL} ").strip()
        if value:
            return value
        print(f"{Fore.RED}{label} is required.{Style.RESET_ALL}")


def prompt_required_int(label: str) -> int:
    while True:
        value = prompt_required(label)
        try:
            return int(value)
        except ValueError:
            print(f"{Fore.RED}{label} must be an integer.{Style.RESET_ALL}")


def prompt_optional(label: str) -> str | None:
    value = input(f"{Fore.CYAN}{label} (optional):{Style.RESET_ALL} ").strip()
    return value or None


def prompt_optional_int(label: str) -> int | None:
    value = prompt_optional(label)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        print(f"{Fore.RED}{label} must be an integer. Value skipped.{Style.RESET_ALL}")
        return None


def prompt_choice(label: str, options: list[str]) -> str:
    normalized_options = {option.lower(): option for option in options}
    while True:
        print(f"{Fore.CYAN}{label}:{Style.RESET_ALL}")
        for index, option in enumerate(options, start=1):
            print(f"  {Fore.YELLOW}{index}.{Style.RESET_ALL} {option}")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip().lower()
        if choice.isdigit():
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(options):
                return options[selected_index].lower()
        if choice in normalized_options:
            return normalized_options[choice].lower()
        print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")


def prompt_exact_choice(label: str, options: list[str]) -> str:
    normalized_options = {option.lower(): option for option in options}
    while True:
        print(f"{Fore.CYAN}{label}:{Style.RESET_ALL}")
        for index, option in enumerate(options, start=1):
            print(f"  {Fore.YELLOW}{index}.{Style.RESET_ALL} {option}")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice.isdigit():
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(options):
                return options[selected_index]
        selected = normalized_options.get(choice.lower())
        if selected:
            return selected
        print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")


def prompt_optional_choice(label: str, options: list[str]) -> str | None:
    normalized_options = {option.lower(): option for option in options}
    while True:
        print(f"{Fore.CYAN}{label} (optional):{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}0.{Style.RESET_ALL} Skip")
        for index, option in enumerate(options, start=1):
            print(f"  {Fore.YELLOW}{index}.{Style.RESET_ALL} {option}")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip().lower()
        if choice in {"", "0"}:
            return None
        if choice.isdigit():
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(options):
                return options[selected_index].lower()
        if choice in normalized_options:
            return normalized_options[choice].lower()
        print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")


def prompt_optional_exact_choice(label: str, options: list[str]) -> str | None:
    normalized_options = {option.lower(): option for option in options}
    while True:
        print(f"{Fore.CYAN}{label} (optional):{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}0.{Style.RESET_ALL} Skip")
        for index, option in enumerate(options, start=1):
            print(f"  {Fore.YELLOW}{index}.{Style.RESET_ALL} {option}")
        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice in {"", "0"}:
            return None
        if choice.isdigit():
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(options):
                return options[selected_index]
        selected = normalized_options.get(choice.lower())
        if selected:
            return selected
        print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")


def prompt_bool(label: str) -> bool:
    while True:
        value = input(f"{Fore.CYAN}{label} (yes/no):{Style.RESET_ALL} ").strip().lower()
        if value in {"yes", "y", "true", "1"}:
            return True
        if value in {"no", "n", "false", "0"}:
            return False
        print(f"{Fore.RED}{label} must be yes or no.{Style.RESET_ALL}")


def prompt_password() -> str:
    while True:
        password = getpass.getpass(f"{Fore.CYAN}Password:{Style.RESET_ALL} ")
        confirm_password = getpass.getpass(f"{Fore.CYAN}Confirm password:{Style.RESET_ALL} ")
        if password != confirm_password:
            print(f"{Fore.RED}Passwords do not match.{Style.RESET_ALL}")
            continue
        if not password:
            print(f"{Fore.RED}Password is required.{Style.RESET_ALL}")
            continue
        return password


def clean_payload(payload: dict[str, object]) -> dict[str, object]:
    return {field: value for field, value in payload.items() if value not in {None, ""}}


def print_api_error(prefix: str, body: dict) -> None:
    print(f"{Fore.RED}{prefix}:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
    errors = body.get("errors")
    if isinstance(errors, dict):
        for field, message in errors.items():
            print(f"{Fore.YELLOW}{field}:{Style.RESET_ALL} {message}")
    missing_permissions = body.get("missing_permissions")
    if isinstance(missing_permissions, list):
        print(f"{Fore.YELLOW}Missing permissions:{Style.RESET_ALL} {', '.join(missing_permissions)}")


if __name__ == "__main__":
    raise SystemExit(main())
