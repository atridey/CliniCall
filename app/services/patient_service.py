from sqlalchemy.orm import Session
from ..models import Patient, TestResult, Appointment, Doctor
from ..database import SessionLocal
from datetime import datetime

class PatientService:
    def __init__(self, db: Session):
        self.db = db

    def get_patient_by_phone(self, phone_number: str):
        return self.db.query(Patient).filter(Patient.phone_number == phone_number).first()

    def fuzzy_search_patient(self, name_query: str, dob_query: str = None):
        # 1. Search by name (loose match)
        # Split query into parts to handle "John" or "John Doe"
        parts = name_query.lower().split()
        
        query = self.db.query(Patient)
        
        # very basic fuzzy match: checking if name parts are in first or last name
        # For a robust system, use a search engine or fuzzystrmatch
        # Here we just look for patients where EITHER first or last name matches the query
        
        # Let's iterate all patients and match in python for flexibility with small db
        all_patients = query.all()
        
        best_match = None
        
        for p in all_patients:
            full_name = f"{p.first_name} {p.last_name}".lower()
            name_match = name_query.lower() in full_name
            
            dob_match = True
            if dob_query:
                # check if dob query is inside patient dob string
                if dob_query not in p.dob:
                    dob_match = False
            
            if name_match and dob_match:
                best_match = p
                break # Return first match for now
                
        return best_match

    def get_patient_results(self, patient_id: int):
        return self.db.query(TestResult).filter(TestResult.patient_id == patient_id).all()

    def get_patient_appointments(self, patient_id: int):
        return self.db.query(Appointment).filter(Appointment.patient_id == patient_id).all()

    def book_appointment(self, patient_id: int, date_str: str, reason: str, doctor_name: str = None):
        try:
            # Flexible parsing: Try ISO first, then maybe simple date? 
            # LLM usually sends ISO if instructed.
            appt_date = datetime.fromisoformat(date_str)
        except ValueError:
            return None

        doctor_id = 1 # Default fallback
        if doctor_name:
            # Case-insensitive search
            doc = self.db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
            if doc:
                doctor_id = doc.id
            else:
                # Create new doctor if not found (for prototype flexibility)
                new_doc = Doctor(name=doctor_name, specialty="General Practice")
                self.db.add(new_doc)
                self.db.commit()
                doctor_id = new_doc.id

        new_appt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=appt_date,
            reason=reason,
            status="Scheduled"
        )
        self.db.add(new_appt)
        self.db.commit()
        return new_appt

    def cancel_appointment(self, appointment_id: int):
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appt:
            appt.status = "Cancelled"
            self.db.commit()
            return True
        return False

    def reschedule_appointment(self, appointment_id: int, new_date_str: str):
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return None
        
        try:
            new_date = datetime.fromisoformat(new_date_str)
            appt.date = new_date
            appt.status = "Rescheduled"
            self.db.commit()
            return appt
        except ValueError:
            return None

def get_patient_service():
    db = SessionLocal()
    try:
        yield PatientService(db)
    finally:
        db.close()
