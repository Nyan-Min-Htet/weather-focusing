from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
import time

# Add project root and src directories to path for imports (works both local & Vercel)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'api'))

from weather_service import WeatherService # type: ignore
import cities # type: ignore

# api/index.py → ../src/templates/
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'templates')
print(f"Templates directory: {TEMPLATE_DIR}")
print(f"Exists: {os.path.exists(TEMPLATE_DIR)}")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
CORS(app)
app.config['JSON_AS_ASCII'] = False

# Python 3.13 - Disable debug for production
app.debug = False


@app.route('/')
def index():
    """Homepage with all cities"""
    regions = cities.get_cities_by_region()
    return render_template(
        'index.html',
        regions=regions,
        total_cities=len(cities.MYANMAR_CITIES),
        MYANMAR_CITIES=cities.MYANMAR_CITIES
    )


@app.route('/api/cities')
def api_cities():
    """JSON API: all cities"""
    return jsonify({
        "total": len(cities.MYANMAR_CITIES),
        "cities": cities.MYANMAR_CITIES
    })


@app.route('/api/weather')
def api_weather():
    """JSON API: weather for specific city"""
    city_name = request.args.get('city', 'Yangon')
    city_info = cities.find_city(city_name)

    if not city_info:
        return jsonify({"error": "မြို့ မတွေ့ပါ။"}), 404

    try:
        weather_data = WeatherService.get_weather(
            city_info["lat"],
            city_info["lon"]
        )
        result = WeatherService.format_response(city_info, weather_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/city/<city_name>')
def city_page(city_name):
    """Dynamic city page"""
    city_info = cities.find_city(city_name)

    if not city_info:
        return "မြို့ မတွေ့ပါ", 404

    try:
        weather_data = WeatherService.get_weather(
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
def api_all_weather():
    """All cities weather"""
    now = time.time()
    if WeatherService._all_weather_cache["data"] is not None and now < WeatherService._all_weather_cache["expires"]:
        return jsonify({"cities": WeatherService._all_weather_cache["data"]})

    def fetch_city(city):
        try:
            weather_data = WeatherService.get_weather(city["lat"], city["lon"])
            weather = WeatherService.format_response(city, weather_data)
            return {
                "city": city["name"],
                "city_mm": city["name_mm"],
                "region": city["region"],
                "temperature": weather["current"]["temperature"],
                "description_mm": weather["current"]["description_mm"],
                "description_en": weather["current"]["description_en"],
                "icon": weather["current"]["icon"],
                "humidity": weather["current"]["humidity"]
            }
        except Exception:
            return None

    try:
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(fetch_city, city) for city in cities.MYANMAR_CITIES]
            all_weather = []
            for future in as_completed(futures, timeout=25):
                result = future.result()
                if result is not None:
                    all_weather.append(result)

        WeatherService._all_weather_cache["data"] = all_weather
        WeatherService._all_weather_cache["expires"] = now + WeatherService.CACHE_EXPIRY
        return jsonify({"cities": all_weather})
    except Exception as e:
        all_weather = []
        for future in futures:
            if future.done() and future.exception() is None:
                result = future.result()
                if result is not None:
                    all_weather.append(result)
        if all_weather:
            WeatherService._all_weather_cache["data"] = all_weather
            WeatherService._all_weather_cache["expires"] = now + WeatherService.CACHE_EXPIRY
            return jsonify({"cities": all_weather})
        return jsonify({"error": str(e)}), 500


# ============================================
# ✨ NEW: Vercel Handler (for serverless)
# ============================================
# Vercel Python runtime uses this
def handler(request, context=None):
    def start_response(status, headers, exc_info=None):
        def write(body):
            return None
        return write

    return app(request.environ, start_response)


# For local development
if __name__ == '__main__':
    import socket
    
    # Try different ports if 5000 fails
    ports_to_try = [8000, 8080, 5050, 8888, 3000]
    
    for port in ports_to_try:
        try:
            # Test if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
            
            # Port is available, use it
            print("\n" + "="*50)
            print("🇲🇲 Myanmar Weather App Starting...")
            print("="*50)
            print(f"📁 Templates: {TEMPLATE_DIR}")
            print(f"📁 Cities: {len(cities.MYANMAR_CITIES)}")
            print(f"🌐 Open: http://localhost:{port}")
            print("="*50 + "\n")
            
            app.run(
                host='127.0.0.1',
                port=port,
                debug=True,
                use_reloader=False
            )
            break
            
        except OSError:
            print(f"⚠️ Port {port} not available, trying next...")
            continue
    else:
        print("❌ No available ports found")
        sys.exit(1)
