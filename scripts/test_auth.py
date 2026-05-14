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
            add_admin(client, access_token)
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
    print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Add Admin")
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
    refresh_token = body.get("refresh_token")
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


def add_admin(client, access_token: str | None) -> None:
    if not access_token:
        print(f"{Fore.YELLOW}Login as an admin or supervisor before adding an admin.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Add Admin{Style.RESET_ALL}")
    payload = {
        "officer_id": input(f"{Fore.CYAN}Officer ID:{Style.RESET_ALL} ").strip(),
        "first_name": input(f"{Fore.CYAN}First name:{Style.RESET_ALL} ").strip(),
        "last_name": input(f"{Fore.CYAN}Last name:{Style.RESET_ALL} ").strip(),
        "email": input(f"{Fore.CYAN}Email:{Style.RESET_ALL} ").strip(),
        "password": getpass.getpass(f"{Fore.CYAN}Password:{Style.RESET_ALL} "),
        "phone": input(f"{Fore.CYAN}Phone:{Style.RESET_ALL} ").strip(),
        "badge_number": input(f"{Fore.CYAN}Badge number:{Style.RESET_ALL} ").strip(),
        "rank": input(f"{Fore.CYAN}Rank:{Style.RESET_ALL} ").strip(),
        "department": input(f"{Fore.CYAN}Department:{Style.RESET_ALL} ").strip(),
        "shift": input(f"{Fore.CYAN}Shift (morning/afternoon/night):{Style.RESET_ALL} ").strip(),
        "date_joined": input(f"{Fore.CYAN}Date joined (YYYY-MM-DD):{Style.RESET_ALL} ").strip(),
        "role": "admin",
        "status": "active",
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
    print(f"{Fore.GREEN}Admin created:{Style.RESET_ALL} {user.get('full_name')} ({user.get('officer_id')})")


if __name__ == "__main__":
    raise SystemExit(main())
