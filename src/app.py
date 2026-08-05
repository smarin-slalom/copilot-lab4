"""
Slalom Capabilities Management System API

A FastAPI application that enables Slalom consultants to register their
capabilities and manage consulting expertise across the organization.
"""

import json
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, ForeignKey, String, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get("DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'capabilities.db'}")
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Capability(Base):
    __tablename__ = "capabilities"

    name = Column(String, primary_key=True, index=True)
    description = Column(String, nullable=False)
    practice_area = Column(String, nullable=False)
    skill_levels = Column(String, nullable=False)        # JSON-encoded list
    certifications = Column(String, nullable=False)      # JSON-encoded list
    industry_verticals = Column(String, nullable=False)  # JSON-encoded list
    capacity = Column(Integer, nullable=False, default=0)

    consultants = relationship("Consultant", back_populates="capability", cascade="all, delete-orphan")


class Consultant(Base):
    __tablename__ = "consultants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, index=True)
    capability_name = Column(String, ForeignKey("capabilities.name"), nullable=False)

    capability = relationship("Capability", back_populates="consultants")


Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Seed data — only inserted once if the table is empty
# ---------------------------------------------------------------------------

SEED_CAPABILITIES = [
    {
        "name": "Cloud Architecture",
        "description": "Design and implement scalable cloud solutions using AWS, Azure, and GCP",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["AWS Solutions Architect", "Azure Architect Expert"],
        "industry_verticals": ["Healthcare", "Financial Services", "Retail"],
        "capacity": 40,
        "consultants": ["alice.smith@slalom.com", "bob.johnson@slalom.com"],
    },
    {
        "name": "Data Analytics",
        "description": "Advanced data analysis, visualization, and machine learning solutions",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Tableau Desktop Specialist", "Power BI Expert", "Google Analytics"],
        "industry_verticals": ["Retail", "Healthcare", "Manufacturing"],
        "capacity": 35,
        "consultants": ["emma.davis@slalom.com", "sophia.wilson@slalom.com"],
    },
    {
        "name": "DevOps Engineering",
        "description": "CI/CD pipeline design, infrastructure automation, and containerization",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Docker Certified Associate", "Kubernetes Admin", "Jenkins Certified"],
        "industry_verticals": ["Technology", "Financial Services"],
        "capacity": 30,
        "consultants": ["john.brown@slalom.com", "olivia.taylor@slalom.com"],
    },
    {
        "name": "Digital Strategy",
        "description": "Digital transformation planning and strategic technology roadmaps",
        "practice_area": "Strategy",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Digital Transformation Certificate", "Agile Certified Practitioner"],
        "industry_verticals": ["Healthcare", "Financial Services", "Government"],
        "capacity": 25,
        "consultants": ["liam.anderson@slalom.com", "noah.martinez@slalom.com"],
    },
    {
        "name": "Change Management",
        "description": "Organizational change leadership and adoption strategies",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Prosci Certified", "Lean Six Sigma Black Belt"],
        "industry_verticals": ["Healthcare", "Manufacturing", "Government"],
        "capacity": 20,
        "consultants": ["ava.garcia@slalom.com", "mia.rodriguez@slalom.com"],
    },
    {
        "name": "UX/UI Design",
        "description": "User experience design and digital product innovation",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Adobe Certified Expert", "Google UX Design Certificate"],
        "industry_verticals": ["Retail", "Healthcare", "Technology"],
        "capacity": 30,
        "consultants": ["amelia.lee@slalom.com", "harper.white@slalom.com"],
    },
    {
        "name": "Cybersecurity",
        "description": "Information security strategy, risk assessment, and compliance",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["CISSP", "CISM", "CompTIA Security+"],
        "industry_verticals": ["Financial Services", "Healthcare", "Government"],
        "capacity": 25,
        "consultants": ["ella.clark@slalom.com", "scarlett.lewis@slalom.com"],
    },
    {
        "name": "Business Intelligence",
        "description": "Enterprise reporting, data warehousing, and business analytics",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Microsoft BI Certification", "Qlik Sense Certified"],
        "industry_verticals": ["Retail", "Manufacturing", "Financial Services"],
        "capacity": 35,
        "consultants": ["james.walker@slalom.com", "benjamin.hall@slalom.com"],
    },
    {
        "name": "Agile Coaching",
        "description": "Agile transformation and team coaching for scaled delivery",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Certified Scrum Master", "SAFe Agilist", "ICAgile Certified"],
        "industry_verticals": ["Technology", "Financial Services", "Healthcare"],
        "capacity": 20,
        "consultants": ["charlotte.young@slalom.com", "henry.king@slalom.com"],
    },
]


def _seed(db: Session) -> None:
    if db.query(Capability).count() > 0:
        return
    for item in SEED_CAPABILITIES:
        cap = Capability(
            name=item["name"],
            description=item["description"],
            practice_area=item["practice_area"],
            skill_levels=json.dumps(item["skill_levels"]),
            certifications=json.dumps(item["certifications"]),
            industry_verticals=json.dumps(item["industry_verticals"]),
            capacity=item["capacity"],
        )
        db.add(cap)
        for email in item["consultants"]:
            db.add(Consultant(email=email, capability_name=item["name"]))
    db.commit()


with SessionLocal() as _db:
    _seed(_db)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Slalom Capabilities Management API",
    description="API for managing consulting capabilities and consultant expertise",
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _capability_to_dict(cap: Capability) -> dict:
    return {
        "description": cap.description,
        "practice_area": cap.practice_area,
        "skill_levels": json.loads(cap.skill_levels),
        "certifications": json.loads(cap.certifications),
        "industry_verticals": json.loads(cap.industry_verticals),
        "capacity": cap.capacity,
        "consultants": [c.email for c in cap.consultants],
    }


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/capabilities")
def get_capabilities(db: Session = Depends(get_db)):
    caps = db.query(Capability).all()
    return {cap.name: _capability_to_dict(cap) for cap in caps}


@app.post("/capabilities/{capability_name}/register")
def register_for_capability(capability_name: str, email: str, db: Session = Depends(get_db)):
    """Register a consultant for a capability"""
    cap = db.query(Capability).filter(Capability.name == capability_name).first()
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found")

    already = db.query(Consultant).filter(
        Consultant.capability_name == capability_name,
        Consultant.email == email,
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="Consultant is already registered for this capability")

    db.add(Consultant(email=email, capability_name=capability_name))
    db.commit()
    return {"message": f"Registered {email} for {capability_name}"}


@app.delete("/capabilities/{capability_name}/unregister")
def unregister_from_capability(capability_name: str, email: str, db: Session = Depends(get_db)):
    """Unregister a consultant from a capability"""
    cap = db.query(Capability).filter(Capability.name == capability_name).first()
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found")

    consultant = db.query(Consultant).filter(
        Consultant.capability_name == capability_name,
        Consultant.email == email,
    ).first()
    if not consultant:
        raise HTTPException(status_code=400, detail="Consultant is not registered for this capability")

    db.delete(consultant)
    db.commit()
    return {"message": f"Unregistered {email} from {capability_name}"}
