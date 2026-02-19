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
        import re
        
        # 1. Normalize queries
        name_parts = name_query.lower().split()
        dob_year = None
        if dob_query:
            # Extract 4-digit year from dob_query
            year_match = re.search(r'\d{4}', dob_query)
            if year_match:
                dob_year = year_match.group(0)

        # 2. Search logic
        # We iterate all patients because the DB is small (prototype).
        # ideally this would be a SQL LIKE query or FTS.
        all_patients = self.db.query(Patient).all()
        
        best_match = None
        max_score = 0
        
        for p in all_patients:
            p_first = p.first_name.lower()
            p_last = p.last_name.lower()
            p_dob = p.dob or ""
            
            # --- Name Score ---
            # Check how many query parts appear in the patient's name
            matches = 0
            for part in name_parts:
                if part in p_first or part in p_last:
                    matches += 1
            
            if matches == 0:
                continue # No name match at all
            
            # --- DOB Check ---
            dob_match = True
            if dob_query:
                # If we found a year in the query, check if patient DOB CLI has that year
                if dob_year:
                    if dob_year not in p_dob:
                        dob_match = False
                else:
                    # No year found in query, fallback to substring match
                    # e.g. query "March 1" vs dob "2024-03-01" -> hard to match without parsing
                    # Let's be lenient: if name matches well (>=2 parts), we might allow it?
                    # For now, simplistic: if query provided but no year, string match
                    if dob_query.lower() not in p_dob.lower():
                        # Try one more fallback: maybe the query is "01/01/1980" and DOB is "1980-01-01"
                        # Too complex for now. Strict year match is safest for this prototype.
                        pass 

            if dob_match:
                # Prioritize matches with more name parts and year agreement
                score = matches + (1 if dob_match and dob_year else 0)
                if score > max_score:
                    max_score = score
                    best_match = p

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

    def update_pharmacy(self, patient_id: int, pharmacy_name: str):
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            patient.preferred_pharmacy = pharmacy_name
            self.db.commit()
            return True
        return False

def get_patient_service():
    db = SessionLocal()
    try:
        yield PatientService(db)
    finally:
        db.close()
