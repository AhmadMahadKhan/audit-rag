from app.metadata.base import BaseExtractor
from app.metadata.schema import MetadataField
from app.canonical.schema import CanonicalDocument

class DocumentInfoExtractor(BaseExtractor):
    name = "document_info_extractor"

    def extract(self, doc: CanonicalDocument) -> list[MetadataField]:
        fields = [
            MetadataField(key="file_name", value=doc.info.file_name, category="document", confidence=1.0, extractor=self.name),
            MetadataField(key="file_type", value=doc.info.file_type, category="document", confidence=1.0, extractor=self.name),
            MetadataField(key="page_count", value=str(doc.info.page_count), category="document", confidence=1.0, extractor=self.name),
            MetadataField(key="parser_version", value=doc.info.parser_version, category="processing", confidence=1.0, extractor=self.name),
        ]
        if doc.info.language:
            fields.append(MetadataField(key="language", value=doc.info.language, category="document", confidence=1.0, extractor=self.name))
        return fields