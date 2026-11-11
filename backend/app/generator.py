from __future__ import annotations
import random,uuid,math
from datetime import datetime,timedelta,timezone
from sqlalchemy import delete
from sqlalchemy.orm import Session
from .models import Merchant,MerchantProfile,Transaction,MerchantEvent,EntityNode,EntityEdge,RiskSignal,RiskAssessment,Investigation,Intervention,AuditLog,BehaviouralFeature

CATEGORIES=["bakery","restaurant","grocery","electronics","clothing"]
SCENARIOS={"normal":{"label":"Normal operations","description":"Stable merchant-specific operating pattern."},"festival":{"label":"Festival sales increase","description":"Seasonal demand increase with stable refund and ticket patterns."},"expansion":{"label":"Legitimate online expansion","description":"New digital channel and higher reach after a declared business change."},"unexplained_spike":{"label":"Unexplained transaction increase","description":"Abrupt volume and ticket-size change without declared context."},"shared_device":{"label":"Suspicious shared-device network","description":"Several unrelated merchants share a pseudonymous device fingerprint."},"refund_anomaly":{"label":"Abnormal refund behaviour","description":"Refund share rises materially above the merchant baseline."},"mixed_signals":{"label":"Mixed legitimate and suspicious signals","description":"Declared promotion overlaps with refund and relationship anomalies."}}
def _id(p):return f"{p}_{uuid.uuid4().hex[:12]}"
def _make_tx(mid,idx,cat,scenario,rng,now,days=90):
    rows=[];base={"bakery":280,"restaurant":520,"grocery":390,"electronics":4200,"clothing":1450}[cat]
    for day in range(days):
        date=now-timedelta(days=days-day);recent=day>=days-30;factor=1.
        if recent and scenario=="festival" and day>=days-10:factor=2.2
        if recent and scenario=="expansion":factor=1.75
        if recent and scenario=="unexplained_spike":factor=3.8
        if recent and scenario=="mixed_signals":factor=2.
        count=max(1,int(rng.gauss(4.5*factor,1.2)))
        for _ in range(count):
            amount=max(35,rng.lognormvariate(math.log(base),.38));hour=int(rng.gauss(12,3.4))%24;status="settled"
            if recent and scenario=="unexplained_spike":amount*=rng.choice([1.,1.2,2.8]);hour=rng.choice([1,2,3,22,23,12,14])
            if recent and scenario=="refund_anomaly" and rng.random()<.24:status="refunded"
            if recent and scenario=="mixed_signals" and rng.random()<.14:status="refunded"
            if recent and scenario=="unexplained_spike" and rng.random()<.13:status="failed"
            if rng.random()<.018:status="failed"
            shared=scenario in {"shared_device","mixed_signals"} and recent and rng.random()<.85
            device="device:shared-cluster-01" if shared else f"device:{idx:03d}:{rng.randrange(1,18):02d}"
            customer=f"customer:{idx:03d}:{rng.randrange(1,160):03d}";settlement=f"settlement:{idx:03d}"
            channel="online" if recent and scenario=="expansion" and rng.random()<.72 else rng.choice(["upi","card","wallet"])
            stamp=date.replace(hour=hour,minute=rng.randrange(60),second=rng.randrange(60),tzinfo=timezone.utc)
            rows.append(Transaction(id=_id("tx"),merchant_id=mid,amount=round(amount,2),status=status,channel=channel,customer_token=customer,device_token=device,settlement_token=settlement,occurred_at=stamp,synthetic=True))
    return rows
def seed_demo(db:Session,force:bool=False):
    existing=db.query(Merchant).count()
    if existing and not force:return {"seeded":False,"merchants":existing,"transactions":db.query(Transaction).count()}
    if force:
        for model in [RiskSignal,RiskAssessment,Intervention,Investigation,AuditLog,EntityEdge,EntityNode,MerchantEvent,Transaction,BehaviouralFeature,MerchantProfile,Merchant]:db.execute(delete(model))
        db.commit()
    rng=random.Random(42);now=datetime.now(timezone.utc);names=["Oven House","Copper Kettle","Green Basket","Circuit House","Thread & Loom","Market Street","Daily Crumb","Harvest Table","Fresh Cart","Pixel Point"]
    cycle=["normal"]*20+["festival"]*10+["expansion"]*10+["unexplained_spike"]*10+["shared_device"]*10+["refund_anomaly"]*10+["mixed_signals"]*10+["normal"]*20
    merchants=[]
    for i in range(100):
        cat=CATEGORIES[i%5];scenario=cycle[i]
        merchants.append(Merchant(id=f"m-{i+1:04d}",name=f"{names[i%10]} {i+1:03d}",category=cat,scenario_label=scenario,declared_description=f"Independent {cat} merchant selling {cat} products through local and digital channels.",onboarding_date=now-timedelta(days=180),status="active"))
    db.add_all(merchants);db.flush();db.add_all([MerchantProfile(merchant_id=m.id,baseline_days=60) for m in merchants]);db.flush();txs=[]
    for i,m in enumerate(merchants):
        scenario=m.scenario_label;txs.extend(_make_tx(m.id,i+1,m.category,scenario,rng,now))
        if scenario in {"festival","expansion","mixed_signals"}:
            kind="festival_promotion" if scenario!="expansion" else "online_expansion"
            db.add(MerchantEvent(id=_id("evt"),merchant_id=m.id,event_type=kind,description=SCENARIOS[scenario]["description"],verification_status="unverified",effective_at=now-timedelta(days=12)))
    db.add_all(txs);db.flush()
    db.add_all([EntityNode(id=m.id,entity_type="merchant",label=m.name,synthetic=True) for m in merchants])
    node=EntityNode(id="device:shared-cluster-01",entity_type="device",label="Shared device fingerprint · synthetic",synthetic=True);db.add(node);db.flush()
    for i in range(50,60):db.add(EntityEdge(source_id=f"m-{i+1:04d}",target_id=node.id,relation="shared_device",evidence_count=8))
    from .analytics import merchant_features
    for merchant in merchants:merchant_features(db,merchant)
    db.commit()
    return {"seeded":True,"merchants":100,"transactions":len(txs),"scenarios":SCENARIOS}
def run_scenario(db:Session,merchant_id:str,scenario:str):
    if scenario not in SCENARIOS:raise ValueError("Unknown scenario")
    merchant=db.get(Merchant,merchant_id)
    if not merchant:raise LookupError("Merchant not found")
    now=datetime.now(timezone.utc);idx=int(merchant_id.split("-")[-1]);db.execute(delete(Transaction).where(Transaction.merchant_id==merchant_id))
    rows=_make_tx(merchant.id,idx,merchant.category,scenario,random.Random(1000+idx+sum(map(ord,scenario))),now);db.add_all(rows)
    db.execute(delete(MerchantEvent).where(MerchantEvent.merchant_id==merchant_id));merchant.scenario_label=scenario
    if scenario in {"festival","expansion","mixed_signals"}:
        db.add(MerchantEvent(id=_id("evt"),merchant_id=merchant.id,event_type="festival_promotion" if scenario!="expansion" else "online_expansion",description=SCENARIOS[scenario]["description"],verification_status="unverified",effective_at=now-timedelta(days=10)))
    db.flush();db.info.pop("trace_portfolio_features",None);db.commit()
    return {"merchant_id":merchant_id,"scenario":scenario,"scenario_label":SCENARIOS[scenario]["label"],"transactions_replaced":len(rows),"data_mode":"SYNTHETIC"}
