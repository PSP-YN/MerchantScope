from __future__ import annotations
import json, uuid
from datetime import datetime, timedelta, timezone
from collections import Counter
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .models import Merchant, MerchantProfile, Transaction, MerchantEvent, BehaviouralFeature, RiskAssessment, RiskSignal, EntityNode, EntityEdge, Investigation, AuditLog

WEIGHTS = {"behaviour": .25, "category": .25, "graph": .25, "payment": .15, "context": .10}
def _uid(prefix): return f"{prefix}_{uuid.uuid4().hex[:12]}"
def _aware(dt):
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

def transaction_frame(rows):
    return pd.DataFrame([{"amount":r.amount,"status":r.status,"customer":r.customer_token,"device":r.device_token,"settlement":r.settlement_token,"hour":_aware(r.occurred_at).hour,"occurred_at":_aware(r.occurred_at)} for r in rows])

def merchant_features(db: Session, merchant: Merchant, window_days: int = 30):
    rows = db.scalars(select(Transaction).where(Transaction.merchant_id==merchant.id).order_by(Transaction.occurred_at)).all()
    if not rows: return {"sufficient_history":False,"sample_size":0,"transaction_count":0,"daily_count":0,"avg_ticket":0,"refund_rate":0,"failed_rate":0,"night_share":0,"customer_concentration":0}
    df=transaction_frame(rows); now=max(df.occurred_at); cutoff=now-timedelta(days=window_days)
    current=df[df.occurred_at>=cutoff]; baseline=df[df.occurred_at<cutoff]
    if current.empty: current=df.tail(max(1,min(len(df),30)))
    daily=current.groupby(current.occurred_at.dt.date).size()
    cust=current.customer.value_counts(normalize=True)
    profile=merchant.profile
    enough= len(baseline)>=30 and len(current)>=10
    if profile and enough:
        profile.baseline_daily_count=float(baseline.groupby(baseline.occurred_at.dt.date).size().mean())
        profile.baseline_avg_ticket=float(baseline.amount.mean())
        profile.baseline_refund_rate=float(baseline.status.eq("refunded").mean())
        profile.baseline_failed_rate=float(baseline.status.eq("failed").mean())
        profile.baseline_night_share=float(baseline.hour.lt(7).sum()+baseline.hour.ge(22).sum())/len(baseline)
        profile.baseline_customer_concentration=float(baseline.customer.value_counts(normalize=True).head(5).sum())
    return {"sufficient_history":enough,"sample_size":len(baseline),"transaction_count":len(current),"daily_count":float(daily.mean()) if len(daily) else 0,
        "avg_ticket":float(current.amount.mean()),"refund_rate":float(current.status.eq("refunded").mean()),"failed_rate":float(current.status.eq("failed").mean()),
        "night_share":float((current.hour.lt(7)|current.hour.ge(22)).mean()),"customer_concentration":float(cust.head(5).sum()) if len(cust) else 0}

def graph_metrics(db: Session, merchant_id: str):
    rows=db.scalars(select(Transaction).where(Transaction.merchant_id==merchant_id)).all()
    ids={"device":Counter(r.device_token for r in rows),"customer":Counter(r.customer_token for r in rows),"settlement":Counter(r.settlement_token for r in rows)}
    G=nx.Graph(); G.add_node(merchant_id,kind="merchant")
    shared=0; evidence=[]
    for kind,counter in ids.items():
        for token,count in counter.items():
            other=db.scalars(select(Transaction.merchant_id).where(getattr(Transaction,{"device":"device_token","customer":"customer_token","settlement":"settlement_token"}[kind])==token).distinct()).all()
            if len(other)>1:
                node=f"{kind}:{token}"; G.add_node(node,kind=kind); G.add_edge(merchant_id,node,relation=f"shared_{kind}",evidence=count)
                shared+=1; evidence.append({"entity_id":node,"entity_type":kind,"merchant_count":len(other),"evidence_count":count})
    degree=G.degree(merchant_id)
    return min(100,shared*12),int(degree),evidence,G

def evaluate_merchant(db: Session, merchant: Merchant, persist: bool=True):
    f=merchant_features(db,merchant); profile=merchant.profile
    signals=[]; components={"behaviour":0.0,"category":0.0,"graph":0.0,"payment":0.0,"context":0.0}; known=0
    if f["sufficient_history"] and profile:
        known+=1
        comparisons=[
            ("volume","Daily volume shift",f["daily_count"],profile.baseline_daily_count,2.0,3.0,"× baseline"),
            ("ticket","Average ticket shift",f["avg_ticket"],profile.baseline_avg_ticket,1.6,2.5,"× baseline"),
            ("refund","Refund deterioration",f["refund_rate"],profile.baseline_refund_rate,.04,.10,"absolute rate increase"),
            ("failed","Failed payment increase",f["failed_rate"],profile.baseline_failed_rate,.05,.12,"absolute rate increase"),
            ("hours","Operating-hour drift",f["night_share"],profile.baseline_night_share,.10,.25,"share increase"),
            ("concentration","Customer concentration",f["customer_concentration"],profile.baseline_customer_concentration,.15,.30,"share increase")]
        points=0
        for key,label,value,base,moderate,severe,unit in comparisons:
            delta=(value/max(base,.005)) if key in {"volume","ticket"} else value-base
            threshold=severe if key in {"volume","ticket"} else severe
            if delta>=severe: p=22
            elif delta>=moderate: p=11
            else: continue
            points+=p; signals.append({"key":key,"label":label,"points":p,"detail":f"Current {value:.3f}; baseline {base:.3f}; {unit}"})
        components["behaviour"]=min(100,points*100/88)
        components["payment"]=min(100,(f["refund_rate"]>max(.08,profile.baseline_refund_rate+.06))*55+(f["failed_rate"]>max(.12,profile.baseline_failed_rate+.08))*45)
    else:
        signals.append({"key":"history","label":"Insufficient baseline history","points":0,"detail":f"Baseline sample {f['sample_size']}; at least 30 baseline and 10 current transactions required."})
    # Category mismatch is deliberately a rules-based review cue, not a prohibited-activity classifier.
    desc=(merchant.declared_description or "").lower()
    mismatch_terms={"bakery":["casino","betting","wager","gambling"],"restaurant":["casino","betting","wager","gambling"],"grocery":["casino","betting","wager","gambling"],"electronics":["casino","betting","wager","gambling"],"clothing":["casino","betting","wager","gambling"]}
    hits=[x for x in mismatch_terms.get(merchant.category,[]) if x in desc]
    components["category"]=80.0 if hits else 0.0
    if hits: signals.append({"key":"category","label":"Declared activity description requires review","points":10,"detail":"Declared business description contains terms outside the merchant's stated category; human verification required."})
    graph_score,degree,entities,G=graph_metrics(db,merchant.id); components["graph"]=graph_score
    if graph_score: signals.append({"key":"graph","label":"Shared entity relationships","points":min(25,degree*5),"detail":f"{degree} shared pseudonymous entity relationships require contextual review."})
    events=db.scalars(select(MerchantEvent).where(MerchantEvent.merchant_id==merchant.id)).all()
    unresolved=[e for e in events if e.verification_status!="verified"]
    if unresolved:
        components["context"]=min(100,20*len(unresolved))
        signals.append({"key":"context","label":"Business-change context is unverified","points":5,"detail":f"{len(unresolved)} context event(s) are declared but not independently verified."})
    # Isolation Forest runs on the cross-sectional feature vector when enough portfolio rows exist.
    portfolio=[]
    for m in db.scalars(select(Merchant)).all():
        ff=merchant_features(db,m)
        if ff["sufficient_history"]: portfolio.append([ff[k] for k in ["daily_count","avg_ticket","refund_rate","failed_rate","night_share","customer_concentration"]])
    if len(portfolio)>=20 and f["sufficient_history"]:
        model=IsolationForest(n_estimators=100,contamination=.10,random_state=42)
        model.fit(np.asarray(portfolio,dtype=float))
        pred=float(model.decision_function(np.asarray([[f[k] for k in ["daily_count","avg_ticket","refund_rate","failed_rate","night_share","customer_concentration"]]],dtype=float))[0])
        if pred<-.08: components["behaviour"]=max(components["behaviour"],min(100,abs(pred)*500))
    # Missing dimensions are excluded and remaining weights renormalized; confidence is reported separately.
    available={k:v for k,v in components.items() if k not in {"behaviour","payment"} or f["sufficient_history"]}
    denom=sum(WEIGHTS[k] for k in available)
    score=round(sum(WEIGHTS[k]*v for k,v in available.items())/denom,1) if denom else 0.0
    confidence=round(100*(.35 if f["sufficient_history"] else .05)+.15*(bool(entities))+.15*(bool(events))+.35*(len(portfolio)>=20),1)
    severity="high" if score>=65 else "medium" if score>=35 else "low"
    explanation=f"{len(signals)} explainable signal(s); {len(available)} score dimensions available. Score is a review-priority index, not a probability."
    result={"risk_score":score,"confidence":confidence,"severity":severity,"signals":signals,"components":components,"features":f,"graph":{"shared_entities":entities,"shared_entity_count":degree},"explanation":explanation}
    if persist:
        aid=_uid("risk"); assessment=RiskAssessment(id=aid,merchant_id=merchant.id,risk_score=score,confidence=confidence,severity=severity,explanation=explanation,components_json=json.dumps(components))
        db.add(assessment); db.flush()
        for s in signals: db.add(RiskSignal(assessment_id=aid,key=s["key"],label=s["label"],points=s["points"],detail=s["detail"]))
        db.add(BehaviouralFeature(merchant_id=merchant.id,transaction_count=f["transaction_count"],daily_count=f["daily_count"],avg_ticket=f["avg_ticket"],refund_rate=f["refund_rate"],failed_rate=f["failed_rate"],night_share=f["night_share"],customer_concentration=f["customer_concentration"]))
        db.add(AuditLog(actor="trace-engine",role="system",action="risk.assessed",resource_type="merchant",resource_id=merchant.id,reason=f"Assessment {aid}: {severity} review priority"))
        result["assessment_id"]=aid
    return result
