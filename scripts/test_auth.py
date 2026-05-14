from __future__ import annotations

import getpass
import sys
from pathlib import Path

from colorama import Fore, Style, init


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
            access_token, refresh_token, current_user = logout(client, access_token, refresh_token, current_user)
        elif choice == "3":
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
    print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Log Out")
    print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Exit")


def login(client) -> tuple[str | None, str | None, dict | None]:
    email = input(f"{Fore.CYAN}Email:{Style.RESET_ALL} ").strip()
    password = getpass.getpass(f"{Fore.CYAN}Password:{Style.RESET_ALL} ")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
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
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} View Active User")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Back")

        choice = input(f"{Fore.CYAN}Select option:{Style.RESET_ALL} ").strip()
        if choice == "1":
            add_admin(client, access_token)
        elif choice == "2":
            show_active_user(client, access_token)
        elif choice == "3":
            return
        else:
            print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")


def show_active_user(client, access_token: str) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Host": "localhost", "Authorization": f"Bearer {access_token}"},
    )
    body = response.get_json(silent=True) or {}

    if response.status_code != 200:
        print(f"{Fore.RED}Failed to load active user:{Style.RESET_ALL} {body.get('error', 'Unknown error')}")
        return

    user = body.get("user")
    if not isinstance(user, dict):
        print(f"{Fore.RED}Failed to load active user:{Style.RESET_ALL} invalid response.")
        return

    print(f"{Fore.GREEN}Name:{Style.RESET_ALL} {user.get('full_name')}")
    print(f"{Fore.GREEN}Email:{Style.RESET_ALL} {user.get('email')}")
    print(f"{Fore.GREEN}Officer ID:{Style.RESET_ALL} {user.get('officer_id')}")
    print(f"{Fore.GREEN}Badge Number:{Style.RESET_ALL} {user.get('badge_number')}")
    print(f"{Fore.GREEN}Rank:{Style.RESET_ALL} {user.get('rank')}")
    print(f"{Fore.GREEN}Department:{Style.RESET_ALL} {user.get('department')}")
    print(f"{Fore.GREEN}Role:{Style.RESET_ALL} {user.get('role')}")
    print(f"{Fore.GREEN}Status:{Style.RESET_ALL} {user.get('status')}")


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
