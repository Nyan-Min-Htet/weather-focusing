from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from weather_service import WeatherService
import cities

# Template folder (relative to src/api/)
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
CORS(app)

# Python 3.13 - Disable debug for production
app.debug = False


@app.route('/')
def index():
    """Homepage with all cities"""
    regions = cities.get_cities_by_region()
    return render_template('index.html',
                         regions=regions,
                         total_cities=len(cities.MYANMAR_CITIES))


@app.route('/api/cities')
def api_cities():
    """JSON API: all cities"""
    return jsonify({
        "total": len(cities.MYANMAR_CITIES),
        "cities": cities.MYANMAR_CITIES
    })


@app.route('/api/weather')
async def api_weather():
    """JSON API: weather for specific city"""
    city_name = request.args.get('city', 'Yangon')
    city_info = cities.find_city(city_name)

    if not city_info:
        return jsonify({"error": "မြို့ မတွေ့ပါ။"}), 404

    try:
        weather_data = await WeatherService.get_weather(
            city_info["lat"],
            city_info["lon"]
        )
        result = WeatherService.format_response(city_info, weather_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/city/<city_name>')
async def city_page(city_name):
    """Dynamic city page"""
    city_info = cities.find_city(city_name)

    if not city_info:
        return "မြို့ မတွေ့ပါ", 404

    try:
        weather_data = await WeatherService.get_weather(
            city_info["lat"],
            city_info["lon"]
        )
        weather = WeatherService.format_response(city_info, weather_data)
        all_cities = cities.MYANMAR_CITIES

        return render_template('city.html',
                             city=city_info,
                             weather=weather,
                             all_cities=all_cities)
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/api/all-weather')
async def api_all_weather():
    """All cities weather (concurrent)"""
    tasks = [
        WeatherService.get_weather(city["lat"], city["lon"])
        for city in cities.MYANMAR_CITIES
    ]
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_weather = []
        for i, city in enumerate(cities.MYANMAR_CITIES):
            if isinstance(results[i], Exception):
                continue
            weather = WeatherService.format_response(city, results[i])
            all_weather.append({
                "city": city["name"],
                "city_mm": city["name_mm"],
                "region": city["region"],
                "temperature": weather["current"]["temperature"],
                "description_mm": weather["current"]["description_mm"],
                "description_en": weather["current"]["description_en"],
                "icon": weather["current"]["icon"],
                "humidity": weather["current"]["humidity"]
            })

        return jsonify({"cities": all_weather})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# For local development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
