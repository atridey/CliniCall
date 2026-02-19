from app.database import SessionLocal, engine, Base
from app.models import (
    Patient, Doctor, TestResult, Appointment, Insurance, VitalSign, 
    Immunization, Problem, Medication, SocialHistory, FamilyHistory, CareTeam
)
from datetime import datetime, timedelta
import random

# Recreate tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("Seeding database with comprehensive MyChart-style data...")

# 1. Doctors
doctors_data = [
    {"name": "Dr. Sarah Smith", "specialty": "Internal Medicine", "phone": "555-0001", "email": "s.smith@clinicall.com"},
    {"name": "Dr. James Wilson", "specialty": "Cardiology", "phone": "555-0002", "email": "j.wilson@clinicall.com"},
    {"name": "Dr. Emily Chen", "specialty": "Endocrinology", "phone": "555-0003", "email": "e.chen@clinicall.com"},
    {"name": "Dr. Robert Johnson", "specialty": "Orthopedics", "phone": "555-0004", "email": "r.johnson@clinicall.com"},
    {"name": "Dr. Lisa Patel", "specialty": "Dermatology", "phone": "555-0005", "email": "l.patel@clinicall.com"}
]

doctors = []
for d in doctors_data:
    doc = Doctor(**d)
    db.add(doc)
    doctors.append(doc)
db.commit()

# Helper for random date
def rand_date(days_back=365):
    return datetime.now() - timedelta(days=random.randint(0, days_back))

def rand_future_date(days_forward=30):
    return datetime.now() + timedelta(days=random.randint(1, days_forward))

# 2. Patients Data
# We preserve John and Jane, plus 8 new ones.
patients_seeds = [
    {
        "first_name": "John", "last_name": "Doe", "dob": "1945-05-15", "gender": "Male",
        "phone_number": "555-0123", "address": "123 Maple Ave, Springfield, IL",
        "emergency_contact_name": "Mary Doe", "emergency_contact_phone": "555-0999", "emergency_contact_relation": "Wife",
        "marital_status": "Married", "preferred_pharmacy": "CVS Pharmacy #421",
        "allergies_summary": "Penicillin (Severe), Peanuts (Mild)",
        "medical_history_summary": "Hypertension (2010), T2 Diabetes (2015), Osteoarthritis",
        "profile": "chronic_mgmt"
    },
    {
        "first_name": "Jane", "last_name": "Roe", "dob": "1950-11-20", "gender": "Female",
        "phone_number": "555-0124", "address": "456 Oak St, Springfield, IL",
        "emergency_contact_name": "Richard Roe", "emergency_contact_phone": "555-0888", "emergency_contact_relation": "Husband",
        "marital_status": "Married", "preferred_pharmacy": "Walgreens #108 - Main St",
        "allergies_summary": "Sulfa Drugs",
        "medical_history_summary": "Asthma, Hypothyroidism, Osteoporosis",
        "profile": "respiratory"
    },
    # 8 New Patients
    {
        "first_name": "Robert", "last_name": "Frost", "dob": "1938-03-26", "gender": "Male",
        "phone_number": "555-0130", "address": "88 Winter Ln, Starkville",
        "emergency_contact_name": "Elinor Frost", "emergency_contact_phone": "555-1111", "emergency_contact_relation": "Wife",
        "marital_status": "Married", "preferred_pharmacy": "Community Care Rx #5",
        "allergies_summary": "Latex",
        "medical_history_summary": "COPD, History of MI (2018)",
        "profile": "cardio_resp"
    },
    {
        "first_name": "Emily", "last_name": "Dickinson", "dob": "1948-12-10", "gender": "Female",
        "phone_number": "555-0131", "address": "280 Main St, Amherst",
        "emergency_contact_name": "Lavinia Dickinson", "emergency_contact_phone": "555-2222", "emergency_contact_relation": "Sister",
        "marital_status": "Single", "preferred_pharmacy": "CVS Pharmacy #12",
        "allergies_summary": "None",
        "medical_history_summary": "Anxiety, Glaucoma",
        "profile": "geriatric_general"
    },
    {
        "first_name": "Walt", "last_name": "Whitman", "dob": "1942-05-31", "gender": "Male",
        "phone_number": "555-0132", "address": "15 Leaves Blvd, Camden",
        "emergency_contact_name": "George Whitman", "emergency_contact_phone": "555-3333", "emergency_contact_relation": "Brother",
        "marital_status": "Widowed", "preferred_pharmacy": "Walgreens #882",
        "allergies_summary": "Seasonal Pollen",
        "medical_history_summary": "Stroke (2020) - Left side weakness",
        "profile": "neuro_rehab"
    },
    {
        "first_name": "Maya", "last_name": "Angelou", "dob": "1955-04-04", "gender": "Female",
        "phone_number": "555-0133", "address": "7 Caged Bird Way, St. Louis",
        "emergency_contact_name": "Guy Johnson", "emergency_contact_phone": "555-4444", "emergency_contact_relation": "Son",
        "marital_status": "Divorced", "preferred_pharmacy": "Rite Aid #441",
        "allergies_summary": "Shellfish",
        "medical_history_summary": "Arthritis, Hypertension",
        "profile": "chronic_mgmt"
    },
    {
        "first_name": "Langston", "last_name": "Hughes", "dob": "1935-02-01", "gender": "Male",
        "phone_number": "555-0134", "address": "20 Harlem Ave, New York",
        "emergency_contact_name": "Carrie Hughes", "emergency_contact_phone": "555-5555", "emergency_contact_relation": "Daughter",
        "marital_status": "Widowed", "preferred_pharmacy": "Duane Reade #77",
        "allergies_summary": "Aspirin",
        "medical_history_summary": "CHF (Congestive Heart Failure), CKD Stage 3",
        "profile": "complex_cardio"
    },
    {
        "first_name": "Sylvia", "last_name": "Plath", "dob": "1960-10-27", "gender": "Female",
        "phone_number": "555-0135", "address": "5 Bell Jar Ct, London",
        "emergency_contact_name": "Warren Plath", "emergency_contact_phone": "555-6666", "emergency_contact_relation": "Brother",
        "marital_status": "Married", "preferred_pharmacy": "Boots #99 (UK)",
        "allergies_summary": "Bee Stings",
        "medical_history_summary": "Depression, Migraines",
        "profile": "neuro_psych"
    },
    {
        "first_name": "Oscar", "last_name": "Wilde", "dob": "1958-10-16", "gender": "Male",
        "phone_number": "555-0136", "address": "90 Dorian Gray Ln, Dublin",
        "emergency_contact_name": "Constance Lloyd", "emergency_contact_phone": "555-7777", "emergency_contact_relation": "Wife",
        "marital_status": "Married", "preferred_pharmacy": "Local Care Pharmacy #1",
        "allergies_summary": "None",
        "medical_history_summary": "Gout, Obstructive Sleep Apnea",
        "profile": "metabolic"
    },
    {
        "first_name": "Virginia", "last_name": "Woolf", "dob": "1949-01-25", "gender": "Female",
        "phone_number": "555-0137", "address": "22 Lighthouse Rd, Sussex",
        "emergency_contact_name": "Leonard Woolf", "emergency_contact_phone": "555-8888", "emergency_contact_relation": "Husband",
        "marital_status": "Married", "preferred_pharmacy": "CVS Pharmacy #22",
        "allergies_summary": "Codeine",
        "medical_history_summary": "Bipolar Disorder, History of Falls",
        "profile": "geriatric_risk"
    }
]

# Generators for specific profile data
def generate_clinical_data(patient_id, profile, db_session):
    # Insurance
    ins = Insurance(
        patient_id=patient_id,
        provider=random.choice(["Blue Cross", "Aetna", "Medicare", "UnitedHealth"]),
        policy_number=f"POL-{random.randint(100000, 999999)}",
        group_number=f"GRP-{random.randint(1000, 9999)}",
        plan_type=random.choice(["HMO", "PPO", "Medicare Advantage"]),
        subscriber_id=f"SUB-{random.randint(1000000, 9999999)}"
    )
    db_session.add(ins)

    # Social History
    smoking = "Never"
    if profile in ["cardio_resp", "complex_cardio"]: smoking = "Former Smoker (Quit 2010)"
    social = SocialHistory(
        patient_id=patient_id,
        smoking_status=smoking,
        alcohol_use="Occasional",
        occupation="Retired",
        living_arrangement=random.choice(["With Spouse", "Alone", "Assisted Living"]),
        diet="Low Sodium" if "cardio" in profile else "Regular",
        exercise="Sedentary" if "rehab" in profile else "Walking 3x/week"
    )
    db_session.add(social)
    
    # Problems & Meds
    problems = []
    meds = []
    
    if profile == "chronic_mgmt":
        problems = [("Essential Hypertension", "Active"), ("Type 2 Diabetes", "Active"), ("Hyperlipidemia", "Active")]
        meds = [
            ("Lisinopril", "10mg", "Daily", "Dr. Smith"),
            ("Metformin", "500mg", "BID", "Dr. Chen"),
            ("Atorvastatin", "20mg", "Nightly", "Dr. Smith")
        ]
    elif profile == "cardio_resp":
        problems = [("COPD", "Active"), ("Coronary Artery Disease", "Active")]
        meds = [("Albuterol Inhaler", "90mcg", "PRN", "Dr. Smith"), ("Clopidogrel", "75mg", "Daily", "Dr. Wilson")]
    elif profile == "complex_cardio":
         problems = [("Congestive Heart Failure", "Active"), ("Chronic Kidney Disease Stage 3", "Active"), ("Atrial Fibrillation", "Active")]
         meds = [("Furosemide", "40mg", "Daily", "Dr. Wilson"), ("Carvedilol", "12.5mg", "BID", "Dr. Wilson"), ("Eliquis", "5mg", "BID", "Dr. Wilson")]
    else: # General/Others
         problems = [("Osteoarthritis", "Active"), ("GERD", "Active")]
         meds = [("Omeprazole", "20mg", "Daily", "Dr. Smith"), ("Tylenol", "500mg", "PRN Pain", "Dr. Johnson")]

    for p_name, p_status in problems:
        db_session.add(Problem(patient_id=patient_id, name=p_name, date_diagnosed=rand_date(3000).strftime("%Y-%m-%d"), status=p_status))
    
    for m_name, m_dose, m_freq, m_doc in meds:
        db_session.add(Medication(patient_id=patient_id, name=m_name, dosage=m_dose, frequency=m_freq, prescribed_by=m_doc, start_date=rand_date(500).strftime("%Y-%m-%d"), status="Active"))

    # Vitals (Last 3 visits)
    for i in range(3):
        ts = rand_date(days_back=90 - (i*30))
        # BP
        sys = random.randint(110, 150)
        dia = random.randint(70, 95)
        db_session.add(VitalSign(patient_id=patient_id, timestamp=ts, type="BP", value=f"{sys}/{dia}", unit="mmHg"))
        # HR
        db_session.add(VitalSign(patient_id=patient_id, timestamp=ts, type="Heart Rate", value=str(random.randint(60, 100)), unit="bpm"))
        # Weight
        db_session.add(VitalSign(patient_id=patient_id, timestamp=ts, type="Weight", value=str(random.randint(140, 220)), unit="lbs"))
        # O2
        db_session.add(VitalSign(patient_id=patient_id, timestamp=ts, type="O2 Sat", value=str(random.randint(94, 100)), unit="%"))

    # Care Team
    # Assign a random PCP
    pcp = doctors[0] # Default Dr. Smith
    db_session.add(CareTeam(patient_id=patient_id, doctor_id=pcp.id, role="PCP", name=pcp.name, phone=pcp.phone))
    if "cardio" in profile:
        cardio = doctors[1] # Dr. Wilson
        db_session.add(CareTeam(patient_id=patient_id, doctor_id=cardio.id, role="Cardiologist", name=cardio.name, phone=cardio.phone))

    # Appointments
    # 1 Past
    db_session.add(Appointment(patient_id=patient_id, doctor_id=pcp.id, date=rand_date(30), reason="Routine Follow-up", status="Completed"))
    # 1 Future
    db_session.add(Appointment(patient_id=patient_id, doctor_id=pcp.id, date=rand_future_date(), reason="Check-up", status="Scheduled"))

    # Test Results
    if "diabetes" in str(problems).lower():
        db_session.add(TestResult(patient_id=patient_id, test_name="Hemoglobin A1c", value=random.uniform(6.5, 8.5), unit="%", interpretation="High"))
    
    db_session.add(TestResult(patient_id=patient_id, test_name="Basic Metabolic Panel", value=0, unit="N/A", interpretation="Normal"))


# Create Patients
for p_data in patients_seeds:
    profile_type = p_data.pop("profile")
    patient = Patient(**p_data)
    patient.password_hash = "hashed_secret"
    db.add(patient)
    db.commit()
    
    generate_clinical_data(patient.id, profile_type, db)

print("Database seeded effectively with 10 extended profiles!")
db.close()
