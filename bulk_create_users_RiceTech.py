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
ORGANIZATION_NAME = " RICETECH Machinery India Pvt Ltd"

# IMPORTANT: Replace this with the REAL unique organization ID from the DB/API.
# Example: ORGANIZATION_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
ORGANIZATION_ID = "558935bf-2a05-4a38-8891-650dbc15db9d"

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
    " RICETECH Machinery India Pvt Ltd": [
        {
            "first_name": "Bhanu",
            "last_name": "Prakash",
            "email": "bhanuprakash.reddy@ricetechmachinery.com",
            "phone": "9440624435",
            "designation": "Managing Director",
        },
        {
            "first_name": "Tharakaram",
            "last_name": "Reddy",
            "email": "tharakaram.ts.redy@ricetechmachinery.com",
            "phone": "+91 94406 24436",
            "designation": "Executive Director",
        },
        {
            "first_name": "Santosh",
            "last_name": "Reddy",
            "email": "rsm_kmnr@ricetechmachinery.com",
            "phone": "+91 94406 24434",
            "designation": "Regional Sales Manager",
        },
        {
            "first_name": "Devender",
            "last_name": "Reddy",
            "email": "rsm_nzbd@ricetechmachinery.com",
            "phone": "+91 94406 24432",
            "designation": "Regional Sales Manager",
        },
        {
            "first_name": "Rajesh",
            "last_name": "Gande",
            "email": "rsm_mbnr@ricetechmachinery.com",
            "phone": "+91 94406 24437",
            "designation": "Regional Sales Manager",
        },
        {
            "first_name": "Surya",
            "last_name": "Abbireddy",
            "email": "rsm_srpt@ricetechmachinery.com",
            "phone": "+91 99639 93239",
            "designation": "Regional Sales Manager",
        },
        {
            "first_name": "Mahesh",
            "last_name": "Boppu",
            "email": "kmnr@ricetechmachinery.com",
            "phone": "+91 99639 93242",
            "designation": "Area Sales Manager",
        },
        {
            "first_name": "Ashruth",
            "last_name": "Gunnala",
            "email": "nzbd@ricetechmachinery.com",
            "phone": "+91 99639 93236",
            "designation": "Area Sales Manager",
        },
        {
            "first_name": "Ramesh",
            "last_name": "Bathula",
            "email": "mbnr@ricetechmachinery.com",
            "phone": "+91 99639 93248",
            "designation": "Area Sales Manager",
        },
        {
            "first_name": "Purnachandra",
            "last_name": "Battini",
            "email": "apcentral@ricetechmachinery.com",
            "phone": "+91 99639 93255",
            "designation": "Area Sales Manager",
        },
        {
            "first_name": "Chandrika",
            "last_name": "Sikhakolli",
            "email": "sales@ricetechmachinery.com",
            "phone": "+91 94406 24430",
            "designation": "Sr. Sales& Service Coordinator",
        },
        {
            "first_name": "Sudeep",
            "last_name": "Dutta",
            "email": "Sudeep.d@gmail.com",
            "phone": "+91 73311 17998",
            "designation": "Digital Mktg Executive & System Admin",
        },
        {
            "first_name": "Swaroop",
            "last_name": "Payarda",
            "email": "service@ricetechmachinery.com",
            "phone": "+91 94406 24438",
            "designation": "Senior Project Engineer",
        },
        {
            "first_name": "Rajendra",
            "last_name": "Prasad",
            "email": "spares@ricetechmachinery.com",
            "phone": "+91 99639 93238",
            "designation": "Senior Service Engineer",
        },
        {
            "first_name": "Naveen",
            "last_name": "Chitukula",
            "email": "support@ricetechmachinery.com",
            "phone": "+91 99639 93240",
            "designation": "MM Manager",
        },
        {
            "first_name": "BSS",
            "last_name": "Prasad Rao",
            "email": "rt_mr@ricetechmachinery.com",
            "phone": "+91 9281083865",
            "designation": "QC Manager",
        },
        {
            "first_name": "Balakrishna",
            "last_name": "Veluru",
            "email": "production@ricetechmachinery.com",
            "phone": "+91 9281083850",
            "designation": "Production Incharge",
        },
        {
            "first_name": "Bhaskar",
            "last_name": "Phanindra",
            "email": "stores@ricetechmachinery.com",
            "phone": "+91 9281083860",
            "designation": "Stores Incharge",
        },
        {
            "first_name": "Naveen",
            "last_name": "Ankesarapu",
            "email": "design@ricetechmachinery.com",
            "phone": "+91 9281083868",
            "designation": "Asst. Design Manager",
        },
        {
            "first_name": "Debajit",
            "last_name": "Roy",
            "email": "Debajit.r@gmail.com",
            "phone": "+91 99639 93231",
            "designation": "HR Manager",
        },
        {
            "first_name": "China",
            "last_name": "Swamy",
            "email": "china.s@gmail.com",
            "phone": "+91 99639 93244",
            "designation": "Accounts Manager",
        },
        {
            "first_name": "Indu",
            "last_name": "Relli",
            "email": "info@ricetechmachinery.com",
            "phone": "+91 95739 26999",
            "designation": "OKR Coordinator",
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
