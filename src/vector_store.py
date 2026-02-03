import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader

class DocumentProcessor:
    """PDF, TXT ve Markdown dökümanlarını otomatik tanıyan ve işleyen sınıf."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def process(self):
        """Dosya uzantısına göre uygun yükleyiciyi seçer ve parçalara böler."""
        ext = os.path.splitext(self.file_path)[-1].lower()
        
        # 1. Uzantıya göre Loader seçimi
        if ext == ".pdf":
            loader = PyPDFLoader(self.file_path)
        elif ext == ".txt":
            loader = TextLoader(self.file_path)
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(self.file_path)
        else:
            raise ValueError(f"Desteklenmeyen dosya formatı: {ext}")

        documents = loader.load()
        
        # 2. Metni parçalara böl (Vaka çalışması PEP8 standardı gereği docstring eklendi) [cite: 35]
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        return text_splitter.split_documents(documents)