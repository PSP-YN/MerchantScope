from fastapi.testclient import TestClient
from app.main import app
from app.engine import MERCHANTS, score_merchant

client = TestClient(app)

def test_health_and_synthetic_notice():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['data_mode'] == 'synthetic'

def test_dashboard_has_expected_scenarios_and_risk_order():
    data = client.get('/api/dashboard').json()
    assert data['data_mode'] == 'SYNTHETIC DEMO DATA'
    assert len(data['merchants']) == 5
    by_id = {m['id']: m for m in data['merchants']}
    assert by_id['m-1003']['risk_score'] > by_id['m-1001']['risk_score']
    assert by_id['m-1003']['risk_level'] == 'high'
    assert by_id['m-1002']['risk_level'] == 'low'

def test_merchant_not_found():
    assert client.get('/api/merchants/not-real').status_code == 404

def test_case_status_validation_and_update():
    cases = client.get('/api/cases').json()
    assert cases
    cid = cases[0]['id']
    updated = client.patch(f'/api/cases/{cid}', json={'status': 'investigating', 'note': 'Review linked fingerprints'})
    assert updated.status_code == 200
    assert updated.json()['status'] == 'investigating'
    assert updated.json()['notes'][-1] == 'Review linked fingerprints'

def test_heuristic_explanations_are_bounded():
    for merchant in MERCHANTS:
        result = score_merchant(merchant)
        assert 0 <= result['risk_score'] <= 100
        assert result['risk_level'] in {'low', 'medium', 'high'}
