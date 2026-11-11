from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix
from sqlalchemy import select,func
from sqlalchemy.orm import Session
import pandas as pd
from datetime import timedelta
from .models import Merchant,Transaction
from .analytics import evaluate_merchant,_aware

POSITIVE={"unexplained_spike","shared_device","refund_anomaly","mixed_signals"}
def _metrics(y,p):
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
    return {"precision":round(float(precision_score(y,p,zero_division=0)),4),"recall":round(float(recall_score(y,p,zero_division=0)),4),"f1":round(float(f1_score(y,p,zero_division=0)),4),"false_positive_rate":round(float(fp/max(1,fp+tn)),4),"legitimate_merchant_false_positive_rate":round(float(fp/max(1,tn)),4),"true_positives":int(tp),"false_positives":int(fp),"false_negatives":int(fn),"true_negatives":int(tn)}

def _scenario_delay(db:Session,merchant:Merchant,shared_devices:set[str]):
    rows=db.scalars(select(Transaction).where(Transaction.merchant_id==merchant.id).order_by(Transaction.occurred_at)).all()
    if len(rows)<40:return None
    frame=pd.DataFrame([{"amount":r.amount,"status":r.status,"device":r.device_token,"date":_aware(r.occurred_at).date(),"night":int(_aware(r.occurred_at).hour<7 or _aware(r.occurred_at).hour>=22)} for r in rows])
    cutoff=max(frame.date)-timedelta(days=30)
    base=frame[frame.date<cutoff];current=frame[frame.date>=cutoff]
    if base.empty or current.empty:return None
    baseline_count=float(base.groupby("date").size().mean());baseline_refund=float(base.status.eq("refunded").mean())
    baseline_night=float(base.night.mean());baseline_ticket=float(base.amount.mean())
    current=current.copy();current["refund"]=current.status.eq("refunded").astype(int)
    daily=current.groupby("date").agg(count=("amount","size"),refund_rate=("refund","mean"),night_share=("night","mean"),avg_ticket=("amount","mean")).sort_index()
    rolling=daily.rolling(3,min_periods=2).mean()
    triggers=(rolling["count"]>max(12,baseline_count*2.8))|(rolling["refund_rate"]>max(.15,baseline_refund+.10))|(rolling["night_share"]>baseline_night+.25)|(rolling["avg_ticket"]>baseline_ticket*2.5)
    dates=list(daily.index[triggers.fillna(False)])
    graph_rows=current[current.device.isin(shared_devices)]
    if not graph_rows.empty:dates.append(graph_rows.date.min())
    if not dates:return None
    onset=current.date.min()
    return max(0,(min(dates)-onset).days)

def evaluate_models(db:Session):
    merchants=db.scalars(select(Merchant).order_by(Merchant.id)).all();truth=[];static=[];trace=[];delay_values=[];eligible=0
    shared_devices=set(db.scalars(select(Transaction.device_token).group_by(Transaction.device_token).having(func.count(func.distinct(Transaction.merchant_id))>1)).all())
    for m in merchants:
        scenario=getattr(m,"scenario_label","normal");label=int(scenario in POSITIVE)
        r=evaluate_merchant(db,m,persist=False);f=r["features"];baseline=m.profile.baseline_daily_count if m.profile else 0
        static.append(int(f["sufficient_history"] and (f["daily_count"]>max(12,baseline*2.8) or f["refund_rate"]>.15 or f["night_share"]>.30)))
        trace.append(int(r["risk_score"]>=20));truth.append(label)
        if label:
            eligible+=1;delay=_scenario_delay(db,m,shared_devices)
            if delay is not None:delay_values.append(delay)
    categories={}
    for cat in sorted({m.category for m in merchants}):
        ix=[i for i,m in enumerate(merchants) if m.category==cat]
        categories[cat]={"merchant_count":len(ix),"trace_f1":round(float(f1_score([truth[i] for i in ix],[trace[i] for i in ix],zero_division=0)),4)}
    delay_report={"mean_days":round(sum(delay_values)/len(delay_values),2) if delay_values else None,"median_days":float(pd.Series(delay_values).median()) if delay_values else None,
        "detected_scenarios":len(delay_values),"eligible_scenarios":eligible,"detection_rate":round(len(delay_values)/max(1,eligible),4),
        "method":"Days from synthetic scenario onset to first 3-day rolling statistical or shared-entity graph trigger."}
    return {"data_mode":"SYNTHETIC LABELLED SCENARIO BENCHMARK","split":{"method":"First 60 days baseline, latest 30 days evaluation","leakage_controls":"Scenario labels are evaluation targets only and are not included in feature vectors."},
      "static_threshold":_metrics(truth,static),"trace_contextual":_metrics(truth,trace),"category_performance":categories,
      "detection_delay_days":delay_report,"limitations":["Synthetic scenario labels are not representative of real payment fraud prevalence.","Isolation Forest is unsupervised and not a calibrated probability.","Detection delay is measured on generated scenario onset, not real payment-provider incident timestamps.","Results are an engineering benchmark, not production performance."]}
