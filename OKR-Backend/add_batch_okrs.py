import sys
from datetime import UTC, datetime
import uuid

import app.main  # Ensure all SQLAlchemy mappers are loaded
from app.batches.models import Batch
from app.batch_members.models import BatchMember
from app.core.database import SessionLocal
from app.my_okr.models import OKR
from app.organization_members.models import OrganizationMember
from app.users.models import User
from app.rbac.models import Role


OKRS_TEMPLATES = [
    {
        "role_type": "BATCH_ADMIN",
        "professional": {
            "objective": "Lead batch delivery and ensure 100% on-time milestone completion",
            "target": "100%",
            "key_results": "1. Conduct weekly sprint reviews and OKR check-ins\n2. Resolve blockers and hurdles within 24 hours\n3. Maintain 95%+ batch participation rate",
            "okr_type": "PROFESSIONAL",
            "tracker_enabled": True,
        },
        "personal": {
            "objective": "Enhance system architecture and engineering management skills",
            "target": "Completed",
            "key_results": "1. Complete 2 advanced architecture modules\n2. Mentor junior engineers on clean API design",
            "okr_type": "PERSONAL",
            "tracker_enabled": False,
        },
    },
    {
        "role_type": "EMPLOYEE",
        "professional": {
            "objective": "Design, implement, and test core microservices and API endpoints",
            "target": "90% Coverage",
            "key_results": "1. Deliver 100% of sprint backlog tasks on schedule\n2. Achieve >90% unit test coverage for new endpoints\n3. Zero critical security vulnerabilities in code reviews",
            "okr_type": "PROFESSIONAL",
            "tracker_enabled": True,
        },
        "personal": {
            "objective": "Master asynchronous programming and performance optimization in Python",
            "target": "Completed",
            "key_results": "1. Study asynchronous concurrency patterns\n2. Present 1 knowledge sharing session to the team",
            "okr_type": "PERSONAL",
            "tracker_enabled": False,
        },
    },
]


def seed_okrs_for_batch_users():
    db = SessionLocal()
    try:
        print("=" * 80)
        print("ADDING OKRS FOR USERS IN BATCHES")
        print("=" * 80)

        # 1. Fetch all active batches
        batches = (
            db.query(Batch)
            .filter(Batch.is_deleted.is_(False))
            .order_by(Batch.created_at.desc())
            .all()
        )

        if not batches:
            print("No active batches found in database!")
            return

        print(f"Found {len(batches)} active batch(es).")
        total_created = 0

        for batch in batches:
            print("\n" + "-" * 80)
            print(f"BATCH: {batch.name} (ID: {batch.id})")
            print(f"Organization ID: {batch.organization_id}")
            print("-" * 80)

            # Find all active members in this batch
            batch_members = (
                db.query(BatchMember)
                .filter(
                    BatchMember.batch_id == batch.id,
                    BatchMember.is_deleted.is_(False),
                    BatchMember.is_active.is_(True),
                )
                .all()
            )

            if not batch_members:
                print(f"  No active batch members found in {batch.name}.")
                continue

            print(f"  Found {len(batch_members)} member(s) in this batch:")

            for bm in batch_members:
                user = db.query(User).filter(User.id == bm.user_id).first()
                role = db.query(Role).filter(Role.id == bm.role_id).first()
                user_display = f"{user.first_name} {user.last_name} (@{user.username})" if user else str(bm.user_id)
                role_name = role.name.upper() if role else "UNKNOWN"

                # Find user's OrganizationMember record in this batch's organization
                org_member = (
                    db.query(OrganizationMember)
                    .filter(
                        OrganizationMember.user_id == bm.user_id,
                        OrganizationMember.organization_id == batch.organization_id,
                        OrganizationMember.is_deleted.is_(False),
                    )
                    .first()
                )

                if not org_member:
                    print(f"  [WARN] No OrganizationMember found for user {user_display} in org {batch.organization_id}. Skipping.")
                    continue

                # Determine template based on role
                template = OKRS_TEMPLATES[0] if "ADMIN" in role_name else OKRS_TEMPLATES[1]

                # Create Professional OKR
                prof_data = template["professional"]
                existing_prof = (
                    db.query(OKR)
                    .filter(
                        OKR.batch_id == batch.id,
                        OKR.assigned_to == org_member.id,
                        OKR.objective == prof_data["objective"],
                        OKR.is_deleted.is_(False),
                    )
                    .first()
                )

                if not existing_prof:
                    prof_okr = OKR(
                        batch_id=batch.id,
                        assigned_to=org_member.id,
                        objective=prof_data["objective"],
                        target=prof_data["target"],
                        key_results=prof_data["key_results"],
                        okr_type=prof_data["okr_type"],
                        tracker_enabled=prof_data["tracker_enabled"],
                        status="ACTIVE",
                        created_by=user.id if user else None,
                    )
                    db.add(prof_okr)
                    db.flush()
                    total_created += 1
                    print(f"  + Added PROFESSIONAL OKR for {user_display} ({role_name}):")
                    print(f"    Objective: '{prof_okr.objective}'")
                    print(f"    Target: {prof_okr.target} | Tracker Enabled: {prof_okr.tracker_enabled}")
                    print(f"    OKR ID: {prof_okr.id}")
                else:
                    print(f"  . Professional OKR already exists for {user_display}: '{existing_prof.objective}'")

                # Create Personal OKR
                pers_data = template["personal"]
                existing_pers = (
                    db.query(OKR)
                    .filter(
                        OKR.batch_id == batch.id,
                        OKR.assigned_to == org_member.id,
                        OKR.objective == pers_data["objective"],
                        OKR.is_deleted.is_(False),
                    )
                    .first()
                )

                if not existing_pers:
                    pers_okr = OKR(
                        batch_id=batch.id,
                        assigned_to=org_member.id,
                        objective=pers_data["objective"],
                        target=pers_data["target"],
                        key_results=pers_data["key_results"],
                        okr_type=pers_data["okr_type"],
                        tracker_enabled=pers_data["tracker_enabled"],
                        status="ACTIVE",
                        created_by=user.id if user else None,
                    )
                    db.add(pers_okr)
                    db.flush()
                    total_created += 1
                    print(f"  + Added PERSONAL OKR for {user_display} ({role_name}):")
                    print(f"    Objective: '{pers_okr.objective}'")
                    print(f"    Target: {pers_okr.target} | Tracker Enabled: {pers_okr.tracker_enabled}")
                    print(f"    OKR ID: {pers_okr.id}")
                else:
                    print(f"  . Personal OKR already exists for {user_display}: '{existing_pers.objective}'")

        db.commit()
        print("\n" + "=" * 80)
        print(f"SUCCESS: Added {total_created} new OKR(s) across batches!")
        print("=" * 80)

    except Exception as e:
        db.rollback()
        print(f"Error seeding OKRs: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_okrs_for_batch_users()
