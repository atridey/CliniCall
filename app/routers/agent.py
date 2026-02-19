from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from ..services.patient_service import PatientService, get_patient_service
from ..services.llm_service import LLMService

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentQuery(BaseModel):
    phone_number: str
    query: str
    history: list[dict] = []

class IdentifiedPatient(BaseModel):
    phone_number: str
    first_name: str
    last_name: str
    dob: str

class AgentResponse(BaseModel):
    response_text: str
    identified_patient: IdentifiedPatient | None = None

def get_llm_service(patient_service: PatientService = Depends(get_patient_service)):
    return LLMService(patient_service)

@router.post("/query", response_model=AgentResponse)
async def query_agent(
    request: AgentQuery,
    llm_service: LLMService = Depends(get_llm_service)
):
    response_text, patient = llm_service.process_query(request.phone_number, request.query, request.history)
    
    identified = None
    if patient:
        identified = IdentifiedPatient(
            phone_number=patient.phone_number,
            first_name=patient.first_name,
            last_name=patient.last_name,
            dob=patient.dob
        )
        
    return AgentResponse(response_text=response_text, identified_patient=identified)
