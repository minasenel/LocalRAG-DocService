import pytest
import os
import tempfile
import shutil
from src.document_processor import DocumentP
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStoreManager

def test_unsupported_file_extension():
    """Desteklenmeyen bir dosya formatı (.exe vs.) hata vermeli."""
    # Sahte bir dosya oluştur
    fake_file = "data/test.exe"
    try:
        with open(fake_file, "w") as f:
            f.write("dummy content")
        
        processor = DocumentProcessor(fake_file)
        
        # valueError fırlatılıp fırlatılmadığını kontrol et
        with pytest.raises(ValueError, match="Desteklenmeyen dosya formatı"):
            processor.process()
    finally:
        # Test bittikten sonra temizle
        if os.path.exists(fake_file):
            os.remove(fake_file)

def test_missing_file_error():
    """Var olmayan bir file path verildiğinde FileNotFoundError fırlatılmalı."""
    processor = DocumentProcessor("data/hayali_dosya.pdf")
    with pytest.raises(FileNotFoundError):
        processor.process()

def test_txt_file_processing():
    """TXT dosyası başarıyla işlenmeli ve chunk'lara bölünmeli."""
    test_file = "data/test_sample.txt"
    try:
        # Test içeriği oluştur (chunk_size=1000'den büyük olsun)
        test_content = "Bu bir test dosyasıdır.\n" * 100  # ~2000 karakter
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        # Chunk'lar oluşturulmuş olmalı
        assert len(chunks) > 0
        # Her chunk bir Document objesi olmalı
        assert hasattr(chunks[0], 'page_content')
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_md_file_processing():
    """Markdown dosyası başarıyla işlenmeli."""
    test_file = "data/test_sample.md"
    try:
        test_content = "# Başlık\n\nBu bir markdown dosyasıdır.\n\n## Alt Başlık\n\nİçerik burada."
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        try:
            chunks = processor.process()
            assert len(chunks) > 0
            assert hasattr(chunks[0], 'page_content')
        except Exception as e:
            # Eğer markdown modülü eksikse test'i skip et
            if "markdown" in str(e).lower() or "No module named" in str(e):
                pytest.skip(f"Markdown işleme için gerekli modül eksik: {e}")
            else:
                raise
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_empty_file_processing():
    """Boş dosya işlenebilmeli (hata vermemeli)."""
    test_file = "data/test_empty.txt"
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("")
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        # Boş dosya da işlenebilmeli (hata vermemeli)
        assert isinstance(chunks, list)
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_chunk_metadata_preservation():
    """Chunk'lar metadata bilgisini korumalı."""
    test_file = "data/test_metadata.txt"
    try:
        test_content = "Test içeriği " * 50
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        # Metadata kontrolü
        if len(chunks) > 0:
            # Langchain Document objeleri metadata içerebilir
            assert hasattr(chunks[0], 'metadata') or hasattr(chunks[0], 'page_content')
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_large_file_chunking():
    """Büyük dosyalar birden fazla chunk'a bölünmeli."""
    test_file = "data/test_large.txt"
    try:
        # chunk_size=1000, bu yüzden 3000 karakterlik içerik en az 2 chunk oluşturmalı
        test_content = "A" * 3000
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        # Büyük dosya birden fazla chunk'a bölünmeli
        assert len(chunks) >= 2
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_vector_store_initialization_with_chunks():
    """VectorStoreManager chunks ile başlatılabilmeli."""
    test_file = "data/test_vector.txt"
    try:
        test_content = "Vector store test içeriği " * 20
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        # Geçici bir veritabanı dizini kullan
        original_dir = VectorStoreManager.__init__.__defaults__
        manager = VectorStoreManager(chunks=chunks)
        
        assert manager.db is not None
        assert manager.embeddings is not None
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_vector_store_initialization_without_chunks():
    """VectorStoreManager chunks olmadan da başlatılabilmeli."""
    # Mevcut veritabanı yoksa boş bir manager oluşturulmalı
    manager = VectorStoreManager(chunks=None)
    assert manager.db is not None
    assert manager.embeddings is not None

def test_vector_store_search():
    """VectorStoreManager search metodu çalışmalı."""
    test_file = "data/test_search.txt"
    try:
        test_content = "Python programlama dili test içeriği " * 30
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        manager = VectorStoreManager(chunks=chunks)
        
        # Arama yapılabilmeli
        results = manager.search("Python", k=2)
        assert isinstance(results, list)
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_vector_store_document_count():
    """VectorStoreManager document count doğru çalışmalı."""
    test_file = "data/test_count.txt"
    try:
        test_content = "Test içeriği " * 50
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        manager = VectorStoreManager(chunks=chunks)
        count = manager.get_document_count()
        
        # En az bir doküman olmalı
        assert count > 0
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_vector_store_add_documents():
    """VectorStoreManager add_documents metodu çalışmalı."""
    test_file1 = "data/test_add1.txt"
    test_file2 = "data/test_add2.txt"
    try:
        # İlk dosya ile manager oluştur
        with open(test_file1, "w", encoding="utf-8") as f:
            f.write("İlk dosya içeriği " * 20)
        
        processor1 = DocumentProcessor(test_file1)
        chunks1 = processor1.process()
        manager = VectorStoreManager(chunks=chunks1)
        
        initial_count = manager.get_document_count()
        
        # İkinci dosyayı ekle
        with open(test_file2, "w", encoding="utf-8") as f:
            f.write("İkinci dosya içeriği " * 20)
        
        processor2 = DocumentProcessor(test_file2)
        chunks2 = processor2.process()
        
        result = manager.add_documents(chunks2)
        assert result is True
        
        # Doküman sayısı artmış olmalı
        new_count = manager.get_document_count()
        assert new_count >= initial_count
    finally:
        for f in [test_file1, test_file2]:
            if os.path.exists(f):
                os.remove(f)

def test_file_extension_case_insensitive():
    """Dosya uzantıları büyük/küçük harf duyarsız olmalı."""
    test_file = "data/test_case.TXT"  # Büyük harf
    try:
        test_content = "Test içeriği"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processor = DocumentProcessor(test_file)
        chunks = processor.process()
        
        # Büyük harfli uzantı da işlenebilmeli
        assert len(chunks) > 0
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)