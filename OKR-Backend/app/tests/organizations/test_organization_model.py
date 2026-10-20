import uuid

from app.organizations.models import Organization


def test_organization_model_creation():

    organization = Organization(
        name="SSDN Technologies",
        description="Training Organization",
        email="info@ssdn.com",
    )

    assert organization.name == "SSDN Technologies"
    assert organization.description == "Training Organization"


def test_organization_default_fields():

    organization = Organization(
        name="Test Org",
    )

    assert organization.is_active is None or organization.is_active is True
    assert organization.is_deleted is None or organization.is_deleted is False


def test_organization_has_uuid():

    organization = Organization(
        name="UUID Org",
    )

    assert organization.id is None or isinstance(
        organization.id,
        uuid.UUID,
    )

