from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CallLog
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

class LogEntry(BaseModel):
    id: int
    phone_number: str
    patient_name: str | None
    query: str
    response: str
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("/logs", response_model=List[LogEntry])
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(CallLog).order_by(CallLog.timestamp.desc()).limit(50).all()
    return [
        LogEntry(
            id=log.id,
            phone_number=log.phone_number,
            patient_name=f"{log.patient.first_name} {log.patient.last_name}" if log.patient else None,
            query=log.query,
            response=log.response,
            timestamp=log.timestamp
        ) for log in logs
    ]

from ..models import Patient, Appointment

class VitalSignView(BaseModel):
    type: str
    value: str
    unit: str
    timestamp: datetime
    class Config: from_attributes = True

class InsuranceView(BaseModel):
    provider: str | None
    plan_type: str | None
    policy_number: str | None
    class Config: from_attributes = True

class ImmunizationView(BaseModel):
    vaccine_name: str
    date_administered: str
    status: str
    class Config: from_attributes = True

class ProblemView(BaseModel):
    name: str
    status: str
    date_diagnosed: str
    class Config: from_attributes = True

class MedicationView(BaseModel):
    name: str
    dosage: str
    frequency: str
    prescribed_by: str | None
    class Config: from_attributes = True

class SocialHistoryView(BaseModel):
    smoking_status: str | None
    alcohol_use: str | None
    occupation: str | None
    class Config: from_attributes = True

class FamilyHistoryView(BaseModel):
    relation: str
    condition: str
    class Config: from_attributes = True

class CareTeamView(BaseModel):
    role: str
    name: str
    phone: str | None
    class Config: from_attributes = True

class TestResultView(BaseModel):
    test_name: str
    value: float
    unit: str
    interpretation: str
    performed_at: datetime

    class Config:
        from_attributes = True

class AppointmentView(BaseModel):
    date: datetime
    reason: str
    status: str
    doctor_name: str

    class Config:
        from_attributes = True

class PatientView(BaseModel):
    first_name: str
    last_name: str
    dob: str
    gender: str | None
    phone_number: str
    address: str | None
    marital_status: str | None
    emergency_contact_name: str | None
    emergency_contact_relation: str | None
    emergency_contact_phone: str | None
    
    allergies_summary: str | None
    medical_history_summary: str | None
    
    results: List[TestResultView] = []
    appointments: List[AppointmentView] = []
    
    # New sections
    vitals: List[VitalSignView] = []
    insurance: InsuranceView | None = None
    immunizations: List[ImmunizationView] = []
    problems: List[ProblemView] = []
    medications: List[MedicationView] = []
    social_history: SocialHistoryView | None = None
    family_history: List[FamilyHistoryView] = []
    care_team: List[CareTeamView] = []

    class Config:
        from_attributes = True

class PatientList(BaseModel):
    id: int
    first_name: str
    last_name: str
    dob: str | None
    phone_number: str

    class Config:
        from_attributes = True

@router.get("/patients", response_model=List[PatientList])
def get_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.get("/patient/{phone_number}", response_model=PatientView)
def get_patient_details(phone_number: str, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    patient = db.query(Patient).options(
        joinedload(Patient.results),
        joinedload(Patient.appointments).joinedload(Appointment.doctor),
        joinedload(Patient.insurance),
        joinedload(Patient.vitals),
        joinedload(Patient.immunizations),
        joinedload(Patient.problems),
        joinedload(Patient.medications),
        joinedload(Patient.social_history),
        joinedload(Patient.family_history),
        joinedload(Patient.care_team)
    ).filter(Patient.phone_number == phone_number).first()
    
    if not patient:
        return None
        
    return PatientView(
        first_name=patient.first_name,
        last_name=patient.last_name,
        dob=patient.dob,
        gender=patient.gender,
        phone_number=patient.phone_number,
        address=patient.address,
        marital_status=patient.marital_status,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_relation=patient.emergency_contact_relation,
        emergency_contact_phone=patient.emergency_contact_phone,
        
        allergies_summary=patient.allergies_summary,
        medical_history_summary=patient.medical_history_summary,
        
        # Pydantic ORM mode handles simple lists of matching models
        results=patient.results,
        vitals=patient.vitals,
        insurance=patient.insurance,
        immunizations=patient.immunizations,
        problems=patient.problems,
        medications=patient.medications,
        social_history=patient.social_history,
        family_history=patient.family_history,
        care_team=patient.care_team,
        
        # Manually handle appointments due to doctor_name field mismatch
        appointments=[
            AppointmentView(
                date=a.date,
                reason=a.reason,
                status=a.status,
                doctor_name=a.doctor.name if a.doctor else "Unknown"
            ) for a in patient.appointments
        ]
    )
