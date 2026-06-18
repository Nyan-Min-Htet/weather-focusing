import httpx
import asyncio
from datetime import datetime

class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
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
    async def get_weather(lat, lon):
        """Get weather from Open-Meteo - Python 3.13 compatible"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset",
            "timezone": "Asia/Yangon",
            "forecast_days": 7
        }
        
        # httpx 0.28+ uses AsyncClient context manager properly
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(WeatherService.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def get_weather_info(code):
        return WeatherService.WEATHER_CODES.get(code, ("မသိရှိပါ", "Unknown", "❓"))
    
    @staticmethod
    def format_response(city_info, weather_data):
        current = weather_data.get("current", {})
        daily = weather_data.get("daily", {})
        
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
            "forecast": []
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
        
        return result
