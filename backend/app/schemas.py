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

class ContextReview(BaseModel):
    verification_status: str = Field(pattern="^(unverified|partially_verified|verified|rejected)$")
    review_reason: str = Field(min_length=8, max_length=1000)

from datetime import datetime, timezone

class MerchantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(pattern="^(bakery|restaurant|grocery|electronics|clothing|other)$")
    declared_description: str = Field(default="", max_length=2000)

class TransactionIngest(BaseModel):
    merchant_id: str = Field(min_length=3, max_length=40)
    amount: float = Field(gt=0, le=100000000)
    status: str = Field(default="settled", pattern="^(settled|refunded|failed|reversed|pending)$")
    channel: str = Field(default="upi", pattern="^(upi|card|wallet|online|pos|bank_transfer|other)$")
    customer_token: str = Field(min_length=3, max_length=64)
    device_token: str = Field(min_length=3, max_length=64)
    settlement_token: str = Field(min_length=3, max_length=64)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    synthetic: bool = True

class TransactionBatch(BaseModel):
    transactions: list[TransactionIngest] = Field(min_length=1, max_length=1000)
