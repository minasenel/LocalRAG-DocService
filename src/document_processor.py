import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    """
    Farklı formatlardaki (PDF, TXT, MD) dökümanları otomatik olarak tanıyan,
    yükleyen ve küçük parçalara ayıran sınıf.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def process(self):
        """
        Dosya uzantısına göre uygun yükleyiciyi seçer ve metni parçalara böler.
        """
        # Dosyanın varlığını kontrol et
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Döküman bulunamadı: {self.file_path}")

        # Uzantıyı al ve küçük harfe çevir
        ext = os.path.splitext(self.file_path)[-1].lower()
        
        # Factory Logic: Uzantıya göre loader seçimi
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(self.file_path)
            elif ext == ".txt":
                loader = TextLoader(self.file_path, encoding='utf-8')
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(self.file_path)
            else:
                # Beklenmeyen bir giriş geldiğinde hata yakalama
                raise ValueError(f"Desteklenmeyen dosya formatı: {ext}. Lütfen PDF, TXT veya MD kullanın.")
            
            documents = loader.load()
        except Exception as e:
            raise Exception(f"Döküman yüklenirken hata oluştu: {str(e)}")

        # Metni Parçalara Bölme
        # 1000 karakterlik parçalar ve 100 karakterlik örtüşme ile bağlam korunur.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        return text_splitter.split_documents(documents)