#!/usr/bin/env python3
"""
Bulk-create OKR Portal Employee users.

IMPORTANT:
- This script does NOT read users from CSV/Excel at runtime.
- User data is hardcoded below, grouped by organization name.
- Before running, enter the correct unique organization ID for the
  organization you want to process.
- The script uses the same user-create API as Users.jsx:
      POST /api/users/

Authentication:
    PowerShell:
        $env:OKR_ACCESS_TOKEN="YOUR_FRESH_ACCESS_TOKEN"
        python bulk_create_users.py

    If OKR_ACCESS_TOKEN is not set, the script securely asks for it.
"""

import getpass
import os
import re
import sys

import requests


# ============================================================================
# CONFIGURATION - UPDATE THIS SECTION BEFORE RUNNING
# ============================================================================

# Same API base URL as frontend Config/ApiEndpoint.jsx.
API_URL = "https://okr.ssdntech.com".rstrip("/")

# Select the organization you want to create users for.
ORGANIZATION_NAME = "Paramtech Engineering Services Private Limited"

# IMPORTANT: Replace this with the REAL unique organization ID from the DB/API.
# Example: ORGANIZATION_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
ORGANIZATION_ID = "3e38c4a4-e7bf-4078-8d58-90144dcc10c3"

# All users created by this script will be Employees.
ROLE_NAME = "EMPLOYEE"

# Optional: If you already know the Employee role ID, put it here.
# Leave it as None to let the script fetch /api/roles/ and find EMPLOYEE.
ROLE_ID = None

# Initial password for all users.
# Leave as None to enter it securely when the script starts.
INITIAL_PASSWORD = "12345678"


# ============================================================================
# HARD-CODED USERS BY ORGANIZATION
# ============================================================================
# Do not edit the CSV. Add/update users here when preparing another
# organization. The organization name must match ORGANIZATION_NAME above.

ORGANIZATION_USERS = {
    "Paramtech Engineering Services Private Limited": [
        {
            "first_name": "Kusum",
            "last_name": "Khandagale",
            "email": "kusum@paramtechnologies.in",
            "phone": "9545427722",
            "designation": "HR Manager",
        },
        {
            "first_name": "Asmita",
            "last_name": "Sinkar",
            "email": "hr5@paramtechnologies.in",
            "phone": "9922880684",
            "designation": "HR Manager",
        },
        {
            "first_name": "Gaurav",
            "last_name": "Sawarkar",
            "email": "gaurav@paramtechnologies.in",
            "phone": "7387117477",
            "designation": "HR Manager",
        },
        {
            "first_name": "Ashwini",
            "last_name": "Yadav",
            "email": "hr3@paramtechnologies.in",
            "phone": "8767845435",
            "designation": "HR Executive",
        },
        {
            "first_name": "Sharanappa",
            "last_name": "Shivagond",
            "email": "sharanappa@paramtechnologies.in",
            "phone": "8554951345",
            "designation": "Manager-Product Development",
        },
        {
            "first_name": "Pranjali",
            "last_name": "Patil",
            "email": "pranjali@paramtechnologies.in",
            "phone": "9322331029",
            "designation": "Business Development Manager",
        },
        {
            "first_name": "Dhiraj",
            "last_name": "Patil",
            "email": "dhiraj@paramtechnologies.in",
            "phone": "7028239595",
            "designation": "Business Development Manager",
        },
        {
            "first_name": "Bhagyashree",
            "last_name": "Parate",
            "email": "Bhagyashree.p@gmail.com",
            "phone": "8459175514",
            "designation": "Finance Executive",
        },
        {
            "first_name": "Varsha",
            "last_name": "Duraphe",
            "email": "finance@paramtechnologies.in",
            "phone": "9423211865",
            "designation": "Account Manager",
        },
        {
            "first_name": "Hemansha",
            "last_name": "Ailani",
            "email": "hemansha@paramtechnologies.in",
            "phone": "8287135125",
            "designation": "Accounts Relationship Manager",
        },
        {
            "first_name": "Saurabh",
            "last_name": "Singh",
            "email": "saurabh@paramtechnologies.in",
            "phone": "8770267488",
            "designation": "Operation Manager",
        },
        {
            "first_name": "Sugandhita",
            "last_name": "Arora",
            "email": "sugandhitaa@paramtechnologies.in",
            "phone": "8295152264",
            "designation": "Asst. Finance Executive",
        },
        {
            "first_name": "Chandni",
            "last_name": "Khatri",
            "email": "hr2@paramtechnologies.in",
            "phone": "7350905079",
            "designation": "Compliance & Strategy Manager",
        },
        {
            "first_name": "Ritika",
            "last_name": "Bilodiya",
            "email": "ritika@paramtechnologies.in",
            "phone": "9993644034",
            "designation": "HR Intern",
        },
        {
            "first_name": "Priyanka",
            "last_name": "Doifode",
            "email": "priyanka@paramtechnologies.in",
            "phone": "7057062115",
            "designation": "HR Executive",
        },
        {
            "first_name": "Mohini",
            "last_name": "Madhavkar",
            "email": "mohinee@paramtechengineering.com",
            "phone": "9284043341",
            "designation": "HR Intern",
        },
        {
            "first_name": "Anjali",
            "last_name": "Vishwakarma",
            "email": "anjali@paramtechengineering.com",
            "phone": "7067754922",
            "designation": "HR Executive",
        },
        {
            "first_name": "Vaishnavi",
            "last_name": "Kumbhar",
            "email": "savi@paramtechengineering.com",
            "phone": "7218829914",
            "designation": "HR Intern",
        },
        {
            "first_name": "Kanchan",
            "last_name": "Birkare",
            "email": "kanchan@paramtechnologies.in",
            "phone": "7350828274",
            "designation": "HR Executive",
        },
        {
            "first_name": "Aditi",
            "last_name": "Avhad",
            "email": "aditi@paramtechnologies.in",
            "phone": "8379996018",
            "designation": "HR Executive",
        },
        {
            "first_name": "Vaishnavi",
            "last_name": "Lad",
            "email": "vaishnavi@paramtechengineering.com",
            "phone": "7387273753",
            "designation": "HR Intern",
        },
        {
            "first_name": "Gauri",
            "last_name": "Bahulekar",
            "email": "gauri@paramtechengineering.com",
            "phone": "7030140061",
            "designation": "HR Executive",
        },
        {
            "first_name": "Vedika",
            "last_name": "Pawar",
            "email": "vedika@paramtechengineering.com",
            "phone": "8839931586",
            "designation": "HR Intern",
        },
        {
            "first_name": "Shrutika",
            "last_name": "Shinde",
            "email": "shrutika@paramtechengineering.com",
            "phone": "7972569611",
            "designation": "HR Intern",
        },
        {
            "first_name": "Sonali",
            "last_name": "Kalel",
            "email": "sonali@paramtechengineering.com",
            "phone": "7249705363",
            "designation": "HR Executive",
        },
        {
            "first_name": "Gaytri",
            "last_name": "Sonavane",
            "email": "gayatri@paramtechengineering.com",
            "phone": "9322702979",
            "designation": "HR Executive",
        },
        {
            "first_name": "Anushka",
            "last_name": "Sharma",
            "email": "anushka@paramtechengineering.com",
            "phone": "9302097988",
            "designation": "HR Intern",
        },
        {
            "first_name": "Mohini",
            "last_name": "Gaikwad",
            "email": "mohini@paramtechengineering.com",
            "phone": "8551061517",
            "designation": "HR Executive",
        },
        {
            "first_name": "Aparna",
            "last_name": "Misal",
            "email": "aparna@paramtechengineering.com",
            "phone": "8766599535",
            "designation": "HR Intern",
        },
        {
            "first_name": "Kirti",
            "last_name": "Ojha",
            "email": "kirti@paramtechengineering.com",
            "phone": "9009309187",
            "designation": "HR Executive",
        },
        {
            "first_name": "Vaibhavi",
            "last_name": "Badarkhe",
            "email": "vaibhavi@paramtechengineering.com",
            "phone": "9112759609",
            "designation": "HR Intern",
        },
        {
            "first_name": "Shrutika",
            "last_name": "Shinde",
            "email": "shrutika.s@gmail.com",
            "phone": "7972569611",
            "designation": "HR Intern",
        },
        {
            "first_name": "Arun Kumar",
            "last_name": "V",
            "email": "executive@paramtechnologies.in",
            "phone": "9535331836",
            "designation": "Business Development Manager",
        },
        {
            "first_name": "Tamilarasu",
            "last_name": "M A",
            "email": "tamil@paramtechengineering.com",
            "phone": "9944050274",
            "designation": "Business Development Manager",
        },
        {
            "first_name": "Divith",
            "last_name": "Sivakumar",
            "email": "divith@paramtechengineering.com",
            "phone": "8012415199",
            "designation": "Business Development Manager",
        },
        {
            "first_name": "Raj",
            "last_name": "Patel",
            "email": "patelraj9909@gmail.com",
            "phone": "7567267141",
            "designation": "Sr. Executive",
        },
        {
            "first_name": "Nikita",
            "last_name": "Jhala",
            "email": "nikitajhala@paramtechnologies.in",
            "phone": "9165730884",
            "designation": "Relationship Executive",
        },
        {
            "first_name": "Swapnil",
            "last_name": "Mahajan",
            "email": "swapnil@paramtechengineering.com",
            "phone": "6261590010",
            "designation": "Relationship Executive",
        },
        {
            "first_name": "Muthu Kumar",
            "last_name": "B",
            "email": "am_chennai@paramtechnologies.in",
            "phone": "6383638450",
            "designation": "Relationship Executive",
        },
        {
            "first_name": "Tejal",
            "last_name": "Navalakar",
            "email": "tejaln@paramtechnologies.in",
            "phone": "8607275429",
            "designation": "Finance Operation Executive",
        },
    ],
}


ORGANIZATIONS_ENDPOINT = "/api/organizations/"
ROLES_ENDPOINT = "/api/roles/"
CREATE_USER_ENDPOINT = "/api/users/"
REQUEST_TIMEOUT = 30


def normalize(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_role_name(value):
    return normalize(value).upper().replace(" ", "_")


def make_username(first_name, last_name, email):
    """Generate username from email prefix, matching the previous script."""
    email = normalize(email)
    first_name = normalize(first_name)
    last_name = normalize(last_name)

    if email and "@" in email:
        username = email.split("@", 1)[0]
    else:
        username = f"{first_name}.{last_name}".strip(".")

    username = username.lower()
    username = re.sub(r"[^a-z0-9._-]+", "", username)
    return username.strip("._-")


def api_headers(token):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def get_role_id(session, token):
    """Fetch Employee role ID unless ROLE_ID is manually configured."""
    if ROLE_ID:
        return ROLE_ID, ROLE_NAME

    response = session.get(
        f"{API_URL}{ROLES_ENDPOINT}?page=1&size=100",
        headers=api_headers(token),
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise RuntimeError(
            f"Unable to fetch roles ({response.status_code}): {response.text}"
        )

    data = response.json()
    roles = data.get("data", []) if isinstance(data, dict) else data

    target = normalize_role_name(ROLE_NAME)

    for role in roles or []:
        if normalize_role_name(role.get("name")) == target:
            return role.get("id"), role.get("name")

    available = [
        normalize(role.get("name"))
        for role in roles or []
        if normalize(role.get("name"))
    ]

    raise RuntimeError(
        f"Role '{ROLE_NAME}' was not found. Available roles: {', '.join(available)}"
    )


def build_user_payload(user, role_id, password):
    first_name = normalize(user.get("first_name"))
    last_name = normalize(user.get("last_name"))
    email = normalize(user.get("email"))
    phone = normalize(user.get("phone"))
    designation = normalize(user.get("designation"))

    if not first_name:
        raise ValueError("First name is missing")
    if not email:
        raise ValueError("Email is missing")

    username = make_username(first_name, last_name, email)

    if not username:
        raise ValueError("Could not generate username")

    return {
        "username": username,
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "designation": designation,
        "organization_id": ORGANIZATION_ID,
        "role_id": role_id,
        "description": "",
    }


def create_user(session, token, payload):
    response = session.post(
        f"{API_URL}{CREATE_USER_ENDPOINT}",
        headers=api_headers(token),
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    if response.ok:
        try:
            return True, response.json()
        except ValueError:
            return True, {}

    try:
        error_data = response.json()
        detail = (
            error_data.get("detail", error_data)
            if isinstance(error_data, dict)
            else error_data
        )

        if isinstance(detail, list):
            detail = "; ".join(
                item.get("msg", str(item))
                if isinstance(item, dict)
                else str(item)
                for item in detail
            )

        return False, f"{response.status_code}: {detail}"

    except ValueError:
        return False, f"{response.status_code}: {response.text}"


def process_users(session, token, role_id, role_name, users, password):
    results = []

    print()
    print("=" * 72)
    print(f"Organization    : {ORGANIZATION_NAME}")
    print(f"Organization ID : {ORGANIZATION_ID}")
    print(f"Role            : {role_name}")
    print(f"Role ID         : {role_id}")
    print(f"Users           : {len(users)}")
    print("=" * 72)

    for index, user in enumerate(users, start=1):
        email = normalize(user.get("email"))
        display_name = (
            f"{normalize(user.get('first_name'))} "
            f"{normalize(user.get('last_name'))}"
        ).strip()
        username = make_username(
            user.get("first_name"),
            user.get("last_name"),
            email,
        )

        try:
            payload = build_user_payload(
                user=user,
                role_id=role_id,
                password=password,
            )

            print(
                f"[{index:>3}/{len(users)}] {email:<40} ",
                end="",
                flush=True,
            )

            success, response = create_user(
                session=session,
                token=token,
                payload=payload,
            )

            if success:
                created_id = (
                    response.get("id")
                    if isinstance(response, dict)
                    else ""
                )
                print("SUCCESS")
                results.append({
                    "organization": ORGANIZATION_NAME,
                    "organization_id": ORGANIZATION_ID,
                    "name": display_name,
                    "email": email,
                    "username": username,
                    "status": "SUCCESS",
                    "user_id": created_id or "",
                    "error": "",
                })
            else:
                print(f"FAILED - {response}")
                results.append({
                    "organization": ORGANIZATION_NAME,
                    "organization_id": ORGANIZATION_ID,
                    "name": display_name,
                    "email": email,
                    "username": username,
                    "status": "FAILED",
                    "user_id": "",
                    "error": str(response),
                })

        except Exception as error:
            print(f"FAILED - {error}")
            results.append({
                "organization": ORGANIZATION_NAME,
                "organization_id": ORGANIZATION_ID,
                "name": display_name,
                "email": email,
                "username": username,
                "status": "FAILED",
                "user_id": "",
                "error": str(error),
            })

    return results


def save_results(results, output_file="bulk_create_results.csv"):
    import csv

    fieldnames = [
        "organization",
        "organization_id",
        "name",
        "email",
        "username",
        "status",
        "user_id",
        "error",
    ]

    with open(output_file, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    # ------------------------------------------------------------------------
    # Validate hardcoded organization configuration.
    # ------------------------------------------------------------------------
    if ORGANIZATION_NAME not in ORGANIZATION_USERS:
        print(
            f"ERROR: No hardcoded users found for '{ORGANIZATION_NAME}'."
        )
        print(
            "Available organizations:",
            ", ".join(ORGANIZATION_USERS.keys()),
        )
        sys.exit(1)

    if not ORGANIZATION_ID or ORGANIZATION_ID == "ENTER_ORGANIZATION_ID_HERE":
        print("ERROR: Set ORGANIZATION_ID at the top of the script before running.")
        sys.exit(1)

    users = ORGANIZATION_USERS[ORGANIZATION_NAME]

    if not users:
        print(f"ERROR: No users configured for '{ORGANIZATION_NAME}'.")
        sys.exit(1)

    token = os.getenv("OKR_ACCESS_TOKEN")
    if not token:
        token = getpass.getpass("Enter the OKR access token: ").strip()

    if not token:
        print("ERROR: Access token is required.")
        sys.exit(1)

    password = INITIAL_PASSWORD
    if not password:
        password = getpass.getpass(
            "Enter initial password for all users: "
        )

    if not password:
        print("ERROR: Password is required.")
        sys.exit(1)

    if len(password) < 8:
        print("ERROR: Password should be at least 8 characters.")
        sys.exit(1)

    try:
        session = requests.Session()

        print(f"Looking up role '{ROLE_NAME}'...")
        role_id, resolved_role_name = get_role_id(session, token)

        results = process_users(
            session=session,
            token=token,
            role_id=role_id,
            role_name=resolved_role_name,
            users=users,
            password=password,
        )

        output_file = "bulk_create_results.csv"
        save_results(results, output_file)

        success_count = sum(
            result["status"] == "SUCCESS" for result in results
        )
        failed_count = len(results) - success_count

        print()
        print("=" * 72)
        print("SUMMARY")
        print("=" * 72)
        print(f"Total   : {len(results)}")
        print(f"Success : {success_count}")
        print(f"Failed  : {failed_count}")
        print(f"Results : {output_file}")
        print("=" * 72)

        if failed_count:
            sys.exit(2)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(130)
    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
