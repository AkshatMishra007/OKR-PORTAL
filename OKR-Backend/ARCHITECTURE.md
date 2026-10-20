# OKR-Backend Architecture & Development Guide

This document defines the standardized directory structure, coding conventions, audit & timestamp tracking, and module index for the **OKR Backend**.

---

## 1. Five-Layer Architecture Standard

Every domain module in `app/` follows a uniform 5-layer design pattern:

```
app/<module_name>/
├── models.py       # SQLAlchemy ORM database models
├── schemas.py      # Pydantic schemas (Request & Response DTOs)
├── repository.py   # Database access layer (CRUD queries & transactions)
├── service.py      # Business logic, tenant security & access checks
└── router.py       # FastAPI HTTP route handlers
```

### Layer Responsibilities

| Layer | Responsibility | What it Must NOT Do |
|---|---|---|
| **`models.py`** | Defines database schema and SQLAlchemy ORM relationships. Inherits from `Base` and `BaseModel`. | No business logic, no HTTP exceptions. |
| **`schemas.py`** | Defines request payloads (`Create`, `Update`) and response envelopes (`Response`). Inherits from `AuditSchemaMixin`. | No direct DB queries. |
| **`repository.py`** | Executes pure SQL/ORM operations (`db.query`, `db.add`, `db.commit`, filters). Accepts `created_by` and `updated_by`. | No HTTP status codes or FastAPI dependencies. |
| **`service.py`** | Implements core business logic, orchestrates repository calls, and raises typed exceptions from `app.common.exceptions`. | No raw HTTP request/response handling. |
| **`router.py`** | Declares endpoints, extracts request parameters, calls services via dependency injection (`Depends(get_db)`, `Depends(get_current_user)`). | No direct DB queries; no complex business workflows. |

---

## 2. Audit & Timestamp Tracking

All database models inherit from `app.common.models.BaseModel`, which automatically provides:

- `id`: UUID v4 primary key.
- `created_at`: Timestamp (UTC) set on creation.
- `updated_at`: Timestamp (UTC) updated on every modification.
- `created_by`: UUID of the authenticated actor who created the record.
- `updated_by`: UUID of the authenticated actor who last modified or deleted the record.
- `is_active`: Boolean flag indicating if record is active (defaults to `True`).
- `is_deleted`: Boolean flag indicating soft deletion (defaults to `False`).
- `deleted_at`: Timestamp (UTC) set when the record is soft-deleted.

### Soft Deletion Standard
When soft-deleting any entity:
```python
entity.is_deleted = True
entity.is_active = False
entity.deleted_at = datetime.now(UTC)
entity.updated_by = current_user_id
```

---

## 3. Module Reference Index

| Module | Core Purpose | Key Models | Key Functions |
|---|---|---|---|
| **`auth/`** | Authentication & Token Management | `Token`, `User` | `create_access_token`, `login_service`, `get_current_user` |
| **`users/`** | User lifecycle & profiles | `User` | `create_user_service`, `get_user_by_id`, `update_user`, `delete_user` |
| **`organizations/`** | Organization tenant management | `Organization` | `create_organization_service`, `list_organizations_service`, `update_organization_service` |
| **`organization_members/`** | Membership & role assignments | `OrganizationMember` | `assign_member_to_organization`, `remove_member_service` |
| **`batches/`** | Quarter & cohort batch management | `Batch` | `create_batch`, `get_batch`, `update_batch`, `list_batches` |
| **`my_okr/`** | Individual & team OKR objectives | `OKR` | `create_okr`, `get_okr`, `update_okr`, `delete_okr` |
| **`queries/`** | Queries, escalations & questions | `Query` | `create_query_service`, `update_query_status`, `list_queries` |
| **`query_activity/`** | Audit logs for query changes | `QueryActivity` | `create_activity`, `list_query_activities` |
| **`fogs_hurdles/`** | Blockers, risks & hurdle tracking | `FogsHurdle` | `create_fogs_hurdle`, `resolve_fogs_hurdle` |
| **`tracker_entries/`** | Key Result tracking entries | `TrackerEntry` | `create_tracker_entry`, `list_tracker_entries` |
| **`weekly_update/`** | Weekly OKR check-ins | `WeeklyUpdate` | `create_weekly_update`, `get_weekly_update` |
| **`okr_logs/`** | Historical OKR change audit logs | `OkrLog` | `create_log`, `get_logs_by_user`, `list_logs` |
| **`rbac/`** | Roles, policies & access scopes | `Role` | `create_role`, `authorize_okr_action`, `is_super_admin` |
| **`common/`** | Shared utilities, models & schemas | `BaseModel`, `ResponseSchema` | `paginate_query`, `validate_and_apply_sorting` |
| **`core/`** | Database, config & security | Engine, SessionLocal, Settings | `get_db`, `settings` |

---

## 4. Function Documentation Standard

Every function created in the repository should adhere to this docstring template:

```python
def function_name(
    param_a: str,
    param_b: int = 10,
) -> ReturnType:
    """
    Brief one-line summary of what the function accomplishes.

    Args:
        param_a: Purpose and description of param_a.
        param_b: Purpose and description of param_b.

    Returns:
        ReturnType: Description of the return value.

    Raises:
        AppException: Reason this exception is raised.
    """
```
