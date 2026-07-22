📻 Akıllı Radyo İstasyonu ve Yerel Öneri Motoru
===============================================

Bu proje, Spotify API kısıtlamalarını (Recommendations ve Audio Features gibi uç noktaların kaldırılmasını) by-pass etmek amacıyla geliştirilmiş, tamamen yerelde çalışan matematiksel bir **Akıllı Radyo ve Müzik Öneri Motoru** sistemidir. FastAPI tabanlı backend mimarisi, NumPy ve Scikit-Learn tabanlı vektör benzerliği analizi ve Spotify Web Playback SDK ile tarayıcıda kesintisiz oynatma deneyimi sunar.

🚀 Öne Çıkan Özellikler
-----------------------

*   **Zamansal Bozunma (Temporal Decay):** Kullanıcının dinleme geçmişindeki şarkıların ağırlığını zamana göre exponential olarak azaltarak anlık zevk analizi yapar ($W(t) = e^{-\\lambda \\cdot \\Delta\\tau}$).
    
*   **Proxy Enerji Skoru:** Ses özelliklerine (Audio Features) ihtiyaç duymadan, şarkı adı, süresi, albüm tipi ve explicit durumu gibi metadataları kullanarak heuristic 0-1 arası enerji skoru üretir.
    
*   **Yerel Vektör Benzerliği (Cosine Similarity):** scikit-learn kullanarak kullanıcının çekirdek zevk vektörü ile aday havuzunu karşılaştırır ve en uygun parçayı seçer.
    
*   **Popülerlik Doğrulama:** Spotify Top 50 listesini baz alarak mainstream çapraz kontrolü yapar ve nihai radyo skoruna bonus ekler.
    
*   **Kesintisiz Kuyruk Besleme:** Web Playback SDK üzerinden çalan şarkının süresini takip ederek bitime 20 saniye kala otomatik olarak sıraya yeni şarkı ekler (/feed-queue).
    

🛠️ Kullanılan Teknolojiler
---------------------------

*   **Backend:** Python, FastAPI, Uvicorn, Requests, NumPy, Scikit-Learn, Jinja2
    
*   **Arayüz:** HTML5, JavaScript (Spotify Web Playback SDK)
    
*   **API:** Spotify Web API (OAuth 2.0 Authorization Code Flow)
    

📂 Proje Yapısı
---------------

Plaintext

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   spotifyRadio/  │  ├── main.py             # FastAPI ana sunucusu ve OAuth rotaları  ├── engine.py           # Vektör motoru, Proxy enerji ve benzerlik hesaplamaları  ├── templates/  │   └── index.html      # Spotify Web Playback SDK arayüzü  └── requirements.txt    # Gerekli Python kütüphaneleri   `

⚙️ Kurulum ve Çalıştırma
------------------------

### 1\. Depoyu Klonlayın


git clone https://github.com/herus435/spotifyRadio.git
cd spotifyRadio

### 2\. Sanal Ortam Oluşturun ve Aktif Edin

conda create -n radyo_env python=3.10
conda activate radyo_env

### 3\. Gerekli Kütüphaneleri Yükleyin

pip install fastapi uvicorn requests numpy scikit-learn jinja2

### 4\. Spotify Developer Bilgilerini Ayarlayın

main.py içerisindeki CLIENT\_ID, CLIENT\_SECRET ve REDIRECT\_URI alanlarını kendi Spotify Developer paneli bilgilerinizle güncelleyin.

### 5\. Sunucuyu Başlatın

uvicorn main:app --host 127.0.0.1 --port 8080 --reload

### 6\. Kullanım

1.  Tarayıcınızda \[http://127.0.0.1:8080/login\](http://127.0.0.1:8080/login) adresine giderek Spotify hesabınızla giriş yapın.
    
2.  Otomatik olarak yönlendirileceğiniz \[http://127.0.0.1:8080/\](http://127.0.0.1:8080/) sayfasında **"Radyoyu Başlat"** butonuna tıklayın.
    
3.  Spotify uygulamanızdan ses çıkış cihazı olarak **"Akıllı Radyo Web Player"** seçeneğini seçerek müziğin akışını başlatın.
