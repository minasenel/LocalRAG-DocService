from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

class VectorStoreManager:
    """Vektör veritabanı işlemlerini (kayıt ve arama) yöneten sınıf."""
    
    def __init__(self, chunks=None):
        # Ollama üzerinden Llama 3.2 modelini embedding için kullanıyoruz
        self.embeddings = OllamaEmbeddings(model="llama3.2")
        self.persist_directory = "./chroma_db"
        
        if chunks:
            # Eğer döküman parçaları gelmişse veritabanını oluştur ve diske kaydet
            self.db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            # Eğer parçalar yoksa mevcut veritabanını diskten yükle
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

    def search(self, query: str, k: int = 3):
        """Soruyla en alakalı k adet döküman parçasını getirir."""
        if not self.db:
            return []
        return self.db.similarity_search(query, k=k)