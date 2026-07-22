import base64
import hashlib
import os
import urllib.parse
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import requests
import asyncio
from datetime import datetime
from database import init_db, insert_track
from fastapi import Request
from fastapi.templating import Jinja2Templates
import numpy as np
import requests
from engine import get_candidate_pool, score_and_select_best_candidate

# Şablonların bulunacağı klasörü belirtiyoruz
templates = Jinja2Templates(directory="templates")
init_db()
CURRENT_ACCESS_TOKEN = None

app = FastAPI()

CLIENT_ID = "63873874053f45699ee0925247246c57"
REDIRECT_URI = "http://127.0.0.1:8080/callback"

# Faz 1'de belirtilen gerekli scope'lar
SCOPES = [
    "user-read-recently-played", 
    "streaming", 
    "user-read-email", 
    "user-read-private", 
    "user-modify-playback-state", 
    "playlist-modify-public", 
    "playlist-modify-private"
]

# Geliştirme aşamasında verifier'ı bellekte tutmak için basit bir sözlük
# İlerleyen fazlarda bunu Redis veya veritabanına taşıyacağız.
session_store = {}

def generate_pkce_pair():
    raw_bytes = os.urandom(64)
    verifier = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("utf-8")).digest()
    ).decode("utf-8").rstrip("=")
    return verifier, challenge

@app.get("/login")
def login(request: Request):
    # 43-128 karakterli rastgele verifier ve challenge üretimi
    verifier, challenge = generate_pkce_pair()
    
    # Doğrulama aşamasında kullanmak üzere verifier'ı kaydediyoruz
    session_store["local_user"] = verifier
    
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "scope": " ".join(SCOPES),
    }
    
    # Kullanıcıyı Spotify yetkilendirme sayfasına yönlendiriyoruz
    auth_url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(code: str, request: Request):
    global CURRENT_ACCESS_TOKEN
    # İlk adımda sakladığımız verifier'ı geri çağırıyoruz
    verifier = session_store.get("local_user")
    if not verifier:
        return {"error": "Verifier bulunamadı. Lütfen tekrar giriş yapın."}
        
    token_url = "https://accounts.spotify.com/api/token"
    
    # Dönen code ile token takası yapıyoruz
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(token_url, data=payload, headers=headers)
    token_data = response.json()
    if "access_token" in token_data:
        CURRENT_ACCESS_TOKEN = token_data["access_token"]
        print(f"Token güncellendi, arka plan görevi API'ye erişebilir!")
        return RedirectResponse(url="/")
    
    return {"error": "Token alınamadı", "details": token_data}
    
    # Token başarıyla alındığında ekranda gösterecek
@app.get("/refresh")
def refresh_access_token(refresh_token: str):
    token_url = "https://accounts.spotify.com/api/token"
    
    # Refresh token için gerekli payload
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(token_url, data=payload, headers=headers)
    new_token_data = response.json()
    
    # Dönen yanıt yeni bir access_token ve yeni bir expires_in süresi içerecek
    return new_token_data

def is_valid_track(played_at_str, duration_ms):
    """
    Belgedeki veri temizleme kurallarını uygular.
    """
    # 30 saniyeden (30000 ms) kısa dinlemeleri (muhtemel atlamalar) filtrele
    if duration_ms < 30000:
        return False
        
    # Zaman damgasını datetime objesine çevir (Örn: "2023-10-15T14:30:24.123Z")
    try:
        played_at_dt = datetime.strptime(played_at_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        
        # Saniyesi 4, 24 veya 54 ile biten kayıtları filtrele
        second = played_at_dt.second
        if second in [4, 24, 54]:
            return False
            
    except ValueError:
        pass
        
    return True

async def fetch_recently_played_loop():
    """
    Her 25 dakikada bir çalışarak 50 şarkı duvarını aşmak için veri biriktirir.
    """
    while True:
        if CURRENT_ACCESS_TOKEN:
            url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"
            headers = {"Authorization": f"Bearer {CURRENT_ACCESS_TOKEN}"}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                valid_count = 0
                for item in items:
                    track = item.get("track", {})
                    played_at = item.get("played_at")
                    duration_ms = track.get("duration_ms", 0)
                    
                    # Veri temizleme filtrelerinden geçiyorsa DB'ye ekle
                    if is_valid_track(played_at, duration_ms):
                        insert_track(
                            track_id=track.get("id"),
                            track_name=track.get("name"),
                            artist_name=track.get("artists", [{}])[0].get("name"),
                            played_at=played_at,
                            duration_ms=duration_ms
                        )
                        valid_count += 1
                print(f"[{datetime.now()}] {valid_count} yeni/geçerli şarkı veritabanına eklendi.")
            else:
                print(f"API Hatası: {response.status_code}")
                
        # 25 dakika (1500 saniye) bekle ve tekrar çalıştır
        await asyncio.sleep(1500)

# FastAPI uygulaması ayağa kalkarken döngüyü arka planda başlat
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_recently_played_loop())

# Kullanıcı ana adrese (http://127.0.0.1:8080/) girdiğinde radyoyu açacak uç nokta
@app.get("/")
def render_radio_player(request: Request):
    if not CURRENT_ACCESS_TOKEN:
        return {"mesaj": "Lütfen önce /login adresine giderek giriş yapın."}
        
    # Parametreleri açıkça yazarak versiyon hatasını (unhashable type: 'dict') aşıyoruz
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={"access_token": CURRENT_ACCESS_TOKEN}
    )

@app.get("/feed-queue")
def feed_queue():
    if not CURRENT_ACCESS_TOKEN:
        return {"status": "error", "message": "Token yok"}
        
    # 1. Zevk Analizi (Faz 2 & 3'ün simülasyonu)
    # Gerçek senaryoda burada analyzer.get_core_set() çalışır.
    # Sistemi test etmek için şimdilik önceki başarılı testimizdeki değerleri kullanıyoruz:
    hedef_tur = "turkish rock" 
    ornek_cekirdek_vektor = np.array([[0.8, 1.0]]) 
    
    # 2. Aday Havuzunu Çek
    adaylar = get_candidate_pool(target_genre=hedef_tur, access_token=CURRENT_ACCESS_TOKEN, limit=10)
    
    if not adaylar:
        return {"status": "error", "message": "Aday bulunamadı"}
        
    # 3. En İyi Şarkıyı Seç
    en_iyi_aday = score_and_select_best_candidate(
        core_set_vector=ornek_cekirdek_vektor,
        candidates=adaylar,
        target_genre=hedef_tur
    )
    
    if en_iyi_aday:
        track_uri = f"spotify:track:{en_iyi_aday['id']}"
        
        # 4. Spotify Kuyruğuna Ekle (Faz 5)
        queue_url = f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}"
        headers = {"Authorization": f"Bearer {CURRENT_ACCESS_TOKEN}"}
        
        # Şarkıyı kuyruğa basıyoruz
        response = requests.post(queue_url, headers=headers)
        
        # Spotify başarılı eklemede 204 No Content döner
        if response.status_code == 204:
            return {"status": "success", "added_track": en_iyi_aday["name"], "artist": en_iyi_aday["artist_name"]}
        else:
            return {"status": "error", "message": "Kuyruğa eklenemedi", "details": response.json()}
            
    return {"status": "error", "message": "Motor şarkı seçemedi"}