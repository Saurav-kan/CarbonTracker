import json
from backend.app import app


def test_assess_cart_basic():
    client = app.test_client()
    cart = [
        {'name':'Brazilian Soy', 'quantity':2},
        {'name':'Wheat flour', 'quantity':5}
    ]
    rv = client.post('/v1/assess_cart', data=json.dumps({'cart':cart}), content_type='application/json')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'summary' in data
    assert data['summary']['total_emissions_kg'] > 0
    assert data['highest_risk_item'] is not None
