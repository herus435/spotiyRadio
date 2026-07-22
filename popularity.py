import requests

# Spotify Top 50 - Global listesinin standart ID'si (Bölgesel liste ID'si de kullanılabilir)
TOP_50_PLAYLIST_ID = "37i9dQZEVXbMDoHDwVN2tF"

# Havuzu bellekte (veya ileride Redis/DB'de) tutacağımız set yapısı
MAINSTREAM_POOL = set()

def update_mainstream_pool(access_token: str):
    """
    Faz 4 - Spotify Top 50 listesini çekip Popüler Şarkılar Havuzunu günceller.
    (Bu fonksiyon 6 saatte bir çalışacak şekilde arka plan görevlerine eklenebilir)
    """
    global MAINSTREAM_POOL
    
    # Şubat 2026 kısıtlamalarına uygun yeni /items uç noktası
    url = f"https://api.spotify.com/v1/playlists/{TOP_50_PLAYLIST_ID}/items"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        items = response.json().get("items", [])
        new_pool = set()
        
        for item in items:
            track = item.get("track")
            if track and "id" in track:
                new_pool.add(track["id"])
                
        MAINSTREAM_POOL = new_pool
        print(f"Popüler Şarkılar Havuzu güncellendi: {len(MAINSTREAM_POOL)} popüler parça hazır.")
    else:
        print(f"Havuz güncellenemedi. API Hatası: {response.status_code}")

def apply_popularity_bonus(candidate: dict) -> dict:
    """
    Faz 3'ten gelen aday şarkıyı Mainstream Havuzu ile çapraz kontrole sokar.
    Eğer parça popülerse Nihai Radyo Skoru'na (RadioScore) ekstra ağırlık ekler.
    """
    # Popüler parçalara verilecek ekstra puan (Bonus Ağırlık)
    bonus_weight = 0.15 
    
    # Faz 3'te hesaplanan benzerlik skoru
    current_score = candidate.get("similarity_score", 0.0)
    
    if candidate["id"] in MAINSTREAM_POOL:
        candidate["similarity_score"] = current_score + bonus_weight
        print(f"⭐ Popülerlik Bonusu Eklendi: {candidate['name']} (Yeni Skor: {candidate['similarity_score']:.2f})")
        
    return candidate