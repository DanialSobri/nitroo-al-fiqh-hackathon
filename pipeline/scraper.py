"""
Web scraper to extract PDFs from BNM Islamic Banking page and store in Qdrant vector database.
"""

import os
import re
import warnings
# Suppress tensorflow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore')

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import pdfplumber
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
import hashlib
import time

# Optional Selenium for JavaScript rendering
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Note: Selenium not available. Install with: pip install selenium webdriver-manager")


class BNMScraper:
    def __init__(self, base_url: str, output_dir: str = "pdfs", qdrant_path: str = None, qdrant_url: str = None):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.selenium_cookies = None  # Store cookies from Selenium session
        
        # Qdrant connection - prefer URL (server) over path (local file)
        if qdrant_url:
            self.qdrant_client = QdrantClient(url=qdrant_url)
            self.qdrant_path = None
            print(f"Connecting to Qdrant server at: {qdrant_url}")
        elif qdrant_path:
            self.qdrant_client = QdrantClient(path=qdrant_path)
            self.qdrant_path = qdrant_path
            print(f"Using local Qdrant database at: {qdrant_path}")
        else:
            # Default to local file database
            self.qdrant_path = "./qdrant_db"
            self.qdrant_client = QdrantClient(path=self.qdrant_path)
            print(f"Using local Qdrant database at: {self.qdrant_path}")
        
        # Initialize sentence transformer for embeddings
        print("Loading embedding model...")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            print("This might be due to protobuf version conflict.")
            print("Try running: pip install 'protobuf>=3.20.3,<5.0.0' --force-reinstall")
            raise
        
        # Collection name
        self.collection_name = "bnm_pdfs"
        
        # Initialize or get collection
        self._setup_collection()
        
    def _setup_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 produces 384-dimensional vectors
                        distance=Distance.COSINE
                    )
                )
            else:
                print(f"Collection {self.collection_name} already exists")
        except Exception as e:
            print(f"Error setting up collection: {e}")
            raise
    
    def get_page_content(self, url: str, use_selenium: bool = False) -> BeautifulSoup:
        """Fetch and parse HTML content from URL"""
        if use_selenium and SELENIUM_AVAILABLE:
            return self._get_page_content_selenium(url)
        else:
            return self._get_page_content_requests(url)
    
    def _get_page_content_requests(self, url: str) -> BeautifulSoup:
        """Fetch page using requests (faster but no JavaScript)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            raise
    
    def _get_page_content_selenium(self, url: str) -> BeautifulSoup:
        """Fetch page using Selenium (renders JavaScript)"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is not installed. Install with: pip install selenium webdriver-manager")
        
        print("  Using Selenium to render JavaScript...")
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            
            # Wait for table to load (wait up to 10 seconds)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                print("  Table found, waiting for content to load...")
                time.sleep(2)  # Additional wait for dynamic content
            except:
                print("  Warning: Table not found, proceeding anyway...")
            
            # Store cookies from Selenium session for later use
            self.selenium_cookies = driver.get_cookies()
            
            # Get page source after JavaScript execution
            html = driver.page_source
            return BeautifulSoup(html, 'lxml')
        finally:
            if driver:
                driver.quit()
    
    def find_pdf_links_from_table(self, soup: BeautifulSoup, base_url: str) -> list:
        """Find PDF links from table structure (Date, Title, Type)"""
        pdf_links = []
        
        # Find all tables on the page
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            # Find tbody for data rows
            tbody = table.find('tbody')
            if not tbody:
                # If no tbody, get all rows and skip header
                rows = table.find_all('tr')
                tbody_rows = rows[1:] if rows else []
            else:
                tbody_rows = tbody.find_all('tr')
            
            # Find thead to identify column indices
            thead = table.find('thead')
            date_col_idx = 0
            title_col_idx = 1
            type_col_idx = 2
            
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    header_cells = header_row.find_all(['th', 'td'])
                    for idx, cell in enumerate(header_cells):
                        header_text = cell.get_text(strip=True).lower()
                        if 'date' in header_text:
                            date_col_idx = idx
                        elif 'title' in header_text:
                            title_col_idx = idx
                        elif 'type' in header_text:
                            type_col_idx = idx
            
            # Process each data row
            for row_idx, row in enumerate(tbody_rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                
                # Extract date - skip hidden spans and get visible text
                date = ""
                if date_col_idx < len(cells):
                    date_cell = cells[date_col_idx]
                    # Remove hidden elements
                    for hidden in date_cell.find_all(class_=re.compile('hidden', re.I)):
                        hidden.decompose()
                    date = date_cell.get_text(strip=True)
                
                # Extract type from badge div
                doc_type = ""
                if type_col_idx < len(cells):
                    type_cell = cells[type_col_idx]
                    # Look for badge div or get text directly
                    badge = type_cell.find('div', class_=re.compile('badge', re.I))
                    if badge:
                        doc_type = badge.get_text(strip=True)
                    else:
                        doc_type = type_cell.get_text(strip=True)
                
                # Extract all PDF links from title cell
                if title_col_idx < len(cells):
                    title_cell = cells[title_col_idx]
                    
                    # Find all PDF links in the title cell (including nested ones in ul/li)
                    all_links = title_cell.find_all('a', href=True)
                    
                    for link in all_links:
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True)
                        
                        # Normalize href - remove trailing slash
                        href_clean = href.rstrip('/')
                        
                        # Check if it's a PDF link
                        # Check for .pdf extension (even if URL ends with /)
                        is_pdf = (href_clean.lower().endswith('.pdf') or 
                                 href.lower().endswith('.pdf/') or
                                 '.pdf' in href_clean.lower())
                        
                        # Skip non-PDF file extensions
                        if not is_pdf:
                            # Check for other common file extensions to exclude
                            excluded_extensions = ['.xlsx', '.xls', '.doc', '.docx', '.zip', 
                                                  '.rar', '.txt', '.html', '.htm', '.xml']
                            href_lower = href_clean.lower()
                            if any(href_lower.endswith(ext) for ext in excluded_extensions):
                                continue
                        
                        if is_pdf:
                            # Use cleaned href (already normalized above)
                            full_url = urljoin(base_url, href_clean)
                            
                            # Use link text as title, or get main title from cell
                            if link_text:
                                title = link_text
                            else:
                                # Get the main title (first text before lists)
                                title = title_cell.get_text(strip=True)
                                # Try to get the first paragraph text
                                first_p = title_cell.find('p')
                                if first_p:
                                    first_link = first_p.find('a')
                                    if first_link and first_link.get('href') == href:
                                        title = first_link.get_text(strip=True)
                            
                            pdf_links.append({
                                'url': full_url,
                                'text': title or 'Untitled PDF',
                                'date': date,
                                'type': doc_type
                            })
        
        # Also check for PDF links outside tables (fallback)
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if href.lower().endswith('.pdf') or '.pdf' in href.lower():
                full_url = urljoin(base_url, href)
                # Check if this URL is already in our list
                if not any(p['url'] == full_url for p in pdf_links):
                    pdf_links.append({
                        'url': full_url,
                        'text': link.get_text(strip=True) or 'Untitled PDF',
                        'date': '',
                        'type': ''
                    })
        
        # Remove duplicates based on URL
        seen = set()
        unique_links = []
        for link in pdf_links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
        
        return unique_links
    
    def find_pdf_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """Find all PDF links on the page (wrapper for table-based scraping)"""
        return self.find_pdf_links_from_table(soup, base_url)
    
    def download_pdf_selenium(self, url: str, filename: str) -> str:
        """Download PDF using Selenium (more reliable for protected content)"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is not installed")
        
        options = Options()
        options.add_argument('--headless=new')  # Use new headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Navigate to URL
            driver.get(url)
            time.sleep(2)  # Wait for page to load
            
            # Get page source - for PDFs, Chrome might display them inline
            page_source = driver.page_source
            
            filepath = self.output_dir / filename
            
            # Check if page source starts with PDF magic number
            if page_source.startswith('%PDF'):
                # PDF content is directly in page source
                with open(filepath, 'wb') as f:
                    # Convert string to bytes (PDF is binary)
                    f.write(page_source.encode('latin-1', errors='ignore'))
            else:
                # Try to get response body using execute_script
                try:
                    # Use JavaScript to fetch the PDF
                    pdf_content = driver.execute_script("""
                        return fetch(arguments[0], {method: 'GET'})
                            .then(response => response.arrayBuffer())
                            .then(buffer => {
                                const bytes = new Uint8Array(buffer);
                                return Array.from(bytes).map(b => String.fromCharCode(b)).join('');
                            });
                    """, url)
                    
                    if pdf_content and pdf_content.startswith('%PDF'):
                        with open(filepath, 'wb') as f:
                            f.write(pdf_content.encode('latin-1', errors='ignore'))
                    else:
                        raise ValueError("Could not retrieve PDF content")
                except Exception as js_error:
                    raise ValueError(f"Could not download PDF: {js_error}")
            
            # Verify file
            if not filepath.exists() or filepath.stat().st_size == 0:
                raise ValueError("Downloaded file is empty or doesn't exist")
            
            return str(filepath)
        finally:
            if driver:
                driver.quit()
    
    def download_pdf(self, url: str, filename: str) -> str:
        """Download PDF file"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'identity',  # Don't compress, we want raw bytes
                'Referer': 'https://www.bnm.gov.my/banking-islamic-banking',
                'Connection': 'keep-alive'
            }
            
            session = requests.Session()
            
            # Use Selenium cookies if available
            if self.selenium_cookies:
                for cookie in self.selenium_cookies:
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', ''))
            else:
                # Fallback: visit main page to get cookies
                session.get('https://www.bnm.gov.my/banking-islamic-banking', headers=headers, timeout=30)
            
            # Now download the PDF
            response = session.get(url, headers=headers, timeout=60, stream=True, allow_redirects=True)
            
            # Debug: Check response status and headers
            print(f"  Response status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  Content-Length: {response.headers.get('Content-Length', 'unknown')}")
            
            response.raise_for_status()
            
            # Check response
            if len(response.content) == 0:
                print(f"  Response content length: 0")
                print(f"  Response URL (after redirects): {response.url}")
                raise ValueError("Downloaded file is empty")
            
            # Check if response is actually a PDF
            content_type = response.headers.get('Content-Type', '').lower()
            first_bytes = response.content[:4] if len(response.content) >= 4 else b''
            
            if first_bytes != b'%PDF':
                # Might be HTML error page or redirect
                if 'text/html' in content_type or first_bytes == b'<!DO' or first_bytes == b'<htm':
                    error_text = response.text[:500] if hasattr(response, 'text') else str(response.content[:500])
                    print(f"  Warning: Server returned HTML instead of PDF")
                    print(f"  Response preview: {error_text[:100]}...")
                    raise ValueError("Server returned HTML instead of PDF - URL might be incorrect or require authentication")
            
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                # Write content directly (already downloaded)
                f.write(response.content)
            
            # Verify file was written
            if filepath.stat().st_size == 0:
                raise ValueError("File was not written correctly")
            
            # Verify it's a valid PDF by checking magic number
            with open(filepath, 'rb') as f:
                first_bytes = f.read(4)
                if first_bytes != b'%PDF':
                    print(f"  Warning: Downloaded file doesn't appear to be a valid PDF (first bytes: {first_bytes})")
                    # Don't raise, just warn - some PDFs might have different headers
            
            return str(filepath)
        except Exception as e:
            # If regular download fails, try Selenium as fallback
            if "empty" in str(e).lower() or "HTML" in str(e):
                print(f"  Trying Selenium download as fallback...")
                try:
                    return self.download_pdf_selenium(url, filename)
                except Exception as selenium_error:
                    print(f"  Selenium download also failed: {selenium_error}")
            
            print(f"  Error details: {str(e)}")
            # Clean up empty file if it exists
            filepath = self.output_dir / filename
            if filepath.exists() and filepath.stat().st_size == 0:
                filepath.unlink()
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF"""
        text_content = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            return '\n\n'.join(text_content)
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """Split text into chunks for better embedding"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def store_in_qdrant(self, pdf_url: str, pdf_title: str, text_chunks: list, filepath: str, 
                       date: str = "", doc_type: str = ""):
        """Store PDF chunks in Qdrant vector database"""
        points = []
        
        for idx, chunk in enumerate(text_chunks):
            # Generate embedding
            embedding = self.embedding_model.encode(chunk).tolist()
            
            # Create unique ID
            chunk_id = hashlib.md5(f"{pdf_url}_{idx}".encode()).hexdigest()
            
            # Create point with metadata
            payload = {
                'pdf_url': pdf_url,
                'pdf_title': pdf_title,
                'chunk_index': idx,
                'chunk_text': chunk,
                'filepath': filepath,
                'total_chunks': len(text_chunks)
            }
            
            # Add optional metadata if available
            if date:
                payload['date'] = date
            if doc_type:
                payload['document_type'] = doc_type
            
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        # Insert points into Qdrant
        if points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"  Stored {len(points)} chunks in Qdrant")
    
    def sanitize_filename(self, url: str, title: str) -> str:
        """Create a safe filename from URL and title"""
        # Try to get filename from URL
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        
        # If no filename in URL, use title
        if not filename or not filename.endswith('.pdf'):
            # Clean title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{safe_title[:50]}.pdf"
        
        # Ensure it ends with .pdf
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        return filename
    
    def scrape_and_store(self, use_selenium: bool = None):
        """Main method to scrape PDFs and store in Qdrant"""
        print(f"Scraping PDFs from: {self.base_url}")
        
        # Try requests first, then Selenium if no tables found
        soup = self.get_page_content(self.base_url, use_selenium=False)
        
        # Debug: Save HTML for inspection
        debug_html_path = self.output_dir / "debug_page.html"
        with open(debug_html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        print(f"  Debug: Saved page HTML to {debug_html_path}")
        
        # Find all PDF links
        pdf_links = self.find_pdf_links(soup, self.base_url)
        print(f"Found {len(pdf_links)} PDF links")
        
        # If no links found and Selenium is available, try with Selenium
        if not pdf_links and SELENIUM_AVAILABLE and (use_selenium is None or use_selenium):
            print("\nNo PDFs found with requests. Trying with Selenium (JavaScript rendering)...")
            soup = self.get_page_content(self.base_url, use_selenium=True)
            pdf_links = self.find_pdf_links(soup, self.base_url)
            print(f"Found {len(pdf_links)} PDF links with Selenium")
        
        if not pdf_links:
            print("No PDF links found on the page")
            if not SELENIUM_AVAILABLE:
                print("Tip: The page might require JavaScript. Install Selenium: pip install selenium webdriver-manager")
            return
        
        # Process each PDF
        for idx, pdf_info in enumerate(tqdm(pdf_links, desc="Processing PDFs"), 1):
            pdf_url = pdf_info['url']
            pdf_title = pdf_info['text']
            date = pdf_info.get('date', '')
            doc_type = pdf_info.get('type', '')
            
            print(f"\n[{idx}/{len(pdf_links)}] Processing: {pdf_title}")
            if date:
                print(f"  Date: {date}")
            if doc_type:
                print(f"  Type: {doc_type}")
            print(f"  URL: {pdf_url}")
            
            try:
                # Download PDF
                filename = self.sanitize_filename(pdf_url, pdf_title)
                filepath = self.download_pdf(pdf_url, filename)
                print(f"  Downloaded: {filename}")
                
                # Extract text
                text = self.extract_text_from_pdf(filepath)
                if not text:
                    print(f"  Warning: No text extracted from {filename}")
                    continue
                
                # Chunk text
                chunks = self.chunk_text(text)
                print(f"  Extracted {len(chunks)} text chunks")
                
                # Store in Qdrant with metadata
                self.store_in_qdrant(pdf_url, pdf_title, chunks, filepath, date, doc_type)
                
            except Exception as e:
                print(f"  Error processing {pdf_url}: {e}")
                continue
        
        print(f"\n[SUCCESS] Scraping complete! PDFs stored in: {self.output_dir}")
        if self.qdrant_path:
            print(f"[SUCCESS] Vector database stored in: {self.qdrant_path}")
        else:
            print(f"[SUCCESS] Vector database stored in Qdrant server")
        print(f"[SUCCESS] Collection name: {self.collection_name}")


def main():
    """Main entry point"""
    import sys
    
    base_url = "https://www.bnm.gov.my/banking-islamic-banking"
    
    # Check for command line arguments
    use_server = "--server" in sys.argv or "-s" in sys.argv
    qdrant_url = "http://localhost:6333" if use_server else None
    
    if use_server:
        print("Using Qdrant server at http://localhost:6333")
        print("Make sure Qdrant server is running!")
    else:
        print("Using local file-based Qdrant database")
        print("To use Qdrant server instead, run: python scraper.py --server")
    
    scraper = BNMScraper(
        base_url=base_url,
        output_dir="pdfs",
        qdrant_url=qdrant_url
    )
    
    scraper.scrape_and_store()


if __name__ == "__main__":
    main()
