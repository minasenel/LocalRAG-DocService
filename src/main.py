from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from src.llm_client import LLMClient
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStoreManager
import os
import glob

class QuestionRequest(BaseModel):
    question: str

def load_all_documents(data_dir: str):
    """data/ klasöründeki tüm desteklenen dosyaları (PDF, TXT, MD) yükler."""
    all_chunks = []
    supported_extensions = ['.pdf', '.txt', '.md']
    
    # Tüm desteklenen dosyaları bul
    files_found = []
    for ext in supported_extensions:
        pattern = os.path.join(data_dir, f"*{ext}")
        files_found.extend(glob.glob(pattern))
    
    if not files_found:
        print(f"--- UYARI: {data_dir} klasöründe desteklenen dosya bulunamadı ---")
        return []
    
    print(f"--- {len(files_found)} dosya bulundu, işleniyor... ---")
    
    for file_path in files_found:
        try:
            print(f"--- Döküman işleniyor: {os.path.basename(file_path)} ---")
            processor = DocumentProcessor(file_path)
            chunks = processor.process()
            all_chunks.extend(chunks)
            print(f"--- ✓ {os.path.basename(file_path)} işlendi ({len(chunks)} chunk) ---")
        except Exception as e:
            print(f"--- ✗ Hata ({os.path.basename(file_path)}): {e} ---")
            continue
    
    return all_chunks

def initialize_database():
    """Veritabanını başlatır veya yeniden yükler."""
    global vector_manager
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(current_dir, "data")
    
    if not os.path.exists(data_dir):
        print(f"--- HATA: {data_dir} klasörü bulunamadı! ---")
        vector_manager = VectorStoreManager(chunks=None)
        return
    
    chunks = load_all_documents(data_dir)
    
    if chunks:
        vector_manager = VectorStoreManager(chunks)
        print(f"--- RAG Sistemi Hazır ({len(chunks)} toplam chunk) ---")
    else:
        # Eğer dosya yoksa ama veritabanı varsa, mevcut veritabanını yükle
        vector_manager = VectorStoreManager(chunks=None)
        count = vector_manager.get_document_count()
        if count > 0:
            print(f"--- Mevcut veritabanı yüklendi ({count} doküman) ---")
        else:
            print("--- Veritabanı boş ---")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_manager
    initialize_database()
    yield
    print("--- Servis kapatılıyor ---")

app = FastAPI(title="Doküman Soru-Cevap Servisi", lifespan=lifespan)
llm = LLMClient()
vector_manager = None

# Static dosyalar için mount
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(current_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_root():
    """Ana sayfa - web arayüzünü döndürür."""
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {"message": "Web arayüzü bulunamadı. Lütfen /docs adresini kullanın."}

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    question = request.question
    context = ""
    if vector_manager:
        relevant_docs = vector_manager.search(question, k=3)
        
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        
        prompt = f"""### SİSTEM TALİMATI:
Sen bir döküman asistanısın. Aşağıdaki döküman içeriğini bir bilgi kaynağı olarak kullan ve soruyu cevapla. 
Sadece dökümandaki bilgilere sadık kal.

### DÖKÜMAN İÇERİĞİ:
{context}

### KULLANICI SORUSU:
{question}
"""
    else:
        prompt = question

    answer = await llm.ask(prompt)
    
    
    return {
        "question": question, 
        "answer": answer,
    }
#veri tabanı işlemleri için endpointlarımız:
# A. get_db_stats: veritabanındaki toplam doküman sayısını döndürür
@app.get("/db/stats") 
async def get_db_stats():
    """Veritabanı istatistiklerini döndürür."""
    if not vector_manager:
        raise HTTPException(status_code=503, detail="Veritabanı başlatılmamış")
    
    count = vector_manager.get_document_count()
    return {
        "total_documents": count,
        "status": "active" if count > 0 else "empty"
    }

# B. get_documents: veritabanındaki dokümanları listeler
@app.get("/db/documents")
async def get_documents(limit: int = 10):
    """Veritabanındaki dokümanları listeler."""
    if not vector_manager:
        raise HTTPException(status_code=503, detail="Veritabanı başlatılmamış")
    
    documents = vector_manager.get_documents_with_metadata(limit=limit)
    return {
        "count": len(documents),
        "documents": documents
    }

# C. preview_documents: veritabanındaki dokümanların önizlemesini gösterir
@app.get("/db/preview")
async def preview_documents(limit: int = 5):
    """Veritabanındaki dokümanların önizlemesini gösterir."""
    if not vector_manager:
        raise HTTPException(status_code=503, detail="Veritabanı başlatılmamış")
    
    documents = vector_manager.get_documents_with_metadata(limit=limit)
    return {
        "preview_count": len(documents),
        "total_documents": vector_manager.get_document_count(),
        "documents": documents
    }

# D. reload_database: veritabanını temizleyip data/ klasöründeki tüm dosyaları yeniden yükler
@app.post("/db/reload")
async def reload_database():
    """Veritabanını temizleyip data/ klasöründeki tüm dosyaları yeniden yükler."""
    global vector_manager
    
    try:
        # Mevcut veritabanını temizle
        import shutil
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chroma_db_path = os.path.join(current_dir, "chroma_db")
        
        if os.path.exists(chroma_db_path):
            shutil.rmtree(chroma_db_path)
            print("--- Mevcut veritabanı temizlendi ---")
        
        # Veritabanını yeniden başlat
        initialize_database()
        
        count = vector_manager.get_document_count() if vector_manager else 0
        return {
            "status": "success",
            "message": "Veritabanı başarıyla yeniden yüklendi",
            "total_documents": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı yeniden yüklenirken hata: {str(e)}")

# E. list_files: data/ klasöründeki tüm dosyaları listeler
@app.get("/db/files")
async def list_files():
    """data/ klasöründeki desteklenen dosyaları listeler."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(current_dir, "data")
    
    if not os.path.exists(data_dir):
        return {
            "files": [],
            "count": 0,
            "message": "data/ klasörü bulunamadı"
        }
    
    supported_extensions = ['.pdf', '.txt', '.md']
    files_found = []
    for ext in supported_extensions:
        pattern = os.path.join(data_dir, f"*{ext}")
        files_found.extend(glob.glob(pattern))
    
    files_info = []
    for file_path in files_found:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        files_info.append({
            "name": file_name,
            "path": file_path,
            "size": file_size,
            "extension": os.path.splitext(file_name)[-1].lower()
        })
    
    return {
        "files": files_info,
        "count": len(files_info),
        "data_directory": data_dir
    }