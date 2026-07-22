import math
import sqlite3
from datetime import datetime, timezone

DB_NAME = "radio_history.db"

def get_core_set(lambda_val=0.5, limit=5):
    """
    Zamansal bozunma formülünü uygulayarak en yüksek ağırlıklı N parçayı (Çekirdek Set) seçer.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Hesaplama maliyetini düşürmek için son 200 kaydı çekiyoruz
    cursor.execute('''
        SELECT track_id, track_name, artist_name, played_at 
        FROM play_history 
        ORDER BY played_at DESC LIMIT 200
    ''')
    records = cursor.fetchall()
    conn.close()

    now = datetime.now(timezone.utc)
    weighted_tracks = []

    for row in records:
        track_id, track_name, artist_name, played_at_str = row
        
        # Spotify'ın zaman damgasını (UTC) datetime objesine çeviriyoruz
        try:
            played_at_dt = datetime.strptime(played_at_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            played_at_dt = played_at_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        
        # Zaman farkını (Delta Tau) saat cinsinden hesaplıyoruz
        delta_tau = (now - played_at_dt).total_seconds() / 3600.0
        
        # Gelecekten gelen hatalı bir zaman damgası varsa 0 kabul et
        if delta_tau < 0:
            delta_tau = 0
            
        # Zamansal Bozunma Formülü: W(t) = e^(-lambda * delta_tau)
        weight = math.exp(-lambda_val * delta_tau)
        
        weighted_tracks.append({
            "track_id": track_id,
            "track_name": track_name,
            "artist_name": artist_name,
            "weight": weight
        })
    
    # Ağırlığa göre büyükten küçüğe sırala
    weighted_tracks.sort(key=lambda x: x["weight"], reverse=True)
    
    # Aynı şarkının tekrarlarını filtreleyerek benzersiz bir Çekirdek Set (Top N) oluştur
    core_set = []
    seen_tracks = set()
    
    for t in weighted_tracks:
        if t["track_id"] not in seen_tracks:
            core_set.append(t)
            seen_tracks.add(t["track_id"])
        
        if len(core_set) == limit:
            break
            
    return core_set

# Test etmek için:
if __name__ == "__main__":
    # Radyo istasyonu için Çekirdek Set'i getir
    seeds = get_core_set(lambda_val=0.8, limit=5)
    print("--- ÇEKİRDEK SET ---")
    for idx, seed in enumerate(seeds, 1):
        print(f"{idx}. {seed['track_name']} - {seed['artist_name']} (Ağırlık: {seed['weight']:.4f})")