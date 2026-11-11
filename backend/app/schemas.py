from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CaseCreate(BaseModel):
    merchant_id: str
    assessment_id: str
    assigned_to: str = Field(default="Unassigned", max_length=120)

class CaseUpdate(BaseModel):
    status: str = Field(pattern="^(open|investigating|resolved|false_positive|escalated)$")
    note: str = Field(default="", max_length=2000)
    assigned_to: str | None = Field(default=None, max_length=120)
    outcome: str | None = Field(default=None, max_length=32)

class VerificationRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)
    requested_document: str = Field(min_length=3, max_length=120)

class InterventionRequest(BaseModel):
    action: str = Field(pattern="^(enhanced_monitoring|verification_request|manual_review|escalation)$")
    reason: str = Field(min_length=8, max_length=1000)

class InterventionApproval(BaseModel):
    approved: bool
    reason: str = Field(min_length=8, max_length=1000)

class ScenarioRequest(BaseModel):
    merchant_id: str
    scenario: str

class MerchantOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    name: str
    category: str
    status: str
