# Yerel Doküman Soru-Cevap Servisi (RAG Mimarisi)

Bu proje; veri gizliliğini merkeze alarak, tamamen yerel donanım üzerinde çalışan bir Doküman Soru-Cevap (Document Q&A) servisidir. Sistem, RAG (Retrieval-Augmented Generation) mimarisini kullanarak kullanıcının yüklediği dökümanlar (PDF, TXT, MD) üzerinden anlamlı ve bağlama dayalı yanıtlar üretir.

## Proje Amacı ve Çalışma Mantığı

Proje, verilerin bulut tabanlı bir LLM'e (Large Language Model) gönderilmesi yerine, yerel bir yapay zeka motoru (Ollama) ve vektör veritabanı (ChromaDB) kullanılarak işlenmesini sağlar.

### Çalışma Akışı

1. **Veri İşleme (Ingestion)**: Belirlenen dizindeki dökümanlar RecursiveCharacterTextSplitter ile anlam bütünlüğü korunacak şekilde küçük parçalara (chunks) bölünür.
2. **Vektörleştirme (Embedding)**: Metin parçaları, Llama 3.2 embedding modeli kullanılarak matematiksel vektörlere dönüştürülür.
3. **Depolama**: Bu vektörler, hızlı benzerlik araması yapılabilmesi için ChromaDB üzerinde indekslenir.
4. **Sorgulama (Retrieval)**: Kullanıcıdan gelen soru vektörleştirilir ve veritabanındaki en alakalı döküman parçaları getirilir.
5. **Yanıt Üretimi (Generation)**: Getirilen döküman içeriği (context), sistem talimatlarıyla birlikte LLM'e iletilerek sadece dökümana sadık bir yanıt üretilir.

## Proje Dizini ve Dosya Yapısı

```
llmCS1/
├── data/                       # Sistemin okuyacağı kaynak dökümanların (PDF, TXT, MD) bulunduğu klasör
├── src/                        # Projenin kaynak kodları
│   ├── main.py                 # FastAPI uygulama merkezi ve lifespan (başlangıç/bitiş) yönetimi
│   ├── document_processor.py   # Factory Pattern ile döküman yükleme ve parçalama mantığı
│   ├── vector_store.py         # Vektör veritabanı (ChromaDB) oluşturma ve arama süreçleri
│   └── llm_client.py           # Ollama API üzerinden LLM iletişimini sağlayan istemci
├── tests/                      # Hata senaryolarını ve mantıksal birimleri test eden pytest dosyaları
├── chroma_db/                  # Vektör verilerinin kalıcı olarak saklandığı veritabanı dizini
├── requirements.txt            # Projenin çalışması için gerekli bağımlılıklar listesi
└── .gitignore                  # Git takibine alınmayacak dosyaların (venv, cache, db) listesi
```

## Kurulum ve Çalıştırma

### Gereksinimler

- Python 3.10 veya üzeri
- Ollama (Yerel LLM çıkarımı için)

### Adımlar

1. **Ollama Modeli**: Llama 3.2 modelinin sisteminizde yüklü olduğundan emin olun:

```bash
ollama pull llama3.2
```

2. **Sanal Ortam Kurulumu**:

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# veya Windows için:
# venv\Scripts\activate
```

3. **Bağımlılıkların Yüklenmesi**:

```bash
pip install -r requirements.txt
```

4. **Uygulamayı Başlatma**:

```bash
uvicorn src.main:app --reload
```

Uygulama başladığında terminalde "RAG Sistemi Hazır" mesajı görüldükten sonra http://127.0.0.1:8000/docs üzerinden test edilebilir.

## Hata Yönetimi ve Testler

Sistem, mühendislik yaklaşımlarına uygun olarak beklenmedik girişleri (desteklenmeyen dosya formatı, eksik dosya yolu vb.) yakalayacak şekilde tasarlanmıştır. Bu mekanizmaları test etmek için:

```bash
export PYTHONPATH=$PYTHONPATH:.
pytest
```

komutu kullanılabilir. Testler, tests/ dizini altındaki senaryolar üzerinden sistemin hata yakalama kabiliyetini doğrular.

## API Endpoint'leri

Sistem, FastAPI üzerinden aşağıdaki REST API endpoint'lerini sunar:

### 1. Soru-Cevap Endpoint'i

**`POST /ask`**
- RAG mimarisi ile dokümanlardan soru-cevap yapma
- Parametre: `question` (string)
- Dönen: Soru ve cevap

**Örnek:**
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Teknoloji Kahvesi ne zaman yapılıyor?"}'
```

### 2. Veritabanı Yönetimi Endpoint'leri

**`GET /db/stats`**
- Veritabanı istatistiklerini döndürür
- Toplam doküman sayısı ve durum bilgisi

**`GET /db/documents?limit=10`**
- Veritabanındaki dokümanları listeler
- Metadata bilgileriyle birlikte
- `limit` parametresi ile sınırlama (varsayılan: 10)

**`GET /db/preview?limit=5`**
- Dokümanların kısa önizlemesini gösterir
- Toplam doküman sayısı ile birlikte
- `limit` parametresi ile sınırlama (varsayılan: 5)

**`GET /db/files`**
- `data/` klasöründeki desteklenen dosyaları listeler
- Dosya adı, yolu, boyutu ve uzantısı bilgileri

**`POST /db/reload`**
- Veritabanını temizleyip `data/` klasöründeki tüm dosyaları yeniden yükler
- Dosya değişikliklerinden sonra kullanılır
- Mevcut veritabanını siler ve sıfırdan oluşturur

**Örnek:**
```bash
curl -X POST "http://127.0.0.1:8000/db/reload"
```

## Çoklu Dosya Desteği

Sistem, `data/` klasöründeki **tüm** desteklenen dosyaları (PDF, TXT, MD) otomatik olarak yükler:

- ✅ Her dosya ayrı metadata ile saklanır (dosya adı, yolu)
- ✅ Her dosya farklı ID'ler altında indekslenir
- ✅ Uygulama başlangıcında tüm dosyalar otomatik işlenir
- ✅ Yeni dosya eklemek için `POST /db/reload` endpoint'ini kullanın

### Dosya Yönetimi

1. **Yeni dosya ekleme:**
   - `data/` klasörüne yeni PDF/TXT/MD dosyası ekleyin
   - `POST /db/reload` endpoint'ini çağırın

2. **Dosya değişikliği:**
   - Dosyayı düzenleyin
   - `POST /db/reload` endpoint'ini çağırın

3. **Dosyaları görüntüleme:**
   - `GET /db/files` ile `data/` klasöründeki dosyaları listeleyin

## Özellikler

✅ Tamamen yerel çalışma (veri gizliliği)  
✅ PDF, TXT, MD formatı desteği  
✅ **Çoklu dosya desteği** - `data/` klasöründeki tüm dosyalar otomatik yüklenir  
✅ RAG mimarisi ile bağlama dayalı yanıtlar  
✅ ChromaDB ile hızlı vektör araması  
✅ Ollama entegrasyonu  
✅ FastAPI tabanlı REST API  
✅ **6 farklı endpoint** ile veritabanı yönetimi  
✅ **Manuel veritabanı yeniden yükleme** desteği  
✅ Kapsamlı hata yönetimi ve test altyapısı  
✅ **13 unit test** ile kapsamlı test kapsamı  

## Swagger UI

Tüm endpoint'leri test etmek için Swagger UI kullanılabilir:

```
http://127.0.0.1:8000/docs
```

---

Bu proje açık kaynak kodludur.
