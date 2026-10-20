from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.organizations.models import Organization


def create_organization(
    db: Session,
    organization: Organization,
):
    """
    Save organization record.
    """

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization


def get_organization_by_id(
    db: Session,
    organization_id,
):
    """
    Fetch organization by ID.
    """

    return (
        db.query(Organization)
        .filter(
            Organization.id == organization_id,
            Organization.is_deleted == False,
        )
        .first()
    )


def get_organization_by_name(
    db: Session,
    name: str,
):
    """
    Check organization name exists.
    """

    return (
        db.query(Organization)
        .filter(
            Organization.name == name,
            Organization.is_deleted == False,
        )
        .first()
    )


from datetime import datetime
from app.common.query import validate_and_apply_sorting

ALLOWED_ORG_SORT_FIELDS = {
    "name": Organization.name,
    "email": Organization.email,
    "created_at": Organization.created_at,
    "updated_at": Organization.updated_at,
}


def get_organizations(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    organization_ids: list | None = None,
):
    """
    Fetch organizations with pagination, search, active filtering, and sorting.
    """
    if organization_ids is not None and len(organization_ids) == 0:
        return []

    query = (
        db.query(Organization)
        .filter(
            Organization.is_deleted == False,
        )
    )

    if organization_ids is not None:
        query = query.filter(Organization.id.in_(organization_ids))

    if is_active is not None:
        query = query.filter(
            Organization.is_active == is_active,
        )

    if search:
        query = query.filter(
            or_(
                Organization.name.ilike(f"%{search}%"),
                Organization.email.ilike(f"%{search}%"),
            )
        )

    if created_after:
        query = query.filter(Organization.created_at >= created_after)

    if created_before:
        query = query.filter(Organization.created_at <= created_before)

    query = validate_and_apply_sorting(
        query=query,
        model=Organization,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_ORG_SORT_FIELDS,
        default_sort_column=Organization.created_at,
    )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_organizations(
    db: Session,
    search: str | None = None,
    is_active: bool | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    organization_ids: list | None = None,
):
    """
    Count organizations for pagination.
    """
    if organization_ids is not None and len(organization_ids) == 0:
        return 0

    query = (
        db.query(Organization)
        .filter(
            Organization.is_deleted == False,
        )
    )

    if organization_ids is not None:
        query = query.filter(Organization.id.in_(organization_ids))

    if is_active is not None:
        query = query.filter(
            Organization.is_active == is_active,
        )

    if search:
        query = query.filter(
            or_(
                Organization.name.ilike(f"%{search}%"),
                Organization.email.ilike(f"%{search}%"),
            )
        )

    if created_after:
        query = query.filter(Organization.created_at >= created_after)

    if created_before:
        query = query.filter(Organization.created_at <= created_before)

    return query.count()




def update_organization(
    db: Session,
    organization: Organization,
):
    """
    Update organization record.
    """

    db.commit()
    db.refresh(organization)

    return organization


def delete_organization(
    db: Session,
    organization: Organization,
):
    """
    Soft delete organization.
    """

    organization.is_deleted = True
    organization.is_active = False

    db.commit()
    db.refresh(organization)

    return organization

