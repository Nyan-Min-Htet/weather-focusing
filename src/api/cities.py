MYANMAR_CITIES = [
    {"name": "Yangon", "name_mm": "ရန်ကုန်", "region": "ရန်ကုန်တိုင်း", "lat": 16.8409, "lon": 96.1735},
    {"name": "Mandalay", "name_mm": "မန္တလေး", "region": "မန္တလေးတိုင်း", "lat": 21.9588, "lon": 96.0891},
    {"name": "Naypyidaw", "name_mm": "နေပြည်တော်", "region": "ပြည်ထောင်စုနယ်မြေ", "lat": 19.7633, "lon": 96.0785},
    {"name": "Mawlamyine", "name_mm": "မော်လမြိုင်", "region": "မွန်ပြည်နယ်", "lat": 16.4905, "lon": 97.6283},
    {"name": "Bago", "name_mm": "ပဲခူး", "region": "ပဲခူးတိုင်း", "lat": 17.3220, "lon": 96.4663},
    {"name": "Pathein", "name_mm": "ပုသိမ်", "region": "ဧရာဝတီတိုင်း", "lat": 16.7792, "lon": 94.7321},
    {"name": "Monywa", "name_mm": "မုံရွာ", "region": "စစ်ကိုင်းတိုင်း", "lat": 22.1192, "lon": 95.1539},
    {"name": "Sittwe", "name_mm": "စစ်တွေ", "region": "ရခိုင်ပြည်နယ်", "lat": 20.1466, "lon": 92.8845},
    {"name": "Taunggyi", "name_mm": "တောင်ကြီး", "region": "ရှမ်းပြည်နယ်", "lat": 20.7803, "lon": 97.0351},
    {"name": "Myitkyina", "name_mm": "မြစ်ကြီးနား", "region": "ကချင်ပြည်နယ်", "lat": 25.3833, "lon": 97.4000},
    {"name": "Dawei", "name_mm": "ထားဝယ်", "region": "တနင်္သာရီတိုင်း", "lat": 14.0827, "lon": 98.1945},
    {"name": "Pyay", "name_mm": "ပြည်", "region": "ပဲခူးတိုင်း", "lat": 18.8402, "lon": 95.2600},
    {"name": "Lashio", "name_mm": "လားရှိုး", "region": "ရှမ်းပြည်နယ်", "lat": 22.9432, "lon": 97.7478},
    {"name": "Hpa-an", "name_mm": "ဘားအံ", "region": "ကရင်ပြည်နယ်", "lat": 16.8892, "lon": 97.6333},
    {"name": "Magway", "name_mm": "မကွေး", "region": "မကွေးတိုင်း", "lat": 20.1500, "lon": 94.9167},
]

def find_city(name):
    """Find city by English or Myanmar name"""
    if not name:
        return None
    name_lower = name.lower().strip()
    for city in MYANMAR_CITIES:
        if city["name"].lower() == name_lower or city["name_mm"] == name.strip():
            return city
    return None

def get_cities_by_region():
    """Group cities by region for organized display"""
    regions = {}
    for city in MYANMAR_CITIES:
        region = city["region"]
        if region not in regions:
            regions[region] = []
        regions[region].append(city)
    return regions
