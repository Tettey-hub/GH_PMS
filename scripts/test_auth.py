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
            show_coming_soon_menu("Inmate Management", [
                "Register inmates",
                "View all inmates",
                "Edit inmate records",
                "Delete inmate records",
                "View inmate profiles",
                "Approve inmate transfers",
                "Approve inmate releases",
            ])
        elif choice == "3":
            show_coming_soon_menu("Court and Sentence Management", [
                "Create court records",
                "Edit sentence records",
                "Approve sentence modifications",
                "Access legal documents",
                "Generate legal reports",
            ])
        elif choice == "4":
            show_coming_soon_menu("Medical Management", [
                "View medical records",
                "Access medical reports",
                "Monitor prison health statistics",
            ])
        elif choice == "5":
            show_coming_soon_menu("Visitor Management", [
                "Approve/reject visitor requests",
                "View visitor logs",
                "Blacklist visitors",
            ])
        elif choice == "6":
            show_coming_soon_menu("Housing and Movement Management", [
                "Manage prison blocks",
                "Assign inmate housing",
                "Approve inmate transfers",
                "Monitor occupancy levels",
            ])
        elif choice == "7":
            show_coming_soon_menu("Reporting and Analytics", [
                "Generate reports",
                "Access analytics dashboard",
                "Export reports",
                "View prison statistics",
            ])
        elif choice == "8":
            show_coming_soon_menu("System Administration", [
                "Configure system settings",
                "Manage roles",
                "Access audit logs",
                "Manage backups",
                "Monitor system activities",
            ])
        elif choice == "9":
            access_token, refresh_token, current_user = logout(client, access_token, refresh_token, current_user)
        elif choice == "10":
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
    print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Court and Sentence Management")
    print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Medical Management")
    print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Visitor Management")
    print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Housing and Movement Management")
    print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Reporting and Analytics")
    print(f"{Fore.YELLOW}8.{Style.RESET_ALL} System Administration")
    print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Log Out")
    print(f"{Fore.YELLOW}10.{Style.RESET_ALL} Exit")


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


def prompt_optional(label: str) -> str | None:
    value = input(f"{Fore.CYAN}{label} (optional):{Style.RESET_ALL} ").strip()
    return value or None


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


if __name__ == "__main__":
    raise SystemExit(main())
