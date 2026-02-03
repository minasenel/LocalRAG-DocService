import pytest
import os
from src.document_processor import DocumentProcessor

def test_unsupported_file_extension():
    """Desteklenmeyen bir dosya formatı (.exe vs.) hata vermeli."""
    # Sahte bir dosya oluştur
    fake_file = "data/test.exe"
    with open(fake_file, "w") as f:
        f.write("dummy content")
    
    processor = DocumentProcessor(fake_file)
    
    # valueError fırlatılıp fırlatılmadığını kontrol et
    with pytest.raises(ValueError, match="Desteklenmeyen dosya formatı"):
        processor.process()
    
    # Test bittikten sonra temizle
    os.remove(fake_file)

def test_missing_file_error():
    """Var olmayan bir file path verildiğinde FileNotFoundError fırlatılmalı."""
    processor = DocumentProcessor("data/hayali_dosya.pdf")
    with pytest.raises(FileNotFoundError):
        processor.process()