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

## Özellikler

✅ Tamamen yerel çalışma (veri gizliliği)  
✅ PDF, TXT, MD formatı desteği  
✅ RAG mimarisi ile bağlama dayalı yanıtlar  
✅ ChromaDB ile hızlı vektör araması  
✅ Ollama entegrasyonu  
✅ FastAPI tabanlı REST API  
✅ Kapsamlı hata yönetimi ve test altyapısı  

---

Bu proje açık kaynak kodludur.
