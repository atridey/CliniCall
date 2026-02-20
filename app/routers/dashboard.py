from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CallLog, Patient, Appointment, Message, VitalSign, Insurance, Immunization, Problem, Medication, SocialHistory
from typing import List, Optional
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

class VitalSignView(BaseModel):
    id: int
    type: str
    value: str
    unit: str
    timestamp: datetime
    class Config: from_attributes = True

class InsuranceView(BaseModel):
    id: int | None = None
    provider: str | None
    plan_type: str | None
    policy_number: str | None
    class Config: from_attributes = True

class ImmunizationView(BaseModel):
    id: int
    vaccine_name: str
    date_administered: str
    status: str
    class Config: from_attributes = True

class ProblemView(BaseModel):
    id: int
    name: str
    status: str
    date_diagnosed: str
    class Config: from_attributes = True

class MedicationView(BaseModel):
    id: int
    name: str
    dosage: str
    frequency: str
    prescribed_by: str | None
    class Config: from_attributes = True

class SocialHistoryView(BaseModel):
    id: int | None = None
    smoking_status: str | None
    alcohol_use: str | None
    occupation: str | None
    class Config: from_attributes = True

class FamilyHistoryView(BaseModel):
    id: int
    relation: str
    condition: str
    class Config: from_attributes = True

class CareTeamView(BaseModel):
    id: int
    role: str
    name: str
    phone: str | None
    class Config: from_attributes = True

class TestResultView(BaseModel):
    id: int
    test_name: str
    value: float
    unit: str
    interpretation: str
    performed_at: datetime

    class Config:
        from_attributes = True

class AppointmentView(BaseModel):
    id: int
    date: datetime
    reason: str
    status: str
    doctor_name: str

    class Config:
        from_attributes = True

class PatientView(BaseModel):
    id: int
    first_name: str
    last_name: str
    dob: str
    gender: str | None
    phone_number: str
    address: str | None
    marital_status: str | None
    preferred_pharmacy: str | None
    emergency_contact_name: str | None
    emergency_contact_relation: str | None
    emergency_contact_phone: str | None
    
    allergies_summary: str | None
    medical_history_summary: str | None
    
    results: List[TestResultView] = []
    appointments: List[AppointmentView] = []
    
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
        raise HTTPException(status_code=404, detail="Patient not found")
        
    return PatientView(
        id=patient.id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        dob=patient.dob,
        gender=patient.gender,
        phone_number=patient.phone_number,
        address=patient.address,
        marital_status=patient.marital_status,
        preferred_pharmacy=patient.preferred_pharmacy,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_relation=patient.emergency_contact_relation,
        emergency_contact_phone=patient.emergency_contact_phone,
        
        allergies_summary=patient.allergies_summary,
        medical_history_summary=patient.medical_history_summary,
        
        results=patient.results,
        vitals=patient.vitals,
        insurance=patient.insurance,
        immunizations=patient.immunizations,
        problems=patient.problems,
        medications=patient.medications,
        social_history=patient.social_history,
        family_history=patient.family_history,
        care_team=patient.care_team,
        
        appointments=[
            AppointmentView(
                id=a.id,
                date=a.date,
                reason=a.reason,
                status=a.status,
                doctor_name=a.doctor.name if a.doctor else "Unknown"
            ) for a in patient.appointments
        ]
    )

# ── Messages ────────────────────────────────────────────────────────────────

class MessageView(BaseModel):
    id: int
    sender_role: str
    sender_name: str
    subject: str | None
    body: str
    is_read: bool
    timestamp: datetime

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    sender_name: str  # Doctor's name, supplied by the front-end
    subject: str | None = None
    body: str

@router.get("/messages/{phone_number}", response_model=list[MessageView])
def get_messages(phone_number: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.phone_number == phone_number).first()
    if not patient:
        return []
    return (
        db.query(Message)
        .filter(Message.patient_id == patient.id)
        .order_by(Message.timestamp.desc())
        .all()
    )

@router.post("/messages/{phone_number}", response_model=MessageView)
def send_doctor_message(phone_number: str, payload: MessageCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.phone_number == phone_number).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    msg = Message(
        patient_id=patient.id,
        sender_role="doctor",
        sender_name=payload.sender_name,
        subject=payload.subject,
        body=payload.body,
        is_read=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

@router.delete("/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(msg)
    db.commit()
    return {"status": "success"}

# ── PATCH Endpoints for Patient Data ────────────────────────────────────────

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    marital_status: Optional[str] = None
    preferred_pharmacy: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies_summary: Optional[str] = None
    medical_history_summary: Optional[str] = None

@router.patch("/patient/{patient_id}", response_model=PatientView)
def update_patient(patient_id: int, patient_update: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    for field, value in patient_update.dict(exclude_unset=True).items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    return get_patient_details(patient.phone_number, db) # Re-use existing detail getter for full view

class InsuranceUpdate(BaseModel):
    provider: Optional[str] = None
    plan_type: Optional[str] = None
    policy_number: Optional[str] = None

@router.patch("/patient/{patient_id}/insurance", response_model=InsuranceView)
def update_insurance(patient_id: int, insurance_update: InsuranceUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if not patient.insurance:
        # Create new insurance record if it doesn't exist
        insurance = Insurance(patient_id=patient_id)
        db.add(insurance)
        db.flush() # Ensure insurance gets an ID before updating
        patient.insurance = insurance
    
    for field, value in insurance_update.dict(exclude_unset=True).items():
        setattr(patient.insurance, field, value)
    
    db.commit()
    db.refresh(patient.insurance)
    return patient.insurance

class SocialHistoryUpdate(BaseModel):
    smoking_status: Optional[str] = None
    alcohol_use: Optional[str] = None
    occupation: Optional[str] = None

@router.patch("/patient/{patient_id}/social_history", response_model=SocialHistoryView)
def update_social_history(patient_id: int, social_history_update: SocialHistoryUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if not patient.social_history:
        # Create new social history record if it doesn't exist
        social_history = SocialHistory(patient_id=patient_id)
        db.add(social_history)
        db.flush()
        patient.social_history = social_history
    
    for field, value in social_history_update.dict(exclude_unset=True).items():
        setattr(patient.social_history, field, value)
    
    db.commit()
    db.refresh(patient.social_history)
    return patient.social_history

class VitalSignCreateUpdate(BaseModel):
    type: str
    value: str
    unit: str
    timestamp: datetime = datetime.now()

@router.post("/patient/{patient_id}/vitals", response_model=VitalSignView)
def add_vital_sign(patient_id: int, vital_sign_data: VitalSignCreateUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    new_vital = VitalSign(patient_id=patient_id, **vital_sign_data.dict())
    db.add(new_vital)
    db.commit()
    db.refresh(new_vital)
    return new_vital

@router.patch("/patient/{patient_id}/vitals/{vital_id}", response_model=VitalSignView)
def update_vital_sign(patient_id: int, vital_id: int, vital_sign_update: VitalSignCreateUpdate, db: Session = Depends(get_db)):
    vital = db.query(VitalSign).filter(VitalSign.id == vital_id, VitalSign.patient_id == patient_id).first()
    if not vital:
        raise HTTPException(status_code=404, detail="Vital sign not found for this patient")
    
    for field, value in vital_sign_update.dict(exclude_unset=True).items():
        setattr(vital, field, value)
    
    db.commit()
    db.refresh(vital)
    return vital

class ProblemCreateUpdate(BaseModel):
    name: str
    status: str
    date_diagnosed: str

@router.post("/patient/{patient_id}/problems", response_model=ProblemView)
def add_problem(patient_id: int, problem_data: ProblemCreateUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    new_problem = Problem(patient_id=patient_id, **problem_data.dict())
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)
    return new_problem

@router.patch("/patient/{patient_id}/problems/{problem_id}", response_model=ProblemView)
def update_problem(patient_id: int, problem_id: int, problem_update: ProblemCreateUpdate, db: Session = Depends(get_db)):
    problem = db.query(Problem).filter(Problem.id == problem_id, Problem.patient_id == patient_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found for this patient")
    
    for field, value in problem_update.dict(exclude_unset=True).items():
        setattr(problem, field, value)
    
    db.commit()
    db.refresh(problem)
    return problem

class MedicationCreateUpdate(BaseModel):
    name: str
    dosage: str
    frequency: str
    prescribed_by: Optional[str] = None

@router.post("/patient/{patient_id}/medications", response_model=MedicationView)
def add_medication(patient_id: int, medication_data: MedicationCreateUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    new_medication = Medication(patient_id=patient_id, **medication_data.dict())
    db.add(new_medication)
    db.commit()
    db.refresh(new_medication)
    return new_medication

@router.patch("/patient/{patient_id}/medications/{medication_id}", response_model=MedicationView)
def update_medication(patient_id: int, medication_id: int, medication_update: MedicationCreateUpdate, db: Session = Depends(get_db)):
    medication = db.query(Medication).filter(Medication.id == medication_id, Medication.patient_id == patient_id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found for this patient")
    
    for field, value in medication_update.dict(exclude_unset=True).items():
        setattr(medication, field, value)
    
    db.commit()
    db.refresh(medication)
    return medication

class ImmunizationCreateUpdate(BaseModel):
    vaccine_name: str
    date_administered: str
    status: str

@router.post("/patient/{patient_id}/immunizations", response_model=ImmunizationView)
def add_immunization(patient_id: int, immunization_data: ImmunizationCreateUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    new_immunization = Immunization(patient_id=patient_id, **immunization_data.dict())
    db.add(new_immunization)
    db.commit()
    db.refresh(new_immunization)
    return new_immunization

@router.patch("/patient/{patient_id}/immunizations/{immunization_id}", response_model=ImmunizationView)
def update_immunization(patient_id: int, immunization_id: int, immunization_update: ImmunizationCreateUpdate, db: Session = Depends(get_db)):
    immunization = db.query(Immunization).filter(Immunization.id == immunization_id, Immunization.patient_id == patient_id).first()
    if not immunization:
        raise HTTPException(status_code=404, detail="Immunization not found for this patient")
    
    for field, value in immunization_update.dict(exclude_unset=True).items():
        setattr(immunization, field, value)
    
    db.commit()
    db.refresh(immunization)
    return immunization
