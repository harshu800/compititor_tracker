"""Workspace creation/listing. Note: organization_id for every OTHER route
is derived server-side from membership (see security/auth.py) — this file
is the only place a client picks/creates an org, and even here we create
the OrganizationMember row ourselves rather than trusting a client-supplied
role or org id for any existing org."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, OrganizationMember, User, NotificationSettings
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
    name: str


@router.get("")
def list_my_organizations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()
    orgs = []
    for m in memberships:
        org = db.query(Organization).filter(Organization.id == m.organization_id).first()
        if org:
            orgs.append({"id": str(org.id), "name": org.name, "role": m.role, "plan": org.plan})
    return orgs


@router.post("", status_code=201)
def create_organization(payload: OrganizationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = Organization(name=payload.name, owner_id=user.id, plan="free")
    db.add(org)
    db.commit()
    db.refresh(org)

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
    db.add(member)
    db.add(NotificationSettings(organization_id=org.id))
    db.commit()

    return {"id": str(org.id), "name": org.name, "role": "owner", "plan": org.plan}
