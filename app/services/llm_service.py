import os
from .patient_service import PatientService
from ..models import Patient
import anthropic
from datetime import datetime

class LLMService:
    def __init__(self, patient_service: PatientService):
        self.patient_service = patient_service
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

    def _get_system_prompt(self, patient: Patient | None, has_history: bool):
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        if not patient:
            # UNKNOWN CALLER CONTEXT
            verification_context = """
CONTEXT:
This is an UNKNOWN caller. Your primary goal is to identify them securely.
You must ask for their Name and Date of Birth.
Once they provide it, use the 'identify_patient' tool to look them up.

INSTRUCTIONS:
1. You are speaking with an unknown caller. Your GOAL is to identify them.
2. Ask for name and date of birth naturally.
3. CRITICAL: BE AGGRESSIVE IN ACCEPTING INPUTS.
   - If the user says "John Doe 1980", "John 1980", "It's John", or ANY fragment that looks like a name/date -> CALL 'identify_patient'.
   - DO NOT ASK for "full sentences" or "clarification" if you have a partial match.
   - BETTER TO GUESS and fail than to ask the user to repeat themselves.
4. Do NOT answer medical questions until identified.
"""
            # Generic patient mock for safety in prompt construction if needed, but we returned above
            patient_context = "Unknown Patient"
        else:
            # KNOWN PATIENT CONTEXT
            if not has_history:
                # Initial verification needed
                verification_context = f"""
CONTEXT:
The call just started. You (the system) ALREADY asked: "Hello, this is CliniCall. For security, please state your full name and date of birth."
You must VERIFY the user's input matches the patient record:
- Expected Name: {patient.first_name} {patient.last_name}
- Expected DOB: {patient.dob}

INSTRUCTIONS:
1. If matches (fuzzy ok), say: "Thank you, {patient.first_name}. How can I help?"
2. If incorrect, politely ask again.
3. If they claim to be someone else, tell them to call from their registered number (or handle as new flow).
"""
            else:
                # History exists
                verification_context = f"""
CONTEXT:
The conversation is ongoing with {patient.first_name} {patient.last_name}.
Proceed with their medical request.
"""
            # Format Full Context
            
            # 1. Medications
            meds_list = []
            for m in patient.medications:
                status = f" ({m.status})" if m.status else ""
                meds_list.append(f"- {m.name} {m.dosage}, {m.frequency} via {m.route}{status}")
            meds_str = "\n".join(meds_list) if meds_list else "None listed"

            # 2. Allergies
            allergies_str = patient.allergies_summary or "No known allergies"

            # 3. Insurance
            ins = patient.insurance
            insurance_str = f"{ins.provider} ({ins.plan_type}) - Policy: {ins.policy_number}" if ins else "Unknown"

            # 4. Social History
            soc = patient.social_history
            social_str = f"Smoking: {soc.smoking_status}, Alcohol: {soc.alcohol_use}, Occupation: {soc.occupation}" if soc else "Not recorded"

            # 5. Vitals (Latest)
            vitals_list = []
            # Sort by timestamp desc if possible, or just take last few
            sorted_vitals = sorted(patient.vitals, key=lambda v: v.timestamp if v.timestamp else datetime.min, reverse=True)[:5]
            for v in sorted_vitals:
                vitals_list.append(f"- {v.type}: {v.value} {v.unit} ({v.timestamp.strftime('%Y-%m-%d')})")
            vitals_str = "\n".join(vitals_list) if vitals_list else "No recent vitals"

            # 6. Problems
            probs_list = [f"- {p.name} ({p.status})" for p in patient.problems]
            probs_str = "\n".join(probs_list) if probs_list else "None"

            # 7. Immunizations (Last 5)
            imm_list = [f"- {i.vaccine_name} ({i.date_administered})" for i in patient.immunizations[:5]]
            imm_str = "\n".join(imm_list) if imm_list else "None"

            patient_context = f"""
You are speaking with {patient.first_name} {patient.last_name}
Age: {2024 - int(patient.dob[:4]) if patient.dob and len(patient.dob) >= 4 else '?'} | Gender: {patient.gender} | Phone: {patient.phone_number}

=== CLINICAL PROFILE ===
[ALLERGIES]
{allergies_str}

[MEDICATIONS]
{meds_str}

[ACTIVE PROBLEMS]
{probs_str}

[INSURANCE]
{insurance_str}

[PHARMACY]
{patient.preferred_pharmacy or "Unknown"}

[LATEST VITALS]
{vitals_str}

[SOCIAL HISTORY]
{social_str}

[IMMUNIZATIONS]
{imm_str}

[MEDICAL HISTORY SUMMARY]
{patient.medical_history_summary}

{{unread_messages_block}}
"""

        return f"""
You are CliniCall, a medical assistant.
Your responses will be spoken (Text-to-Speech).
Current Date/Time: {current_time}

CRITICAL INSTRUCTIONS:
1. BE EXTREMELY CONCISE. Aim for 1-2 short sentences.
2. Speak slowly and clearly.
3. NO emojis, lists, or formatting.
4. If the patient has UNREAD MESSAGES, mention them naturally at the start of the conversation. Offer to read them and accept a reply.

{verification_context}

{patient_context}
"""

    def _build_system_prompt(self, patient, has_history: bool, unread_messages: list):
        """Build the system prompt, filling in the unread messages block."""
        template = self._get_system_prompt(patient, has_history)
        if unread_messages:
            msgs_text = "\n".join(
                f"- From {m.sender_name} ({m.timestamp.strftime('%b %d')}): {m.body}"
                for m in unread_messages
            )
            block = f"[UNREAD DOCTOR MESSAGES]\nYou have {len(unread_messages)} unread message(s) from your care team:\n{msgs_text}"
        else:
            block = ""
        return template.replace("{unread_messages_block}", block)

    def process_query(self, patient_phone: str, user_query: str, history: list[dict] = []):
        # 1. Identify Patient
        patient = None
        if patient_phone != "555-9999":
            patient = self.patient_service.get_patient_by_phone(patient_phone)
        
        # 1b. Fetch unread messages for known patient
        unread_messages = []
        if patient:
            unread_messages = self.patient_service.get_unread_messages(patient.id)

        # 2. Add Context (Results, Appointments) -> Only if patient known
        context_str = ""
        if patient:
            results = self.patient_service.get_patient_results(patient.id)
            appointments = self.patient_service.get_patient_appointments(patient.id)
            
            context_str = "Recent Test Results:\n"
            if results:
                for r in results:
                    context_str += f"- {r.test_name}: {r.value} {r.unit} ({r.interpretation})\n"
            else:
                context_str += "No recent results.\n"
            
            if appointments:
                context_str += "\nAppointments:\n"
                for a in appointments:
                    if a.status == "Cancelled":
                        continue
                    context_str += f"- ID {a.id}: {a.date} ({a.status}) with {a.doctor.name}\n"

        # 3. Define Tools
        tools = [
            {
                "name": "identify_patient",
                "description": "Look up a patient by name and DOB. Use this when an unknown caller provides their identity.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name_query": {"type": "string", "description": "Name provided by user"},
                        "dob_query": {"type": "string", "description": "DOB provided by user (e.g. 1980, or full date)"}
                    },
                    "required": ["name_query"]
                }
            },
            {
                "name": "book_appointment",
                "description": "Book a new appointment. Date must be ISO 8601.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                         "date": {"type": "string", "description": "ISO 8601 date AND time (e.g. 2024-12-01T10:00:00)."},
                        "reason": {"type": "string", "description": "Reason for appointment"},
                        "doctor_name": {"type": "string", "description": "Name of the doctor (optional)."}
                    },
                    "required": ["date", "reason"]
                }
            },
            {
                "name": "cancel_appointment",
                "description": "Cancel an appointment by ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {"type": "integer", "description": "ID of the appointment"}
                    },
                    "required": ["appointment_id"]
                }
            },
            {
                "name": "reschedule_appointment",
                "description": "Reschedule an existing appointment.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {"type": "integer"},
                        "new_date": {"type": "string"}
                    },
                    "required": ["appointment_id", "new_date"]
                }
            },
            {
                "name": "update_pharmacy",
                "description": "Update the patient's preferred pharmacy.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pharmacy_name": {"type": "string", "description": "The new pharmacy name (e.g. 'CVS on Main St')"}
                    },
                    "required": ["pharmacy_name"]
                }
            },
            {
                "name": "send_message_reply",
                "description": "Send a message reply from the patient back to their care team. Use this when the patient wants to reply to a doctor message or send a new message.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "body": {"type": "string", "description": "The message body to send from the patient."}
                    },
                    "required": ["body"]
                }
            }
        ]

        # 4. Call LLM (Claude)
        response_text = ""
        identified_patient = None

        try:
             # Basic Mock if no key
            if not self.client:
                return "I'm sorry, I cannot process your request without a brain connection.", None

            # Build messages from history + current query
            llm_messages = []
            for msg in history:
                role = "user" if msg['role'] == 'user' else "assistant"
                llm_messages.append({"role": role, "content": msg['content']})
            
            # Add current query
            llm_messages.append({"role": "user", "content": f"Context data:\n{context_str}\n\nPatient Query: {user_query}"})
            
            sys_prompt = self._build_system_prompt(patient, has_history=len(history) > 0, unread_messages=unread_messages)
            
            # DEBUG checks
            print("--- DEBUG SYSTEM PROMPT ---")
            print(sys_prompt)
            print("--- USER QUERY ---")
            print(user_query)
            print("--- END DEBUG ---")

            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                temperature=0.7,
                system=sys_prompt,
                messages=llm_messages,
                tools=tools
            )
            
            # 5. Handle Tool Use or Text Response
            if message.stop_reason == "tool_use":
                tool_use = message.content[-1] # Assume last block is tool use
                tool_name = tool_use.name
                tool_input = tool_use.input
                
                if tool_name == "identify_patient":
                    # Logic to find patient
                    # We can use the patient_service to search all patients
                    # For now, let's just iterate all patients in DB or add a search method
                    # Simplest: Get all and fuzzy match in python
                    found = self.patient_service.fuzzy_search_patient(tool_input['name_query'], tool_input.get('dob_query'))
                    
                    if found:
                        identified_patient = found
                        response_text = f"Thank you, {found.first_name}. I have found your record. How can I help you today?"
                    else:
                        response_text = "I'm sorry, I couldn't find a record matching that name and date of birth. Could you please repeat it?"

                elif tool_name == "book_appointment":
                    doctor_name = tool_input.get('doctor_name')
                    # require patient
                    if not patient:
                        response_text = "I need to identify you first before booking."
                    else:
                        appt = self.patient_service.book_appointment(patient.id, tool_input['date'], tool_input['reason'], doctor_name)
                        if appt:
                            response_text = f"I have booked your appointment with Dr. {appt.doctor.name} for {appt.date.strftime('%B %d at %I:%M %p')}."
                        else:
                            response_text = "I'm sorry, I couldn't understand the date. Please try again."
                
                elif tool_name == "cancel_appointment":
                    success = self.patient_service.cancel_appointment(tool_input['appointment_id'])
                    if success:
                        response_text = "I have cancelled that appointment for you."
                    else:
                        response_text = "I couldn't find an appointment with that ID."

                elif tool_name == "reschedule_appointment":
                     appt = self.patient_service.reschedule_appointment(tool_input['appointment_id'], tool_input['new_date'])
                     if appt:
                         response_text = f"I have rescheduled your appointment to {appt.date.strftime('%B %d at %I:%M %p')}."
                     else:
                        response_text = "I couldn't update that appointment. Please check the date or ID."
                
                elif tool_name == "update_pharmacy":
                     if not patient:
                         response_text = "I need to identify you first."
                     else:
                         success = self.patient_service.update_pharmacy(patient.id, tool_input['pharmacy_name'])
                         if success:
                             response_text = f"I have updated your preferred pharmacy to {tool_input['pharmacy_name']}."
                         else:
                             response_text = "I couldn't verified your record to update the pharmacy."

                elif tool_name == "send_message_reply":
                    if not patient:
                        response_text = "I need to identify you first before sending a message."
                    else:
                        sender_name = f"{patient.first_name} {patient.last_name}"
                        self.patient_service.send_patient_message(patient.id, sender_name, tool_input['body'])
                        self.patient_service.mark_messages_read(patient.id)
                        response_text = "Your message has been sent to your care team."

                else:
                    response_text = "I'm sorry, I don't know how to do that."
            else:
                response_text = message.content[0].text

        except Exception as e:
            print(f"LLM Error: {e}")
            response_text = "I'm having trouble connecting to my central system right now."
        
        # 6. Log Call
        try:
            from ..models import CallLog
            from ..database import SessionLocal
            db = SessionLocal()
            log = CallLog(
                patient_id=patient.id if patient else (identified_patient.id if identified_patient else None),
                phone_number=patient.phone_number if patient else (identified_patient.phone_number if identified_patient else patient_phone),
                query=user_query,
                response=response_text
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Logging Error: {e}")

        return response_text, identified_patient
