from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def utcnow(): return datetime.now(timezone.utc)
class Merchant(Base):
    __tablename__="merchants"
    id:Mapped[str]=mapped_column(String(40),primary_key=True)
    name:Mapped[str]=mapped_column(String(160),nullable=False)
    category:Mapped[str]=mapped_column(String(40),nullable=False,index=True)
    declared_description:Mapped[str]=mapped_column(Text,default="")
    scenario_label:Mapped[str]=mapped_column(String(40),default="normal")
    onboarding_date:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    status:Mapped[str]=mapped_column(String(24),default="active")
    profile:Mapped["MerchantProfile"]=relationship(back_populates="merchant",uselist=False,cascade="all, delete-orphan")
    transactions:Mapped[list["Transaction"]]=relationship(back_populates="merchant",cascade="all, delete-orphan")
class MerchantProfile(Base):
    __tablename__="merchant_profiles"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id",ondelete="CASCADE"),unique=True,index=True)
    baseline_days:Mapped[int]=mapped_column(Integer,default=60)
    baseline_daily_count:Mapped[float]=mapped_column(Float,default=0)
    baseline_avg_ticket:Mapped[float]=mapped_column(Float,default=0)
    baseline_refund_rate:Mapped[float]=mapped_column(Float,default=0)
    baseline_failed_rate:Mapped[float]=mapped_column(Float,default=0)
    baseline_night_share:Mapped[float]=mapped_column(Float,default=0)
    baseline_customer_concentration:Mapped[float]=mapped_column(Float,default=0)
    merchant:Mapped["Merchant"]=relationship(back_populates="profile")
class Transaction(Base):
    __tablename__="transactions"
    id:Mapped[str]=mapped_column(String(48),primary_key=True)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id",ondelete="CASCADE"),index=True)
    amount:Mapped[float]=mapped_column(Float,nullable=False)
    status:Mapped[str]=mapped_column(String(20),default="settled")
    channel:Mapped[str]=mapped_column(String(20),default="upi")
    customer_token:Mapped[str]=mapped_column(String(64),index=True)
    device_token:Mapped[str]=mapped_column(String(64),index=True)
    settlement_token:Mapped[str]=mapped_column(String(64),index=True)
    occurred_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    synthetic:Mapped[bool]=mapped_column(Boolean,default=True)
    merchant:Mapped["Merchant"]=relationship(back_populates="transactions")
    __table_args__=(Index("ix_tx_merchant_time","merchant_id","occurred_at"),)
class MerchantEvent(Base):
    __tablename__="merchant_events"
    id:Mapped[str]=mapped_column(String(48),primary_key=True)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id",ondelete="CASCADE"),index=True)
    event_type:Mapped[str]=mapped_column(String(40))
    description:Mapped[str]=mapped_column(Text)
    verification_status:Mapped[str]=mapped_column(String(20),default="unverified")
    effective_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class BehaviouralFeature(Base):
    __tablename__="behavioural_features"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id",ondelete="CASCADE"),index=True)
    computed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    window_days:Mapped[int]=mapped_column(Integer,default=30)
    transaction_count:Mapped[int]=mapped_column(Integer,default=0)
    daily_count:Mapped[float]=mapped_column(Float,default=0)
    avg_ticket:Mapped[float]=mapped_column(Float,default=0)
    refund_rate:Mapped[float]=mapped_column(Float,default=0)
    failed_rate:Mapped[float]=mapped_column(Float,default=0)
    night_share:Mapped[float]=mapped_column(Float,default=0)
    customer_concentration:Mapped[float]=mapped_column(Float,default=0)
class RiskAssessment(Base):
    __tablename__="risk_assessments"
    id:Mapped[str]=mapped_column(String(48),primary_key=True)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id",ondelete="CASCADE"),index=True)
    risk_score:Mapped[float]=mapped_column(Float)
    confidence:Mapped[float]=mapped_column(Float)
    severity:Mapped[str]=mapped_column(String(16))
    explanation:Mapped[str]=mapped_column(Text)
    components_json:Mapped[str]=mapped_column(Text,default="{}")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class RiskSignal(Base):
    __tablename__="risk_signals"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    assessment_id:Mapped[str]=mapped_column(ForeignKey("risk_assessments.id",ondelete="CASCADE"),index=True)
    key:Mapped[str]=mapped_column(String(48))
    label:Mapped[str]=mapped_column(String(160))
    points:Mapped[float]=mapped_column(Float)
    detail:Mapped[str]=mapped_column(Text)
    disposition:Mapped[str]=mapped_column(String(24),default="unresolved")
class EntityNode(Base):
    __tablename__="entity_nodes"
    id:Mapped[str]=mapped_column(String(80),primary_key=True)
    entity_type:Mapped[str]=mapped_column(String(24),index=True)
    label:Mapped[str]=mapped_column(String(160))
    synthetic:Mapped[bool]=mapped_column(Boolean,default=True)
class EntityEdge(Base):
    __tablename__="entity_edges"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    source_id:Mapped[str]=mapped_column(ForeignKey("entity_nodes.id",ondelete="CASCADE"),index=True)
    target_id:Mapped[str]=mapped_column(ForeignKey("entity_nodes.id",ondelete="CASCADE"),index=True)
    relation:Mapped[str]=mapped_column(String(48))
    evidence_count:Mapped[int]=mapped_column(Integer,default=1)
    first_seen:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    last_seen:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(UniqueConstraint("source_id","target_id","relation",name="uq_entity_relation"),)
class Investigation(Base):
    __tablename__="investigations"
    id:Mapped[str]=mapped_column(String(48),primary_key=True)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id",ondelete="CASCADE"),index=True)
    assessment_id:Mapped[str]=mapped_column(ForeignKey("risk_assessments.id"))
    status:Mapped[str]=mapped_column(String(24),default="open")
    assigned_to:Mapped[str]=mapped_column(String(120),default="Unassigned")
    outcome:Mapped[str]=mapped_column(String(32),default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class Intervention(Base):
    __tablename__="interventions"
    id:Mapped[str]=mapped_column(String(48),primary_key=True)
    investigation_id:Mapped[str]=mapped_column(ForeignKey("investigations.id",ondelete="CASCADE"),index=True)
    action:Mapped[str]=mapped_column(String(40))
    reason:Mapped[str]=mapped_column(Text)
    approved_by:Mapped[str]=mapped_column(String(120),default="")
    approval_status:Mapped[str]=mapped_column(String(24),default="pending")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class InvestigationNote(Base):
    __tablename__="investigation_notes"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    investigation_id:Mapped[str]=mapped_column(ForeignKey("investigations.id",ondelete="CASCADE"),index=True)
    actor:Mapped[str]=mapped_column(String(120))
    note:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)

class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    actor:Mapped[str]=mapped_column(String(120))
    role:Mapped[str]=mapped_column(String(32))
    action:Mapped[str]=mapped_column(String(80),index=True)
    resource_type:Mapped[str]=mapped_column(String(48))
    resource_id:Mapped[str]=mapped_column(String(80))
    reason:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
