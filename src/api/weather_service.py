import httpx
import time
from datetime import date, datetime

class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    _all_weather_cache = {"data": None, "expires": 0}
    CACHE_EXPIRY = 300  # seconds
    _weather_cache = {}
    _all_weather_cache = {
        "expires": 0,
        "data": None
    }

    WEATHER_CODES = {
        0: ("ကြည်လင်", "Clear sky", "☀️"),
        1: ("အများအားဖြင့် ကြည်လင်", "Mainly clear", "🌤️"),
        2: ("တိမ်အနည်းငယ်", "Partly cloudy", "⛅"),
        3: ("တိမ်ထူ", "Overcast", "☁️"),
        45: ("မြူထူ", "Foggy", "🌫️"),
        48: ("နှင်းဖြစ်တဲ့ မြူ", "Rime fog", "🌫️"),
        51: ("ဖုန်းပြေး မိုး", "Light drizzle", "🌦️"),
        53: ("ဖုန်းပြေး မိုး အနည်းငယ်", "Moderate drizzle", "🌦️"),
        55: ("ဖုန်းပြေး မိုး ပြင်း", "Dense drizzle", "🌧️"),
        61: ("မိုးအနည်းငယ်", "Slight rain", "🌧️"),
        63: ("မိုးအနည်းငယ် ပြင်း", "Moderate rain", "🌧️"),
        65: ("မိုးပြင်း", "Heavy rain", "⛈️"),
        71: ("နှင်းပြောင်း အနည်းငယ်", "Slight snow", "🌨️"),
        73: ("နှင်းပြောင်း", "Moderate snow", "🌨️"),
        75: ("နှင်းပြောင်း ပြင်း", "Heavy snow", "❄️"),
        80: ("မိုးရွာပြောင်း အနည်းငယ်", "Slight rain showers", "🌦️"),
        81: ("မိုးရွာပြောင်း", "Moderate rain showers", "🌧️"),
        82: ("မိုးရွာပြောင်း ပြင်း", "Violent rain showers", "⛈️"),
        95: ("မိုးကြိုးပစ်", "Thunderstorm", "⛈️"),
        96: ("မိုးကြိုးပစ် + မိုးသီး", "Thunderstorm with hail", "⛈️"),
        99: ("မိုးကြိုးပစ် ပြင်း + မိုးသီး", "Heavy thunderstorm", "⛈️"),
    }
    
    @staticmethod
    def get_weather(lat, lon):
        """Get weather from Open-Meteo"""
        cache_key = f"{lat},{lon}"
        now = time.time()
        cached = WeatherService._weather_cache.get(cache_key)
        if cached and now < cached[0]:
            return cached[1]

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset",
            "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "timezone": "Asia/Yangon",
            "forecast_days": 7
        }

        timeout = httpx.Timeout(10.0, connect=5.0, read=10.0)
        with httpx.Client(timeout=timeout) as client:
            response = client.get(WeatherService.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            WeatherService._weather_cache[cache_key] = (now + WeatherService.CACHE_EXPIRY, data)
            return data
    
    @staticmethod
    def get_weather_info(code):
        return WeatherService.WEATHER_CODES.get(code, ("မသိရှိပါ", "Unknown", "❓"))
    
    @staticmethod
    def format_response(city_info, weather_data):
        current = weather_data.get("current", {})
        daily = weather_data.get("daily", {})
        hourly = weather_data.get("hourly", {})
        
        weather_code = current.get("weather_code", 0)
        desc_mm, desc_en, icon = WeatherService.get_weather_info(weather_code)
        
        result = {
            "city": city_info["name"],
            "city_mm": city_info["name_mm"],
            "region": city_info["region"],
            "current": {
                "temperature": round(current.get("temperature_2m", 0), 1),
                "feels_like": round(current.get("apparent_temperature", 0), 1),
                "humidity": current.get("relative_humidity_2m", 0),
                "wind_speed": round(current.get("wind_speed_10m", 0), 1),
                "wind_direction": current.get("wind_direction_10m", 0),
                "precipitation": current.get("precipitation", 0),
                "is_day": current.get("is_day", 1),
                "description_mm": desc_mm,
                "description_en": desc_en,
                "icon": icon,
                "updated_at": current.get("time", "")
            },
            "forecast": [],
            "wind_hourly": []
        }
        
        if daily and "time" in daily:
            times = daily["time"]
            for i in range(len(times)):
                fc_code = daily.get("weather_code", [0] * len(times))[i]
                fc_desc_mm, fc_desc_en, fc_icon = WeatherService.get_weather_info(fc_code)
                
                result["forecast"].append({
                    "date": times[i],
                    "temp_max": round(daily.get("temperature_2m_max", [0] * len(times))[i], 1),
                    "temp_min": round(daily.get("temperature_2m_min", [0] * len(times))[i], 1),
                    "precipitation": round(daily.get("precipitation_sum", [0] * len(times))[i], 1),
                    "sunrise": daily.get("sunrise", [""] * len(times))[i],
                    "sunset": daily.get("sunset", [""] * len(times))[i],
                    "description_mm": fc_desc_mm,
                    "description_en": fc_desc_en,
                    "icon": fc_icon
                })
        if hourly and "time" in hourly:
            times = hourly["time"]
            wind_speeds = hourly.get("wind_speed_10m", [])
            wind_dirs = hourly.get("wind_direction_10m", [])
            wind_gusts = hourly.get("wind_gusts_10m", [])
        
            # Only take next 24 hours
            for i in range(min(24, len(times))):
                speed = wind_speeds[i] if i < len(wind_speeds) else 0
                direction = wind_dirs[i] if i < len(wind_dirs) else 0
                gusts = wind_gusts[i] if i < len(wind_gusts) else 0
            
                result["wind_hourly"].append({
                    "time": times[i],
                    "speed": round(speed, 1),
                    "direction": int(direction),
                    "gusts": round(gusts, 1),
                    "direction_text": WeatherService.get_wind_direction(direction),
                    "direction_arrow": WeatherService.get_wind_arrow(direction),
                    "category": WeatherService.get_wind_category(speed)
                })
            # Calculate wind summary
            if result["wind_hourly"]:
                speeds = [h["speed"] for h in result["wind_hourly"]]
                result["wind_summary"] = {
                    "max_speed": max(speeds),
                    "min_speed": min(speeds),
                    "avg_speed": round(sum(speeds) / len(speeds), 1),
                    "max_gust": max(h["gusts"] for h in result["wind_hourly"]),
                    "dominant_direction": WeatherService.get_dominant_direction(result["wind_hourly"])
                }
            else:
                result["wind_summary"] = {}    
        return result

    @staticmethod
    def get_wind_direction(degrees):
            """Convert wind degrees to compass direction text"""
            directions = [
                "မြောက်", "အရှေ့မြောက်", "အရှေ့", "အရှေ့တောင်",
                "တောင်", "အနောက်တောင်", "အနောက်", "အနောက်မြောက်"
            ]
            directions_en = [
                "N", "NE", "E", "SE", "S", "SW", "W", "NW"
            ]
            idx = int((degrees + 22.5) / 45) % 8
            return f"{directions[idx]} ({directions_en[idx]})"

    @staticmethod
    def get_wind_arrow(degrees):
        """Convert wind degrees to arrow direction"""
        arrows = ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"]
        idx = int((degrees + 22.5) / 45) % 8
        return arrows[idx]

    @staticmethod
    def get_wind_category(speed):
        """Categorize wind speed"""
        if speed < 1:
            return "လေပြင်း", "Calm", "#94a3b8"  # slate-400
        elif speed < 6:
            return "လေအေး", "Light", "#86efac"  # green-300
        elif speed < 12:
            return "လေသင့်", "Moderate", "#fde047"  # yellow-300
        elif speed < 20:
            return "လေပြင်း", "Fresh", "#fb923c"  # orange-400
        elif speed < 29:
            return "လေပြင်းထန်", "Strong", "#ef4444"  # red-500
        else:
            return "မုန်တိုင်း", "Gale", "#a855f7"  # purple-500

    @staticmethod
    def get_dominant_direction(hourly_data):
        """Get most common wind direction"""
        from collections import Counter
        directions = [h["direction_text"].split(" ")[1] for h in hourly_data]
        if not directions:
            return "N/A"
        most_common = Counter(directions).most_common(1)[0][0]
        return most_common
    
    @staticmethod
    def get_moon_phase(date):
        """Simple moon phase calculation"""
        # Reference new moon: Jan 6, 2000
        reference = datetime(2000, 1, 6)
        days_since = (date - reference).days
        cycle = 29.53059  # Lunar cycle in days
        phase = (days_since % cycle) / cycle
        
        if phase < 0.03 or phase > 0.97:
            return "🌑", "လကွယ်", "New Moon"
        elif phase < 0.22:
            return "🌒", "လကွယ်လပြန်", "Waxing Crescent"
        elif phase < 0.28:
            return "🌓", "လပြန်တစ်ချိုး", "First Quarter"
        elif phase < 0.47:
            return "🌔", "လပြန်ဝင်ဆန်း", "Waxing Gibbous"
        elif phase < 0.53:
            return "🌕", "လပြည့်", "Full Moon"
        elif phase < 0.72:
            return "🌖", "လဆုတ်ဝင်ဆန်း", "Waning Gibbous"
        elif phase < 0.78:
            return "🌗", "လဆုတ်တစ်ချိုး", "Last Quarter"
        else:
            return "🌘", "လဆုတ်လကွယ်", "Waning Crescent"
