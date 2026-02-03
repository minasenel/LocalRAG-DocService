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