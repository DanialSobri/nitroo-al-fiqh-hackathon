import PyPDF2
from typing import List
from io import BytesIO

class PDFService:
    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> str:
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_content = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text.strip():
                text_content.append(text)
        
        return "\n\n".join(text_content)
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                split_point = max(last_period, last_newline)
                
                if split_point > chunk_size * 0.5:
                    end = start + split_point + 1
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap if end < text_length else end
        
        return [chunk for chunk in chunks if chunk]

pdf_service = PDFService()
