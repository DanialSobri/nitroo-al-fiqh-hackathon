import PyPDF2
from typing import List, Dict, Tuple
from io import BytesIO
import os

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
    def extract_text_with_pages(pdf_content: bytes) -> List[Dict[str, any]]:
        """Extract text from PDF with page numbers"""
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        pages_data = []
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text()
            if text.strip():
                pages_data.append({
                    "page_number": page_num,
                    "text": text
                })
        
        return pages_data
    
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
    
    @staticmethod
    def chunk_text_with_pages(pages_data: List[Dict], chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Chunk text while maintaining page number references"""
        chunks_with_pages = []
        
        # Combine all text with page boundaries marked
        full_text = ""
        page_boundaries = []  # List of (char_position, page_number)
        
        for page_data in pages_data:
            page_num = page_data["page_number"]
            text = page_data["text"]
            
            start_pos = len(full_text)
            full_text += text + "\n\n"
            end_pos = len(full_text)
            
            page_boundaries.append({
                "page": page_num,
                "start": start_pos,
                "end": end_pos
            })
        
        # Now create chunks and determine which pages each chunk spans
        start = 0
        text_length = len(full_text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk_text = full_text[start:end]
            
            # Find a good break point if not at the end
            if end < text_length:
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                split_point = max(last_period, last_newline)
                
                if split_point > chunk_size * 0.5:
                    end = start + split_point + 1
                    chunk_text = full_text[start:end]
            
            # Determine which pages this chunk spans
            chunk_pages = []
            for boundary in page_boundaries:
                # Check if chunk overlaps with this page
                chunk_start = start
                chunk_end = end
                page_start = boundary["start"]
                page_end = boundary["end"]
                
                # If there's any overlap, include this page
                if not (chunk_end <= page_start or chunk_start >= page_end):
                    # Calculate how much of the chunk is in this page
                    overlap_start = max(chunk_start, page_start)
                    overlap_end = min(chunk_end, page_end)
                    overlap_length = overlap_end - overlap_start
                    
                    # Only include page if significant content (>10% of chunk or >50 chars)
                    if overlap_length > max(50, len(chunk_text) * 0.1):
                        chunk_pages.append(boundary["page"])
            
            if chunk_text.strip() and chunk_pages:
                chunks_with_pages.append({
                    "text": chunk_text.strip(),
                    "pages": sorted(list(set(chunk_pages)))
                })
            
            # Move forward with overlap
            start = end - overlap if end < text_length else end
        
        return chunks_with_pages
    
    @staticmethod
    def chunk_by_page(pages_data: List[Dict]) -> List[Dict]:
        """Create one chunk per page"""
        chunks = []
        for page_data in pages_data:
            chunks.append({
                "text": page_data["text"],
                "pages": [page_data["page_number"] - 1]  # 0-based for PDF viewer
            })
        return chunks
    
    @staticmethod
    def save_pdf(pdf_content: bytes, contract_id: str, filename: str) -> str:
        """Save PDF file to storage"""
        storage_dir = "storage/contracts"
        os.makedirs(storage_dir, exist_ok=True)
        
        file_path = os.path.join(storage_dir, f"{contract_id}.pdf")
        with open(file_path, "wb") as f:
            f.write(pdf_content)
        
        return file_path

pdf_service = PDFService()
