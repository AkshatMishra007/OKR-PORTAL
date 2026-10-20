from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.organization_members.models import OrganizationMember


def create_organization_member(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    role_id: UUID,
    created_by: UUID | None = None,
    **kwargs,
) -> OrganizationMember:
    """
    Create a new OrganizationMember entity in the session without committing.
    Accepts **kwargs (e.g. legacy batch_id) and safely ignores them.
    """
    member = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        role_id=role_id,
        created_by=created_by,
    )

    db.add(member)

    return member


def create_member(
    db: Session,
    member: OrganizationMember,
):
    """
    Create a new organization member.
    """

    db.add(member)
    db.commit()
    db.refresh(member)

    return get_member_by_id(db, member.id)


def get_member_by_id(
    db: Session,
    member_id: UUID,
):
    """
    Get organization member by ID with eagerly loaded User, Role, and Organization relationships.
    """

    return (
        db.query(OrganizationMember)
        .options(
            joinedload(OrganizationMember.user),
            joinedload(OrganizationMember.role),
            joinedload(OrganizationMember.organization),
        )
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.is_deleted.is_(False),
        )
        .first()
    )


def get_member_by_user_and_organization(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
):
    """
    Check whether a user already belongs to an organization with eagerly loaded relationships.
    """

    return (
        db.query(OrganizationMember)
        .options(
            joinedload(OrganizationMember.user),
            joinedload(OrganizationMember.role),
            joinedload(OrganizationMember.organization),
        )
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_deleted.is_(False),
        )
        .first()
    )


def get_member_by_user_and_batch(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    batch_id: UUID,
) -> OrganizationMember | None:
    return get_member_by_user_and_organization(db, organization_id, user_id)


def get_member_by_user_and_role(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    role_id: UUID,
) -> OrganizationMember | None:
    """
    Fetch active member record for a specific user, organization, and role.
    """
    return (
        db.query(OrganizationMember)
        .options(
            joinedload(OrganizationMember.user),
            joinedload(OrganizationMember.role),
            joinedload(OrganizationMember.organization),
        )
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.role_id == role_id,
            OrganizationMember.is_active.is_(True),
            OrganizationMember.is_deleted.is_(False),
        )
        .first()
    )


def get_member_by_user_and_no_batch(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
) -> OrganizationMember | None:
    """
    Fetch active member record for a user in an organization.
    """
    return get_member_by_user_and_organization(db, organization_id, user_id)



from app.common.query import validate_and_apply_sorting
from app.users.models import User

ALLOWED_MEMBER_SORT_FIELDS = {
    "created_at": OrganizationMember.created_at,
    "joined_at": OrganizationMember.joined_at,
    "updated_at": OrganizationMember.updated_at,
}


def get_members(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    organization_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
):
    """
    Get organization members with optional filters, search, sorting, and eagerly loaded relationships.
    """

    query = (
        db.query(OrganizationMember)
        .options(
            joinedload(OrganizationMember.user),
            joinedload(OrganizationMember.role),
            joinedload(OrganizationMember.organization),
        )
        .filter(
            OrganizationMember.is_deleted.is_(False),
        )
    )

    if organization_id:
        query = query.filter(
            OrganizationMember.organization_id == organization_id
        )

    if user_id:
        query = query.filter(
            OrganizationMember.user_id == user_id
        )

    if role_id:
        query = query.filter(
            OrganizationMember.role_id == role_id
        )

    if is_active is not None:
        query = query.filter(
            OrganizationMember.is_active == is_active
        )

    if search:
        query = query.join(User, OrganizationMember.user_id == User.id).filter(
            (User.first_name.ilike(f"%{search}%"))
            | (User.last_name.ilike(f"%{search}%"))
            | (User.email.ilike(f"%{search}%"))
            | (User.username.ilike(f"%{search}%"))
        )

    if sort_by is not None:
        query = validate_and_apply_sorting(
            query=query,
            model=OrganizationMember,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sort_fields=ALLOWED_MEMBER_SORT_FIELDS,
            default_sort_column=OrganizationMember.created_at,
        )
    else:
        query = query.order_by(OrganizationMember.created_at.desc())

    return (
        query.offset(skip)
        .limit(limit)
        .all()
    )


def count_members(
    db: Session,
    organization_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = None,
    is_active: bool | None = None,
):
    """
    Count organization members.
    """

    query = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.is_deleted.is_(False),
        )
    )

    if organization_id:
        query = query.filter(
            OrganizationMember.organization_id == organization_id
        )

    if user_id:
        query = query.filter(
            OrganizationMember.user_id == user_id
        )

    if role_id:
        query = query.filter(
            OrganizationMember.role_id == role_id
        )

    if is_active is not None:
        query = query.filter(
            OrganizationMember.is_active == is_active
        )

    if search:
        query = query.join(User, OrganizationMember.user_id == User.id).filter(
            (User.first_name.ilike(f"%{search}%"))
            | (User.last_name.ilike(f"%{search}%"))
            | (User.email.ilike(f"%{search}%"))
            | (User.username.ilike(f"%{search}%"))
        )

    return query.count()


def update_member(
    db: Session,
    member: OrganizationMember,
):
    """
    Persist updated organization member and return with loaded relationships.
    """

    db.commit()
    db.refresh(member)

    return get_member_by_id(db, member.id)


def delete_member(
    db: Session,
    member: OrganizationMember,
):
    """
    Persist soft-deleted organization member.
    """

    db.commit()
    db.refresh(member)

    return member


def soft_delete_member(
    db: Session,
    member: OrganizationMember,
    updated_by: UUID | None = None,
) -> OrganizationMember:
    """
    Soft-delete an organization member without committing immediately.
    """
    member.is_deleted = True
    member.is_active = False
    member.deleted_at = datetime.now(UTC)
    member.updated_by = updated_by

    return member