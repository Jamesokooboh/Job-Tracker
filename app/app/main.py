"""
Job Application Tracker API
A minimal FastAPI service backed by PostgreSQL, containerized and deployed
to AWS ECS Fargate via Terraform + GitHub Actions.
"""

from datetime import date
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, Enum as SAEnum
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from .config import get_database_url

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobApplicationModel(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    status = Column(SAEnum(ApplicationStatus), default=ApplicationStatus.APPLIED, nullable=False)
    date_applied = Column(Date, nullable=False)
    notes = Column(String, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class JobApplicationCreate(BaseModel):
    company: str
    role: str
    status: ApplicationStatus = ApplicationStatus.APPLIED
    date_applied: date
    notes: Optional[str] = None


class JobApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    date_applied: Optional[date] = None
    notes: Optional[str] = None


class JobApplicationOut(JobApplicationCreate):
    id: int

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Job Application Tracker API",
    description="Track job applications: company, role, status, and notes.",
    version="1.0.0",
)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["infra"])
def health_check():
    """Used by the ALB target group health check."""
    return {"status": "ok"}


@app.post("/applications", response_model=JobApplicationOut, status_code=201, tags=["applications"])
def create_application(payload: JobApplicationCreate, db: Session = Depends(get_db)):
    record = JobApplicationModel(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/applications", response_model=list[JobApplicationOut], tags=["applications"])
def list_applications(status: Optional[ApplicationStatus] = None, db: Session = Depends(get_db)):
    query = db.query(JobApplicationModel)
    if status:
        query = query.filter(JobApplicationModel.status == status)
    return query.order_by(JobApplicationModel.date_applied.desc()).all()


@app.get("/applications/{application_id}", response_model=JobApplicationOut, tags=["applications"])
def get_application(application_id: int, db: Session = Depends(get_db)):
    record = db.get(JobApplicationModel, application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    return record


@app.patch("/applications/{application_id}", response_model=JobApplicationOut, tags=["applications"])
def update_application(application_id: int, payload: JobApplicationUpdate, db: Session = Depends(get_db)):
    record = db.get(JobApplicationModel, application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@app.delete("/applications/{application_id}", status_code=204, tags=["applications"])
def delete_application(application_id: int, db: Session = Depends(get_db)):
    record = db.get(JobApplicationModel, application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(record)
    db.commit()
    return None
