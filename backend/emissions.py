import os
import requests
from typing import Dict, List, Optional

# --- Cache for API results ---
api_cache = {}

class EmissionsService:
    """
    Provides emission factors (kg CO2e per unit) and risk multipliers.
    New behavior:
    - Fetches data from Open Food Facts API using UPC barcode.
    - Parses ingredients and calculates emissions based on an expanded database.
    - Caches API results to minimize external calls.
    - Falls back to name-based estimation if API call fails or no ingredients are found.
    """

    STATIC_FACTORS: Dict[str, float] = {
        # Animal-based
        'beef': 50.0,
        'lamb': 39.2,
        'cheese': 13.5,
        'butter': 10.77,
        'pork': 12.1,
        'chicken': 6.9,
        'fish': 5.0,
        'eggs': 4.8,
        'milk': 1.9,

        # Plant-based
        'rice': 3.7,
        'vegetable oil': 3.66,
        'potatoes': 2.9,
        'nuts': 2.3,
        'beans': 2.0,
        'tofu': 2.0,
        'vegetables': 2.0,
        'pasta': 1.54,
        'fruit': 1.1,
        'lentils': 0.9,
        'wheat': 0.8,
        'soy': 0.7,
        'corn': 0.6,
        'sugar': 0.5,
        'oats': 0.4,
        'palm oil': 8.0, # Higher value due to deforestation risk

        'default': 1.0
    }

    def __init__(self):
        self.api_key = os.getenv('EXTERNAL_EMISSIONS_API_KEY') # Not used for Open Food Facts

    def _get_from_openfoodfacts(self, upc: str) -> Optional[Dict]:
        """Fetches product data from Open Food Facts API."""
        if upc in api_cache:
            return api_cache[upc]

        url = f"https://world.openfoodfacts.org/api/v0/product/{upc}.json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 1:
                api_cache[upc] = data
                return data
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
        return None

    def _parse_ingredients(self, ingredients_text: str) -> List[str]:
        """Parses a string of ingredients into a list."""
        if not ingredients_text:
            return []
        # Basic parsing: lowercase, split by comma, remove extra chars
        return [
            ing.strip().lower().replace('_', '')
            for ing in ingredients_text.split(',')
        ]

    def get_emission_factor(self, product_name: str, upc: Optional[str] = None, ingredients_str: Optional[str] = None) -> float:
        """
        Calculates the emission factor for a product.
        Prioritizes UPC-based ingredient analysis, then falls back to name-based.
        """
        # 1. Try UPC and Open Food Facts
        if upc:
            product_data = self._get_from_openfoodfacts(upc)
            if product_data and "product" in product_data and "ingredients_text" in product_data["product"]:
                ingredients = self._parse_ingredients(product_data["product"]["ingredients_text"])
                if ingredients:
                    total_emissions = 0
                    found_ingredients = 0
                    for ing in ingredients:
                        for factor_name, factor_value in self.STATIC_FACTORS.items():
                            if factor_name in ing:
                                total_emissions += factor_value
                                found_ingredients += 1
                                break
                    # Return average emission factor of found ingredients
                    if found_ingredients > 0:
                        return total_emissions / found_ingredients

        # 2. Fallback to ingredients string if provided
        if ingredients_str:
            ingredients = self._parse_ingredients(ingredients_str)
            if ingredients:
                total_emissions = 0
                found_ingredients = 0
                for ing in ingredients:
                    for factor_name, factor_value in self.STATIC_FACTORS.items():
                        if factor_name in ing:
                            total_emissions += factor_value
                            found_ingredients += 1
                            break
                if found_ingredients > 0:
                    return total_emissions / found_ingredients

        # 3. Fallback to naive name matching (original method)
        if not product_name:
            return self.STATIC_FACTORS['default']
        prod = product_name.lower()
        for k in self.STATIC_FACTORS:
            if k in prod:
                return self.STATIC_FACTORS[k]
        return self.STATIC_FACTORS['default']


    def get_risk_multiplier(self, product_name: str) -> float:
        # This logic can also be enhanced with API data in the future
        prod = (product_name or '').lower()
        if 'soy' in prod and 'brazil' in prod:
            return 1.10
        if 'soy' in prod:
            return 1.05
        if 'palm' in prod or 'palm oil' in prod:
            return 1.25
        if 'beef' in prod:
            return 1.15
        return 1.0