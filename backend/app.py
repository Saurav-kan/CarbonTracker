from flask import Flask, request, jsonify
from flask_cors import CORS
from .emissions import EmissionsService

app = Flask(__name__)
CORS(app)

es = EmissionsService()

SOCIAL_COST_PER_TON = 50.0  # USD per ton CO2e — demo value


@app.route('/v1/assess_cart', methods=['POST'])
def assess_cart():
    payload = request.get_json() or {}
    cart = payload.get('cart') or []

    if not isinstance(cart, list):
        return jsonify({'error':'cart must be a list'}), 400

    items_out = []
    total_emissions_kg = 0.0

    for item in cart:
        name = item.get('name','').lower()
        qty = max(1, int(item.get('quantity',1)))
        upc = item.get('upc')
        ingredients_str = item.get('ingredients')

        base_factor_kg = es.get_emission_factor(name, upc=upc, ingredients_str=ingredients_str)  # kg CO2e per unit
        risk_adj = es.get_risk_multiplier(name)

        item_emissions = base_factor_kg * risk_adj * qty
        total_emissions_kg += item_emissions

        items_out.append({
            'name': item.get('name'),
            'quantity': qty,
            'base_factor_kg': base_factor_kg,
            'risk_multiplier': risk_adj,
            'emissions_kg': item_emissions
        })

    total_emissions_tons = total_emissions_kg / 1000.0
    social_cost_usd = total_emissions_tons * SOCIAL_COST_PER_TON

    # Determine PASS/FAIL for demo: FAIL if any item has multiplier >1.1
    highest_item = max(items_out, key=lambda x: x['emissions_kg']) if items_out else None
    fail = any(it['risk_multiplier'] > 1.1 for it in items_out)

    result = {
        'summary':{
            'total_emissions_kg': total_emissions_kg,
            'total_emissions_tons': total_emissions_tons,
            'social_cost_usd': round(social_cost_usd,2),
            'status': 'FAIL' if fail else 'PASS'
        },
        'highest_risk_item': highest_item,
        'items': items_out
    }

    return jsonify(result)


if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)