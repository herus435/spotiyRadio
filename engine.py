import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
import random

def get_candidate_pool(target_genre: str, access_token: str, limit: int = 20) -> list:
    """
    Faz 4.3 - Aday Havuzu Üretimi: Belirli bir tür (genre) için Spotify'da arama yapar.
    Arama limiti 10 olduğu için offset kullanarak birden fazla istek atar.
    """
    candidates = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 10'luk limit kısıtını aşmak için offset döngüsü
    for offset in range(0, limit, 10):
        url = f"https://api.spotify.com/v1/search?q=genre:\"{target_genre}\"&type=track&limit=10&offset={offset}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            tracks = response.json().get("tracks", {}).get("items", [])
            for t in tracks:
                candidates.append({
                    "id": t["id"],
                    "name": t["name"],
                    "artist_id": t["artists"][0]["id"],
                    "artist_name": t["artists"][0]["name"],
                    "duration_ms": t["duration_ms"],
                    "explicit": t["explicit"],
                    "album_type": t["album"]["album_type"]
                })
        else:
            break
            
    return candidates

def create_track_vector(proxy_energy: float, genre_match: bool) -> np.ndarray:
    """
    Şarkının özelliklerini bir numpy dizisine (vektöre) çevirir.
    Basit bir boyutlandırma yapıyoruz: [Enerji, Tür Eşleşmesi]
    """
    genre_weight = 1.0 if genre_match else 0.0
    return np.array([[proxy_energy, genre_weight]])

def score_and_select_best_candidate(core_set_vector: np.ndarray, candidates: list, target_genre: str) -> dict:
    """
    Faz 4.4 - Benzerlik Skorlama: Aday havuzundaki parçaları,
    Çekirdek Set'in temsil ettiği vektör ile karşılaştırır (Cosine Similarity).
    """
    best_candidate = None
    highest_similarity = -1.0
    
    for candidate in candidates:
        # Aday şarkı için proxy enerji skorunu hesapla
        energy = calculate_proxy_energy(
            track_name=candidate["name"],
            duration_ms=candidate["duration_ms"],
            explicit=candidate["explicit"],
            album_type=candidate["album_type"]
        )
        
        # Adayın vektörünü oluştur (Şimdilik genre araması yaptığımız için tür eşleşmesini 1.0 (True) kabul ediyoruz)
        candidate_vector = create_track_vector(proxy_energy=energy, genre_match=True)
        
        # Kosinüs Benzerliği Hesaplama
        similarity = cosine_similarity(core_set_vector, candidate_vector)[0][0]
        
        # En yüksek skorlu adayı güncelle
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_candidate = candidate
            best_candidate["similarity_score"] = similarity
            
    return best_candidate

if __name__ == "__main__":
    # Test için daha önce terminalden aldığın access_token'ı buraya yapıştır
    TEST_TOKEN = "BQBSR3WyqweyRpFndmcgrjwZRwDHvX7lm5tajCatpWPzv3HBd0I9oqc7V1xdd3P8kg2vLk9TKsMsYKOP1Oqrskn6LTIeu-sLKJ-RKi8jt9RdfTpdeZQ6zLoFSToJt5fjOoOmtajjcuLuNwBg5F-5jx9dWiQZz-mcmKe6M_600akT8MKLNbdiOft_H-gzMjp4-wieZRF9m-n7os8P0EYY_xN1bc43x2pBPndmxSE7t01t67T-FqMC_1rZ_UWeGoWzqy6l511E4YKlJYaHt2frV3TCgUCY5Bym9LFQgPeCmzKuDs9D" 
    
    # Test etmek istediğimiz örnek bir tür (genre) belirleyelim
    HEDEF_TUR = "turkish rock" 
    
    print(f"🔍 '{HEDEF_TUR}' türünde aday şarkılar aranıyor...")
    
    # 1. Faz 4.3 - Adayları Spotify Search API'den çekiyoruz (10 adet çekelim)
    adaylar = get_candidate_pool(target_genre=HEDEF_TUR, access_token=TEST_TOKEN, limit=10)
    
    if adaylar:
        print(f"✅ {len(adaylar)} aday havuzdan çekildi. Cosine Similarity ile skorlama yapılıyor...\n")
        
        # 2. Faz 2'den geldiğini varsaydığımız örnek bir Çekirdek Set Vektörü (Kullanıcı Zevki)
        # Örnek: [0.8 enerji, 1.0 tür eşleşmesi] -> Kullanıcı yüksek enerjili ve bu türü seviyor demek.
        ornek_cekirdek_vektor = np.array([[0.8, 1.0]])
        
        # 3. Faz 4.4 - Havuzdaki parçaları zevk vektörümüzle karşılaştırıp en iyisini seçiyoruz
        en_iyi_aday = score_and_select_best_candidate(
            core_set_vector=ornek_cekirdek_vektor, 
            candidates=adaylar, 
            target_genre=HEDEF_TUR
        )
        
        if en_iyi_aday:
            print("🎵 --- İLK ADAY ŞARKIMIZ BULUNDU --- 🎵")
            print(f"🎶 Şarkı        : {en_iyi_aday['name']}")
            print(f"🎤 Sanatçı      : {en_iyi_aday['artist_name']}")
            print(f"⏱️ Süre (ms)    : {en_iyi_aday['duration_ms']}")
            print(f"📈 Benzerlik Skoru : {en_iyi_aday['similarity_score']:.4f} / 1.0000")
            print("--------------------------------------")
    else:
        print("❌ Aday bulunamadı. Token süresi dolmuş olabilir veya tür (genre) eşleşmemiş olabilir.")

# --- Öneri Motorunu Çalıştırma Mantığı ---
# def run_recommendation_engine(access_token: str, core_set: list):
#    1. Çekirdek setin ortalama enerji ve tür ağırlıklarını hesapla -> core_set_vector
#    2. En baskın türü bul (örn: "turkish rock")
#    3. get_candidate_pool() ile adayları çek
#    4. score_and_select_best_candidate() ile çalınacak bir sonraki parçayı bul.

def calculate_proxy_energy(track_name: str, duration_ms: int, explicit: bool, album_type: str) -> float:
    """
    Faz 4.2 - Audio Features olmadan metadata tabanlı Proxy Enerji Skoru üretir.
    0 (Düşük Enerji/Acoustic) ile 1 (Yüksek Enerji/Hareketli) arası bir değer döner.
    """
    score = 0.5  # Nötr başlangıç noktası

    name_lower = track_name.lower()
    
    # 1. Anahtar Kelime Analizi
    if any(kw in name_lower for kw in ["remix", "sped up", "live", "edit"]):
        score += 0.2
    if any(kw in name_lower for kw in ["acoustic", "instrumental", "slowed", "lullaby"]):
        score -= 0.2
        
    # 2. Süre (Duration) Analizi
    # Kısa parçalar (3 dakikadan az) genelde pop/enerjik eğilimlidir
    if duration_ms < 180000:
        score += 0.1
    # Uzun parçalar (5 dakikadan fazla) prog/ambient eğilimlidir
    elif int(duration_ms) > 300000:
        score -= 0.1
        
    # 3. Explicit ve Albüm Tipi
    if explicit:
        score += 0.05
    if album_type == "single":
        score += 0.05
        
    # Skoru 0.0 ile 1.0 arasına sınırla
    return max(0.0, min(1.0, score))

def fetch_artist_genres(artist_id: str, access_token: str) -> list:
    """
    Spotify API'den sanatçının tür (genre) etiketlerini çeker.
    """
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("genres", [])
    return []

# --- Test ve Vektörleştirme Mantığı ---
if __name__ == "__main__":
    # Örnek Şarkı Analizi Testi
    ornek_isim = "Blinding Lights (Remix)"
    ornek_sure = 175000
    ornek_skor = calculate_proxy_energy(ornek_isim, ornek_sure, explicit=False, album_type="single")
    
    print(f"'{ornek_isim}' için Proxy Enerji Skoru: {ornek_skor:.2f}")