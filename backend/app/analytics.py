from __future__ import annotations
import json, uuid
from datetime import datetime, timedelta, timezone
import pandas as pd
import networkx as nx
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .models import Merchant, Transaction, MerchantEvent, BehaviouralFeature, RiskAssessment, RiskSignal, AuditLog

WEIGHTS={"behaviour":.25,"category":.25,"graph":.25,"payment":.15,"context":.10}
def _uid(p): return f"{p}_{uuid.uuid4().hex[:12]}"
def _aware(dt): return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

def merchant_features(db:Session, merchant:Merchant, window_days:int=30):
    rows=db.scalars(select(Transaction).where(Transaction.merchant_id==merchant.id).order_by(Transaction.occurred_at)).all()
    if not rows:return {"sufficient_history":False,"sample_size":0,"transaction_count":0,"daily_count":0,"avg_ticket":0,"refund_rate":0,"failed_rate":0,"night_share":0,"customer_concentration":0}
    df=pd.DataFrame([{"amount":r.amount,"status":r.status,"customer":r.customer_token,"hour":_aware(r.occurred_at).hour,"occurred_at":_aware(r.occurred_at)} for r in rows])
    cutoff=max(df.occurred_at)-timedelta(days=window_days); current=df[df.occurred_at>=cutoff]; baseline=df[df.occurred_at<cutoff]
    if current.empty:current=df.tail(min(len(df),30))
    daily=current.groupby(current.occurred_at.dt.date).size(); cust=current.customer.value_counts(normalize=True); p=merchant.profile
    enough=len(baseline)>=30 and len(current)>=10
    if p and enough:
        p.baseline_daily_count=float(baseline.groupby(baseline.occurred_at.dt.date).size().mean());p.baseline_avg_ticket=float(baseline.amount.mean())
        p.baseline_refund_rate=float(baseline.status.eq("refunded").mean());p.baseline_failed_rate=float(baseline.status.eq("failed").mean())
        p.baseline_night_share=float((baseline.hour.lt(7)|baseline.hour.ge(22)).mean());p.baseline_customer_concentration=float(baseline.customer.value_counts(normalize=True).head(5).sum())
    return {"sufficient_history":enough,"sample_size":len(baseline),"transaction_count":len(current),"daily_count":float(daily.mean()) if len(daily) else 0,
        "avg_ticket":float(current.amount.mean()),"refund_rate":float(current.status.eq("refunded").mean()),"failed_rate":float(current.status.eq("failed").mean()),
        "night_share":float((current.hour.lt(7)|current.hour.ge(22)).mean()),"customer_concentration":float(cust.head(5).sum()) if len(cust) else 0}

def graph_metrics(db:Session,merchant_id:str):
    rows=db.scalars(select(Transaction).where(Transaction.merchant_id==merchant_id)).all();G=nx.Graph();G.add_node(merchant_id,kind="merchant");evidence=[]
    for kind,attr in [("device","device_token"),("customer","customer_token"),("settlement","settlement_token")]:
        tokens=list({getattr(r,attr) for r in rows})
        if not tokens:continue
        shared=db.execute(select(getattr(Transaction,attr),func.count(func.distinct(Transaction.merchant_id))).where(getattr(Transaction,attr).in_(tokens)).group_by(getattr(Transaction,attr)).having(func.count(func.distinct(Transaction.merchant_id))>1)).all()
        for token,count in shared:
            node=f"{kind}:{token}";G.add_node(node,kind=kind);G.add_edge(merchant_id,node,relation=f"shared_{kind}")
            evidence.append({"entity_id":node,"entity_type":kind,"merchant_count":int(count),"evidence_count":sum(1 for r in rows if getattr(r,attr)==token)})
    return min(100,len(evidence)*12),int(G.degree(merchant_id)),evidence,G

def evaluate_merchant(db:Session,merchant:Merchant,persist:bool=True):
    f=merchant_features(db,merchant);p=merchant.profile;signals=[];c={"behaviour":0.,"category":0.,"graph":0.,"payment":0.,"context":0.}
    if f["sufficient_history"] and p:
        checks=[("volume","Daily volume shift",f["daily_count"],p.baseline_daily_count,2.,3.,True),("ticket","Average ticket shift",f["avg_ticket"],p.baseline_avg_ticket,1.6,2.5,True),
        ("refund","Refund deterioration",f["refund_rate"],p.baseline_refund_rate,.04,.10,False),("failed","Failed payment increase",f["failed_rate"],p.baseline_failed_rate,.05,.12,False),
        ("hours","Operating-hour drift",f["night_share"],p.baseline_night_share,.10,.25,False),("concentration","Customer concentration",f["customer_concentration"],p.baseline_customer_concentration,.15,.30,False)]
        points=0
        for key,label,value,base,moderate,severe,ratio in checks:
            delta=value/max(base,.005) if ratio else value-base
            if delta>=severe:pts=22
            elif delta>=moderate:pts=11
            else:continue
            points+=pts;signals.append({"key":key,"label":label,"points":pts,"detail":f"Current {value:.3f}; baseline {base:.3f}; {'ratio' if ratio else 'absolute change'}"})
        c["behaviour"]=min(100,points*100/132);c["payment"]=min(100,(55 if f["refund_rate"]>max(.08,p.baseline_refund_rate+.06) else 0)+(45 if f["failed_rate"]>max(.12,p.baseline_failed_rate+.08) else 0))
    else:signals.append({"key":"history","label":"Insufficient baseline history","points":0,"detail":f"Baseline sample {f['sample_size']}; at least 30 baseline and 10 current transactions required."})
    hits=[x for x in ["casino","betting","wager","gambling","unlicensed gaming"] if x in (merchant.declared_description or "").lower()]
    c["category"]=80. if hits else 0.
    if hits:signals.append({"key":"category","label":"Declared activity description requires review","points":10,"detail":"Description contains terms outside the stated category; human verification required."})
    gs,degree,entities,G=graph_metrics(db,merchant.id);c["graph"]=gs
    if gs:signals.append({"key":"graph","label":"Shared entity relationships","points":min(25,degree*5),"detail":f"{degree} shared pseudonymous entity relationships require contextual review."})
    events=db.scalars(select(MerchantEvent).where(MerchantEvent.merchant_id==merchant.id)).all();unverified=[e for e in events if e.verification_status!="verified"]
    if unverified:c["context"]=min(100,20*len(unverified));signals.append({"key":"context","label":"Business-change context is unverified","points":5,"detail":f"{len(unverified)} declared context event(s) are not independently verified."})
    portfolio=db.info.get("trace_portfolio_features")
    if portfolio is None:
        portfolio=[]
        for m in db.scalars(select(Merchant)).all():
            ff=merchant_features(db,m)
            if ff["sufficient_history"]:portfolio.append([ff[k] for k in ["daily_count","avg_ticket","refund_rate","failed_rate","night_share","customer_concentration"]])
        db.info["trace_portfolio_features"]=portfolio
    if len(portfolio)>=20 and f["sufficient_history"]:
        model=IsolationForest(n_estimators=100,contamination=.10,random_state=42);model.fit(portfolio)
        anomaly=float(model.decision_function([[f[k] for k in ["daily_count","avg_ticket","refund_rate","failed_rate","night_share","customer_concentration"]]])[0])
        if anomaly<-.08:c["behaviour"]=max(c["behaviour"],min(100,abs(anomaly)*500))
    available={k:v for k,v in c.items() if k not in {"behaviour","payment"} or f["sufficient_history"]};denom=sum(WEIGHTS[k] for k in available)
    score=round(sum(WEIGHTS[k]*v for k,v in available.items())/denom,1) if denom else 0.
    confidence=round(100*((.45 if f["sufficient_history"] else .05)+(.20 if entities else 0)+(.15 if events else 0)+(.20 if len(portfolio)>=20 else 0)),1)
    severity="high" if score>=65 else "medium" if score>=35 else "low"
    explanation=f"{len(signals)} explainable signal(s); {len(available)} score dimensions available. Score is a review-priority index, not a probability."
    result={"risk_score":score,"confidence":confidence,"severity":severity,"signals":signals,"components":c,"features":f,"graph":{"shared_entities":entities,"shared_entity_count":degree},"explanation":explanation}
    if persist:
        aid=_uid("risk");db.add(RiskAssessment(id=aid,merchant_id=merchant.id,risk_score=score,confidence=confidence,severity=severity,explanation=explanation,components_json=json.dumps(c)));db.flush()
        for s in signals:db.add(RiskSignal(assessment_id=aid,key=s["key"],label=s["label"],points=s["points"],detail=s["detail"]))
        db.add(BehaviouralFeature(merchant_id=merchant.id,transaction_count=f["transaction_count"],daily_count=f["daily_count"],avg_ticket=f["avg_ticket"],refund_rate=f["refund_rate"],failed_rate=f["failed_rate"],night_share=f["night_share"],customer_concentration=f["customer_concentration"]))
        db.add(AuditLog(actor="trace-engine",role="system",action="risk.assessed",resource_type="merchant",resource_id=merchant.id,reason=f"Assessment {aid}: {severity} review priority"));result["assessment_id"]=aid
    return result
