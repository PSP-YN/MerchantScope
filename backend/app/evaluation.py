from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Merchant
from .analytics import evaluate_merchant

POSITIVE={"unexplained_spike","shared_device","refund_anomaly","mixed_signals"}
def _metrics(y,p):
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
    return {"precision":round(float(precision_score(y,p,zero_division=0)),4),"recall":round(float(recall_score(y,p,zero_division=0)),4),"f1":round(float(f1_score(y,p,zero_division=0)),4),"false_positive_rate":round(float(fp/max(1,fp+tn)),4),"legitimate_merchant_false_positive_rate":round(float(fp/max(1,tn)),4),"true_positives":int(tp),"false_positives":int(fp),"false_negatives":int(fn),"true_negatives":int(tn)}
def evaluate_models(db:Session):
    merchants=db.scalars(select(Merchant).order_by(Merchant.id)).all();truth=[];static=[];trace=[]
    for m in merchants:
        label=int(getattr(m,"scenario_label","normal") in POSITIVE);r=evaluate_merchant(db,m,persist=False);f=r["features"]
        baseline=m.profile.baseline_daily_count if m.profile else 0
        static.append(int(f["sufficient_history"] and (f["daily_count"]>max(12,baseline*2.8) or f["refund_rate"]>.15 or f["night_share"]>.30)))
        trace.append(int(r["risk_score"]>=30));truth.append(label)
    categories={}
    for cat in sorted({m.category for m in merchants}):
        ix=[i for i,m in enumerate(merchants) if m.category==cat]
        categories[cat]={"merchant_count":len(ix),"trace_f1":round(float(f1_score([truth[i] for i in ix],[trace[i] for i in ix],zero_division=0)),4)}
    return {"data_mode":"SYNTHETIC LABELLED SCENARIO BENCHMARK","split":{"method":"First 60 days baseline, latest 30 days evaluation","leakage_controls":"Scenario labels are evaluation targets only and are not included in feature vectors."},"static_threshold":_metrics(truth,static),"trace_contextual":_metrics(truth,trace),"category_performance":categories,"detection_delay_days":"Not estimated; event-level adjudicated timestamps are not present.","limitations":["Synthetic scenario labels are not representative of real payment fraud prevalence.","Isolation Forest is unsupervised and not a calibrated probability.","Results are an engineering benchmark, not production performance."]}
