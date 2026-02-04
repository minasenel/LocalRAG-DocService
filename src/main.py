from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from src.llm_client import LLMClient
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStoreManager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_manager
    # data_path kısmını garantiye almak için os.path.join kullanalım
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(current_dir, "data", "notes.txt")
    
    if os.path.exists(data_path):
        print(f"--- Döküman işleniyor: {data_path} ---")
        try:
            processor = DocumentProcessor(data_path)
            chunks = processor.process()
            vector_manager = VectorStoreManager(chunks)
            print("--- RAG Sistemi Hazır ---")
        except Exception as e:
            print(f"--- Hata: {e} ---")
    else:
        print(f"--- HATA: {data_path} dosyası bulunamadı! ---")
    
    yield
    print("--- Servis kapatılıyor ---")

app = FastAPI(title="Doküman Soru-Cevap Servisi", lifespan=lifespan)
llm = LLMClient()
vector_manager = None

@app.post("/ask")
async def ask_question(question: str):
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