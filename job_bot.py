import os
import requests
from datetime import datetime, timedelta

# --- KONFIGURATION ---
# Discord Webhook URL (Denna sparar du säkert sen)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# Dina platser (Arbetsförmedlingens ID-koder för kommuner/län eller fritext)
# Stockholm län (01), Umeå kommun (2480)
LOCATIONS = ["01", "2480"] 

# Dina sökord för ekonomi-praktik
KEYWORDS = ["praktik", "internship", "intern", "trainee", "thesis", "examensarbete"]
ECONOMY_TERMS = ["ekonomi", "finans", "finance", "controller", "redovisning", "revision", "accounting"]

def fetch_jobs():
    # Vi söker efter annonser publicerade de senaste 24 timmarna
    url = "https://jobsearch.api.jobtechdev.se/search"
    
    # Vi gör en bred sökning på "ekonomi" först för att inte missa något
    headers = {"accept": "application/json"}
    params = {
        "q": "ekonomi",
        "limit": 100,
        "published-after": (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("hits", [])
    return []

def is_relevant(job):
    title = job.get("headline", "").lower()
    description = job.get("description", {}).get("text", "").lower()
    
    # Kolla Geografi: Stockholm, Umeå eller Distans
    workplace = job.get("workplace_address", {})
    municipality_code = workplace.get("municipality_code", "")
    region_code = workplace.get("region_code", "")
    remote = "distans" in description or job.get("remote_work", False)
    
    correct_location = (region_code == "01") or (municipality_code == "2480") or remote
    if not correct_location:
        return False
        
    # Kolla Sökordsmatchning för PRAKTIK
    has_praktik_keyword = any(word in title or word in description for word in KEYWORDS)
    
    # Kolla Sökordsmatchning för EKONOMI (så det inte är praktik för systemutvecklare)
    has_economy_keyword = any(word in title or word in description for word in ECONOMY_TERMS)
    
    return has_praktik_keyword and has_economy_keyword

def send_to_discord(job):
    title = job.get("headline")
    employer = job.get("employer", {}).get("name", "Okänd arbetsgivare")
    url = job.get("webpage_url")
    location = job.get("workplace_address", {}).get("municipality", "Distans/Oklart")
    
    message = {
        "content": f"💼 **Ny ekonomi-praktik hittad!**\n"
                   f"**Roll:** {title}\n"
                   f"**Företag:** {employer}\n"
                   f"**Plats:** {location}\n"
                   f"🔗 [Ansök här]({url})"
    }
    
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json=message)
    else:
        print(f"Hittade jobb (Ingen webhook konfigurerad): {title} hos {employer}")

# Huvudprogram
if __name__ == "__main__":
    all_jobs = fetch_jobs()
    for job in all_jobs:
        if is_relevant(job):
            send_to_discord(job)
