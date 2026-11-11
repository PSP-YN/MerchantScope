from fastapi.testclient import TestClient
import pytest
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_health_and_portfolio(client):
    r=client.get("/health");assert r.status_code==200 and r.json()["data_mode"]=="synthetic"
    d=client.get("/api/dashboard").json()
    assert d["metrics"]["merchants_monitored"]==100
    assert d["metrics"]["transactions_monitored"]>=30000
    assert len(d["merchants"])==100

def test_merchant_and_transaction_detail(client):
    r=client.get("/api/merchants/m-0001");assert r.status_code==200
    assert r.json()["assessment"]["confidence"]>=0
    tx=client.get("/api/merchants/m-0001/transactions?limit=10").json()
    assert len(tx["items"])==10 and all(x["synthetic"] for x in tx["items"])

def test_scenarios_execute_pipeline(client):
    scenarios=client.get("/api/scenarios").json()
    assert {"festival","expansion","unexplained_spike","shared_device","refund_anomaly","mixed_signals"}<=set(scenarios)
    for scenario in ["festival","expansion","unexplained_spike","shared_device","refund_anomaly","mixed_signals"]:
        r=client.post("/api/scenarios/run",json={"merchant_id":"m-0001","scenario":scenario})
        assert r.status_code==200 and r.json()["assessment"]["severity"] in {"low","medium","high"}
        if scenario in {"festival","expansion"}: assert r.json()["assessment"]["severity"]=="low"
        if scenario in {"unexplained_spike","shared_device","refund_anomaly","mixed_signals"}: assert r.json()["assessment"]["risk_score"]>=20

def test_investigation_verification_and_audit(client):
    assert client.post("/api/merchants/m-0001/assess").status_code==200
    case=client.post("/api/investigations?merchant_id=m-0001");assert case.status_code==200
    cid=case.json()["id"]
    update=client.patch(f"/api/investigations/{cid}",json={"status":"investigating","note":"Review the declared change","assigned_to":"analyst-1"})
    assert update.status_code==200 and update.json()["status"]=="investigating"
    v=client.post(f"/api/investigations/{cid}/verification",json={"reason":"Confirm the declared operating change","requested_document":"Business registration"})
    assert v.status_code==200
    refreshed=client.get("/api/investigations").json()
    saved=next(x for x in refreshed if x["id"]==cid)
    assert any("declared operating change" in n["note"] for n in saved["notes"])
    proposal=client.post(f"/api/investigations/{cid}/interventions",json={"action":"enhanced_monitoring","reason":"Maintain monitoring during manual verification"},headers={"X-Role":"admin"})
    assert proposal.status_code==200 and proposal.json()["approval_status"]=="pending"
    iid=proposal.json()["id"]
    approval=client.patch(f"/api/interventions/{iid}/approval",json={"approved":True,"reason":"Reviewer approved enhanced monitoring for this case"},headers={"X-Role":"admin"})
    assert approval.status_code==200 and approval.json()["approval_status"]=="approved"
    assert any(x["resource_id"]==cid for x in client.get("/api/audit").json())

def test_graph_and_evaluation(client):
    graph=client.get("/api/relationships?merchant_id=m-0051").json()
    assert graph["nodes"] and graph["edges"]
    evaluation=client.get("/api/evaluation").json()
    assert 0<=evaluation["trace_contextual"]["f1"]<=1
