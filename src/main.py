from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from src.llm_client import LLMClient
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStoreManager
import os

# 1. Lifespan, Startup ve Shutdown işlemlerini yönetir
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken yapılacaklar (Startup)
    global vector_manager
    data_path = "data/notlar.txt"
    
    if os.path.exists(data_path):
        print(f"--- Döküman işleniyor: {data_path} ---")
        try:
            processor = DocumentProcessor(data_path)
            chunks = processor.process()
            vector_manager = VectorStoreManager(chunks)
            print("--- RAG Sistemi Hazır ---")
        except Exception as e:
            print(f"--- Hata: {e} ---")
    
    yield  # uygulama burada çalışmaya devam eder
    
    # Uygulama kapanırken 
    print("--- Servis kapatılıyor ---")

# FastAPI uygulamasını lifespan ile başlatıyoruz
app = FastAPI(title="Doküman Soru-Cevap Servisi", lifespan=lifespan)
llm = LLMClient()
vector_manager = None

@app.get("/health")
async def health():
    return {
        "status": "up", 
        "rag_status": "active" if vector_manager else "inactive"
    }

@app.post("/ask")
async def ask_question(question: str):
    if vector_manager:
        relevant_docs = vector_manager.search(question, k=3)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        prompt = f"""
        Aşağıdaki döküman içeriğine dayanarak soruyu cevapla. 
        Cevap dökümanda yoksa 'Bu bilgi dökümanda bulunmuyor' de.

        Döküman:
        {context}

        Soru: {question}
        """
    else:
        prompt = question

    answer = await llm.ask(prompt)
    return {"question": question, "answer": answer}