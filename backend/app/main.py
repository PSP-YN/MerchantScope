from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .db import Base, engine, get_db
from .models import Merchant, Transaction, MerchantEvent, RiskAssessment, RiskSignal, Investigation, Intervention, AuditLog, EntityNode, EntityEdge, InvestigationNote
from .analytics import evaluate_merchant, merchant_features
from .generator import seed_demo, run_scenario, SCENARIOS
from .schemas import CaseUpdate, VerificationRequest, InterventionRequest, InterventionApproval, ScenarioRequest
from .security import actor_context, require_role

app=FastAPI(title="TRACE — Transaction Reality & Activity Consistency Engine",version="1.0.0",description="Explainable merchant-risk intelligence using synthetic demonstration data. Scores prioritize review and are not fraud probabilities.")
origins=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=["GET","POST","PATCH","OPTIONS"],allow_headers=["Authorization","Content-Type","X-Actor","X-Role"])
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    from .db import SessionLocal
    db=SessionLocal()
    try: seed_demo(db)
    finally: db.close()

def _merchant(db,mid):
    m=db.get(Merchant,mid)
    if not m: raise HTTPException(404,"Merchant not found")
    return m

def _latest_assessment(db,mid):
    return db.scalar(select(RiskAssessment).where(RiskAssessment.merchant_id==mid).order_by(RiskAssessment.created_at.desc()).limit(1))

def _case_dict(db,c):
    a=db.get(RiskAssessment,c.assessment_id)
    signals=db.scalars(select(RiskSignal).where(RiskSignal.assessment_id==c.assessment_id)).all()
    m=db.get(Merchant,c.merchant_id)
    return {"id":c.id,"merchant_id":c.merchant_id,"merchant_name":m.name if m else c.merchant_id,"assessment_id":c.assessment_id,
      "risk_score":a.risk_score if a else 0,"confidence":a.confidence if a else 0,"risk_level":a.severity if a else "low","status":c.status,
      "assigned_to":c.assigned_to,"outcome":c.outcome,"signals":[{"key":s.key,"label":s.label,"points":s.points,"detail":s.detail} for s in signals],
      "notes":[{"actor":n.actor,"note":n.note,"created_at":n.created_at.isoformat()} for n in db.scalars(select(InvestigationNote).where(InvestigationNote.investigation_id==c.id).order_by(InvestigationNote.created_at)).all()],
      "created_at":c.created_at.isoformat(),"updated_at":c.updated_at.isoformat()}

@app.get("/health")
def health(db:Session=Depends(get_db)):
    return {"status":"ok","service":"trace-api","data_mode":"synthetic","database":"connected","merchant_count":db.scalar(select(func.count()).select_from(Merchant))}

@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db)):
    merchants=db.scalars(select(Merchant).order_by(Merchant.name)).all();items=[]
    for m in merchants:
        r=evaluate_merchant(db,m,persist=False);f=r["features"]
        items.append({"id":m.id,"name":m.name,"category":m.category,"status":m.status,"risk_score":r["risk_score"],"risk_level":r["severity"],"confidence":r["confidence"],"signals":r["signals"],"explanation":r["explanation"],"features":f})
    total_tx=db.scalar(select(func.count()).select_from(Transaction)) or 0
    high=sum(x["risk_level"]=="high" for x in items);med=sum(x["risk_level"]=="medium" for x in items)
    open_cases=db.scalar(select(func.count()).select_from(Investigation).where(Investigation.status.in_(["open","investigating","escalated"]))) or 0
    verification=db.scalar(select(func.count()).select_from(Intervention).where(Intervention.action=="verification_request")) or 0
    return {"data_mode":"SYNTHETIC DEMO DATA","generated_at":datetime.now(timezone.utc).isoformat(),"metrics":{"merchants_monitored":len(items),"transactions_monitored":total_tx,"high_risk_merchants":high,"open_investigations":open_cases,"verification_requests":verification,"legitimate_anomalies":sum(any(s["key"]=="context" for s in x["signals"]) and x["risk_level"]=="low" for x in items)},"review_queue":high+med},"merchants":items,"scenarios":SCENARIOS}

@app.get("/api/merchants")
def merchants(db:Session=Depends(get_db),q:str|None=None,category:str|None=None):
    stmt=select(Merchant).order_by(Merchant.name)
    if q: stmt=stmt.where(Merchant.name.ilike(f"%{q[:80]}%"))
    if category: stmt=stmt.where(Merchant.category==category)
    result=[]
    for m in db.scalars(stmt).all():
        r=evaluate_merchant(db,m,persist=False);result.append({"id":m.id,"name":m.name,"category":m.category,"status":m.status,"risk_score":r["risk_score"],"risk_level":r["severity"],"confidence":r["confidence"]})
    return result

@app.get("/api/merchants/{merchant_id}")
def merchant_detail(merchant_id:str,db:Session=Depends(get_db)):
    m=_merchant(db,merchant_id);r=evaluate_merchant(db,m,persist=False)
    events=db.scalars(select(MerchantEvent).where(MerchantEvent.merchant_id==merchant_id).order_by(MerchantEvent.effective_at.desc())).all()
    assessments=db.scalars(select(RiskAssessment).where(RiskAssessment.merchant_id==merchant_id).order_by(RiskAssessment.created_at.desc()).limit(10)).all()
    return {"id":m.id,"name":m.name,"category":m.category,"declared_description":m.declared_description,"status":m.status,"onboarding_date":m.onboarding_date.isoformat(),"assessment":r,"events":[{"id":e.id,"event_type":e.event_type,"description":e.description,"verification_status":e.verification_status,"effective_at":e.effective_at.isoformat()} for e in events],"assessment_history":[{"id":a.id,"risk_score":a.risk_score,"confidence":a.confidence,"severity":a.severity,"created_at":a.created_at.isoformat()} for a in assessments]}

@app.get("/api/merchants/{merchant_id}/transactions")
def merchant_transactions(merchant_id:str,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_db)):
    _merchant(db,merchant_id);rows=db.scalars(select(Transaction).where(Transaction.merchant_id==merchant_id).order_by(Transaction.occurred_at.desc()).offset(offset).limit(limit)).all()
    return {"items":[{"id":t.id,"amount":t.amount,"status":t.status,"channel":t.channel,"customer_token":t.customer_token,"device_token":t.device_token,"settlement_token":t.settlement_token,"occurred_at":t.occurred_at.isoformat(),"synthetic":t.synthetic} for t in rows],"limit":limit,"offset":offset}

@app.post("/api/merchants/{merchant_id}/assess")
def assess(merchant_id:str,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"analyst","investigator","admin"});m=_merchant(db,merchant_id);result=evaluate_merchant(db,m,persist=True);db.commit();return result

@app.get("/api/merchants/{merchant_id}/features")
def features(merchant_id:str,db:Session=Depends(get_db)):
    return merchant_features(db,_merchant(db,merchant_id))

@app.get("/api/transactions")
def transactions(merchant_id:str|None=None,limit:int=Query(200,ge=1,le=1000),db:Session=Depends(get_db)):
    stmt=select(Transaction).order_by(Transaction.occurred_at.desc()).limit(limit)
    if merchant_id:stmt=stmt.where(Transaction.merchant_id==merchant_id)
    rows=db.scalars(stmt).all()
    return [{"id":t.id,"merchant_id":t.merchant_id,"amount":t.amount,"status":t.status,"channel":t.channel,"occurred_at":t.occurred_at.isoformat(),"synthetic":t.synthetic} for t in rows]

@app.get("/api/relationships")
def relationships(merchant_id:str|None=None,db:Session=Depends(get_db)):
    stmt=select(EntityEdge)
    if merchant_id:stmt=stmt.where((EntityEdge.source_id==merchant_id)|(EntityEdge.target_id==merchant_id))
    edges=db.scalars(stmt).all();ids={x for e in edges for x in [e.source_id,e.target_id]}
    nodes=db.scalars(select(EntityNode).where(EntityNode.id.in_(ids))).all() if ids else []
    return {"nodes":[{"id":n.id,"label":n.label,"kind":n.entity_type,"synthetic":n.synthetic} for n in nodes],
      "edges":[{"id":e.id,"source":e.source_id,"target":e.target_id,"relation":e.relation,"evidence_count":e.evidence_count,"first_seen":e.first_seen.isoformat(),"last_seen":e.last_seen.isoformat()} for e in edges],
      "notice":"Pseudonymous synthetic relationships. Shared identifiers are investigative leads, not proof of wrongdoing."}

@app.post("/api/scenarios/run")
def simulate(req:ScenarioRequest,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"analyst","investigator","admin"})
    try:result=run_scenario(db,req.merchant_id,req.scenario)
    except LookupError as e:raise HTTPException(404,str(e))
    except ValueError as e:raise HTTPException(422,str(e))
    db.info.pop("trace_portfolio_features",None);db.info.pop("trace_category_features",None)
    db.add(AuditLog(actor=actor["actor"],role=actor["role"],action="scenario.executed",resource_type="merchant",resource_id=req.merchant_id,reason=f"Executed synthetic scenario: {req.scenario}"))
    merchant=_merchant(db,req.merchant_id);assessment=evaluate_merchant(db,merchant,persist=True);db.commit()
    result["assessment"]=assessment
    return result

@app.get("/api/scenarios")
def scenarios():return SCENARIOS

@app.get("/api/investigations")
def investigations(db:Session=Depends(get_db)):
    rows=db.scalars(select(Investigation).order_by(Investigation.updated_at.desc())).all()
    return [_case_dict(db,c) for c in rows]

@app.post("/api/investigations")
def open_investigation(merchant_id:str,assessment_id:str|None=None,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"analyst","investigator","admin"});_merchant(db,merchant_id)
    a=db.get(RiskAssessment,assessment_id) if assessment_id else _latest_assessment(db,merchant_id)
    if not a or a.merchant_id!=merchant_id:
        r=evaluate_merchant(db,_merchant(db,merchant_id),persist=True);a=db.get(RiskAssessment,r["assessment_id"])
    cid=f"case_{uuid.uuid4().hex[:12]}";c=Investigation(id=cid,merchant_id=merchant_id,assessment_id=a.id,assigned_to=actor["actor"])
    db.add(c);db.add(AuditLog(actor=actor["actor"],role=actor["role"],action="investigation.opened",resource_type="investigation",resource_id=cid,reason="Analyst opened a merchant review case."));db.commit()
    return _case_dict(db,c)

@app.patch("/api/investigations/{case_id}")
def update_investigation(case_id:str,update:CaseUpdate,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"analyst","investigator","admin"});c=db.get(Investigation,case_id)
    if not c:raise HTTPException(404,"Investigation not found")
    c.status=update.status;c.updated_at=datetime.now(timezone.utc)
    if update.assigned_to is not None:c.assigned_to=update.assigned_to
    if update.outcome is not None:c.outcome=update.outcome
    if update.note.strip():
        db.add(InvestigationNote(investigation_id=c.id,actor=actor["actor"],note=update.note.strip()))
        db.add(AuditLog(actor=actor["actor"],role=actor["role"],action="investigation.note_added",resource_type="investigation",resource_id=c.id,reason=update.note.strip()))
    db.add(AuditLog(actor=actor["actor"],role=actor["role"],action="investigation.updated",resource_type="investigation",resource_id=c.id,reason=f"Status changed to {update.status}"));db.commit();return _case_dict(db,c)

@app.post("/api/investigations/{case_id}/verification")
def request_verification(case_id:str,req:VerificationRequest,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"analyst","investigator","admin"});c=db.get(Investigation,case_id)
    if not c:raise HTTPException(404,"Investigation not found")
    item=Intervention(id=f"int_{uuid.uuid4().hex[:12]}",investigation_id=c.id,action="verification_request",reason=f"{req.reason} Requested: {req.requested_document}",approved_by=actor["actor"],approval_status="requested")
    db.add(item);db.add(InvestigationNote(investigation_id=c.id,actor=actor["actor"],note=f"Verification requested: {req.reason} Requested document: {req.requested_document}"));db.add(AuditLog(actor=actor["actor"],role=actor["role"],action="verification.requested",resource_type="investigation",resource_id=c.id,reason=req.reason));db.commit()
    return {"id":item.id,"status":item.approval_status,"action":item.action,"reason":item.reason}

@app.post("/api/investigations/{case_id}/interventions")
def propose_intervention(case_id:str,req:InterventionRequest,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"investigator","admin"});c=db.get(Investigation,case_id)
    if not c:raise HTTPException(404,"Investigation not found")
    item=Intervention(id=f"int_{uuid.uuid4().hex[:12]}",investigation_id=c.id,action=req.action,reason=req.reason,approved_by="",approval_status="pending")
    db.add(item);db.add(AuditLog(actor=actor["actor"],role=actor["role"],action="intervention.proposed",resource_type="investigation",resource_id=c.id,reason=req.reason));db.commit()
    return {"id":item.id,"approval_status":item.approval_status,"action":item.action,"consequential_action_implemented":False}

@app.patch("/api/interventions/{intervention_id}/approval")
def approve_intervention(intervention_id:str,req:InterventionApproval,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"reviewer","admin"});item=db.get(Intervention,intervention_id)
    if not item:raise HTTPException(404,"Intervention not found")
    item.approval_status="approved" if req.approved else "rejected";item.approved_by=actor["actor"]
    db.add(AuditLog(actor=actor["actor"],role=actor["role"],action="intervention.approval_recorded",resource_type="intervention",resource_id=item.id,reason=req.reason));db.commit()
    return {"id":item.id,"approval_status":item.approval_status,"approved_by":item.approved_by}


@app.get("/api/interventions")
def list_interventions(db:Session=Depends(get_db)):
    rows=db.scalars(select(Intervention).order_by(Intervention.created_at.desc())).all()
    return [{"id":x.id,"investigation_id":x.investigation_id,"action":x.action,"reason":x.reason,"approved_by":x.approved_by,"approval_status":x.approval_status,"created_at":x.created_at.isoformat()} for x in rows]

@app.get("/api/audit")
def audit(limit:int=Query(200,ge=1,le=1000),db:Session=Depends(get_db)):
    rows=db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [{"id":x.id,"actor":x.actor,"role":x.role,"action":x.action,"resource_type":x.resource_type,"resource_id":x.resource_id,"reason":x.reason,"created_at":x.created_at.isoformat()} for x in rows]

@app.get("/api/evaluation")
def evaluation(db:Session=Depends(get_db)):
    from .evaluation import evaluate_models
    return evaluate_models(db)

@app.post("/api/admin/seed")
def reseed(force:bool=False,db:Session=Depends(get_db),actor:dict=Depends(actor_context)):
    require_role(actor,{"admin"})
    return seed_demo(db,force=force)
