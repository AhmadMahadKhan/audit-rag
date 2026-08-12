# ===== app/metadata/registry.py =====
from app.metadata.document_info_extractor import DocumentInfoExtractor
from app.metadata.language_detector import LanguageDetector
from app.metadata.date_extractor import DateExtractor
from app.metadata.currency_extractor import CurrencyExtractor
from app.metadata.company_extractor import CompanyExtractor

def get_extractors() -> list:
    return [DocumentInfoExtractor(), LanguageDetector(), DateExtractor(), CurrencyExtractor(), CompanyExtractor()]
