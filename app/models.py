from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Text
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    
    # Demographics
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    dob = Column(String) # YYYY-MM-DD
    gender = Column(String)
    phone_number = Column(String, unique=True, index=True)
    address = Column(String)
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    emergency_contact_relation = Column(String)
    marital_status = Column(String)
    preferred_pharmacy = Column(String)
    
    password_hash = Column(String) # Simulated

    # Computed/Summary fields for quick access (optional but helpful)
    allergies_summary = Column(Text) # Comma-separated or text block
    medical_history_summary = Column(Text) 

    # Relationships
    insurance = relationship("Insurance", back_populates="patient", uselist=False)
    vitals = relationship("VitalSign", back_populates="patient")
    immunizations = relationship("Immunization", back_populates="patient")
    problems = relationship("Problem", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    social_history = relationship("SocialHistory", back_populates="patient", uselist=False)
    family_history = relationship("FamilyHistory", back_populates="patient")
    care_team = relationship("CareTeam", back_populates="patient")
    
    results = relationship("TestResult", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    logs = relationship("CallLog", back_populates="patient")

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    specialty = Column(String)
    phone = Column(String)
    email = Column(String)

    appointments = relationship("Appointment", back_populates="doctor")
    care_team_entries = relationship("CareTeam", back_populates="doctor")

class Insurance(Base):
    __tablename__ = "insurance"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    provider = Column(String)
    policy_number = Column(String)
    group_number = Column(String)
    plan_type = Column(String) # HMO, PPO etc.
    subscriber_id = Column(String)
    
    patient = relationship("Patient", back_populates="insurance")

class VitalSign(Base):
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String) # BP, HR, Temp, Weight, Height, O2, BMI
    value = Column(String) # Stored as string to handle "120/80"
    unit = Column(String)
    
    patient = relationship("Patient", back_populates="vitals")

class Immunization(Base):
    __tablename__ = "immunizations"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    vaccine_name = Column(String)
    date_administered = Column(String) # YYYY-MM-DD
    lot_number = Column(String)
    status = Column(String, default="Completed")

    patient = relationship("Patient", back_populates="immunizations")

class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String) # Diagnosis
    icd_10 = Column(String, nullable=True)
    date_diagnosed = Column(String)
    status = Column(String) # Active, Resolved
    notes = Column(Text)

    patient = relationship("Patient", back_populates="problems")

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String)
    dosage = Column(String)
    frequency = Column(String)
    route = Column(String) # Oral, IV, etc
    prescribed_by = Column(String)
    start_date = Column(String)
    end_date = Column(String, nullable=True)
    status = Column(String) # Active, Discontinued

    patient = relationship("Patient", back_populates="medications")

class SocialHistory(Base):
    __tablename__ = "social_history"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    smoking_status = Column(String)
    alcohol_use = Column(String)
    occupation = Column(String)
    living_arrangement = Column(String)
    diet = Column(String)
    exercise = Column(String)

    patient = relationship("Patient", back_populates="social_history")

class FamilyHistory(Base):
    __tablename__ = "family_history"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    relation = Column(String)
    condition = Column(String)
    age_of_onset = Column(String)
    
    patient = relationship("Patient", back_populates="family_history")

class CareTeam(Base):
    __tablename__ = "care_team"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    role = Column(String) # PCP, Cardiologist, etc.
    name = Column(String) # If simulated and not in doctors table
    phone = Column(String)

    patient = relationship("Patient", back_populates="care_team")
    doctor = relationship("Doctor", back_populates="care_team_entries")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    test_name = Column(String) # e.g. "Lipid Panel"
    value = Column(Float)
    unit = Column(String)
    ref_range_min = Column(Float)
    ref_range_max = Column(Float)
    interpretation = Column(String) # "High", "Normal", "Low"
    performed_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="results")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    date = Column(DateTime)
    reason = Column(String)
    status = Column(String, default="Scheduled")

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    phone_number = Column(String)
    query = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="logs")
