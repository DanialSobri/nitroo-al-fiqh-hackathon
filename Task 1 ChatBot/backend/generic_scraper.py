"""Generic scraper class for custom sources"""
import sys
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# Add Web-Scraper to path
scraper_path = Path(__file__).parent.parent / "Web-Scraper"
if str(scraper_path) not in sys.path:
    sys.path.insert(0, str(scraper_path))

from scraper import BNMScraper, SELENIUM_AVAILABLE  # Use BNMScraper as base since it's the most generic

if SELENIUM_AVAILABLE:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager


class GenericScraper(BNMScraper):
    """Generic scraper that can handle any URL with PDF links"""
    
    def __init__(
        self,
        base_url: str,
        collection_name: str,
        output_dir: str = "pdfs",
        qdrant_path: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        scraping_strategy: str = "direct_links",
        form_selector: Optional[str] = None,
        form_button_selector: Optional[str] = None
    ):
        # Initialize parent with base_url and output_dir
        super().__init__(
            base_url=base_url,
            output_dir=output_dir,
            qdrant_path=qdrant_path,
            qdrant_url=qdrant_url
        )
        
        # Override collection name
        self.collection_name = collection_name
        self.scraping_strategy = scraping_strategy
        self.form_selector = form_selector
        self.form_button_selector = form_button_selector
        self._setup_collection()
    
    def find_pdf_links_from_form(self, soup: BeautifulSoup, base_url: str) -> list:
        """Find PDF links by submitting forms"""
        pdf_links = []
        
        if not self.form_selector:
            print("Warning: form_selector not provided for form-based scraping")
            return pdf_links
        
        # Find all forms matching the selector
        if self.form_selector.startswith('#'):
            # ID selector
            form_id = self.form_selector[1:]
            forms = soup.find_all('form', id=form_id)
        elif self.form_selector.startswith('.'):
            # Class selector
            class_name = self.form_selector[1:]
            forms = soup.find_all('form', class_=class_name)
        else:
            # Try as ID first, then class
            forms = soup.find_all('form', id=self.form_selector)
            if not forms:
                forms = soup.find_all('form', class_=self.form_selector)
        
        for form in forms:
            # Get form action URL
            form_action = form.get('action', '')
            if not form_action:
                continue
            
            # Build full URL
            if form_action.startswith('http'):
                form_url = form_action
            else:
                form_url = urljoin(base_url, form_action)
            
            # Get form method (default to GET)
            form_method = form.get('method', 'get').lower()
            
            # Try to extract title/name from form context
            title = "Untitled PDF"
            # Look for title in parent elements or nearby text
            parent = form.find_parent(['div', 'article', 'section', 'td', 'th'])
            if parent:
                # Try to find title in headings or links
                title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'a'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # Extract form data
            form_data = {}
            inputs = form.find_all(['input', 'select', 'textarea'])
            for inp in inputs:
                name = inp.get('name')
                if name:
                    value = inp.get('value', '')
                    if inp.name == 'select':
                        selected = inp.find('option', selected=True)
                        if selected:
                            value = selected.get('value', selected.get_text(strip=True))
                    form_data[name] = value
            
            pdf_links.append({
                'url': form_url,
                'text': title,
                'date': '',
                'type': '',
                'form_method': form_method,
                'form_data': form_data,
                'form_element': form
            })
        
        return pdf_links
    
    def find_pdf_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """Find PDF links based on scraping strategy"""
        if self.scraping_strategy == "form_based":
            return self.find_pdf_links_from_form(soup, base_url)
        elif self.scraping_strategy == "table_based":
            return self.find_pdf_links_from_table(soup, base_url)
        else:
            # Default: direct links
            return self.find_pdf_links_from_table(soup, base_url)
    
    def download_pdf_from_form(self, form_info: dict, filename: str) -> str:
        """Download PDF by submitting a form"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required for form-based downloads")
        
        form_url = form_info['url']
        form_method = form_info.get('form_method', 'get').lower()
        form_data = form_info.get('form_data', {})
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Set download preferences
        prefs = {
            "download.default_directory": str(self.output_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Navigate to the page with the form
            page_url = self.base_url
            driver.get(page_url)
            time.sleep(2)
            
            # Find and submit the form
            if self.form_selector:
                if self.form_selector.startswith('#'):
                    form = driver.find_element(By.ID, self.form_selector[1:])
                elif self.form_selector.startswith('.'):
                    form = driver.find_element(By.CLASS_NAME, self.form_selector[1:])
                else:
                    form = driver.find_element(By.ID, self.form_selector)
                
                # Fill form fields if needed
                for name, value in form_data.items():
                    try:
                        field = form.find_element(By.NAME, name)
                        if field.tag_name == 'select':
                            from selenium.webdriver.support.ui import Select
                            select = Select(field)
                            select.select_by_value(value)
                        else:
                            field.clear()
                            field.send_keys(value)
                    except:
                        pass  # Field might not exist
                
                # Submit form
                if self.form_button_selector:
                    if self.form_button_selector.startswith('#'):
                        button = driver.find_element(By.ID, self.form_button_selector[1:])
                    elif self.form_button_selector.startswith('.'):
                        button = driver.find_element(By.CLASS_NAME, self.form_button_selector[1:])
                    else:
                        button = form.find_element(By.CSS_SELECTOR, self.form_button_selector)
                    button.click()
                else:
                    form.submit()
                
                # Wait for download or page change
                time.sleep(3)
                
                # Check if PDF was downloaded
                import time as time_module
                max_wait = 10
                waited = 0
                while waited < max_wait:
                    downloaded_files = list(self.output_dir.glob("*.pdf"))
                    if downloaded_files:
                        # Find the most recently downloaded file
                        latest_file = max(downloaded_files, key=lambda p: p.stat().st_mtime)
                        if latest_file.stat().st_mtime > time_module.time() - 10:
                            # Rename to desired filename
                            target_path = self.output_dir / filename
                            if latest_file != target_path:
                                latest_file.rename(target_path)
                            return str(target_path)
                    time_module.sleep(1)
                    waited += 1
                
                # If download didn't work, try to get PDF from response
                # Check if current URL is a PDF
                current_url = driver.current_url
                if '.pdf' in current_url.lower() or driver.page_source.startswith('%PDF'):
                    # Save the PDF content
                    filepath = self.output_dir / filename
                    if driver.page_source.startswith('%PDF'):
                        with open(filepath, 'wb') as f:
                            f.write(driver.page_source.encode('latin-1', errors='ignore'))
                    else:
                        # Download from current URL
                        import requests
                        response = requests.get(current_url)
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                    return str(filepath)
                
                raise ValueError("Could not download PDF from form")
            else:
                raise ValueError("Form selector not provided")
                
        finally:
            if driver:
                driver.quit()
    
    def scrape_and_store(self, use_selenium: bool = None):
        """Main method to scrape PDFs and store in Qdrant"""
        print(f"Scraping PDFs from: {self.base_url} (Strategy: {self.scraping_strategy})")
        
        # For form-based scraping, always use Selenium
        if self.scraping_strategy == "form_based":
            use_selenium = True
        
        # Get page content
        soup = self.get_page_content(self.base_url, use_selenium=use_selenium)
        
        # Find PDF links based on strategy
        pdf_links = self.find_pdf_links(soup, self.base_url)
        print(f"Found {len(pdf_links)} PDF links")
        
        if not pdf_links:
            print("No PDF links found on the page")
            return
        
        # Process each PDF
        for idx, pdf_info in enumerate(pdf_links, 1):
            try:
                print(f"\n[{idx}/{len(pdf_links)}] Processing: {pdf_info.get('text', 'Unknown')}")
                
                # Generate filename
                title = pdf_info.get('text', 'Untitled')
                url = pdf_info.get('url', '')
                filename = self.sanitize_filename(url, title)
                
                # Download PDF
                if self.scraping_strategy == "form_based":
                    filepath = self.download_pdf_from_form(pdf_info, filename)
                else:
                    filepath = self.download_pdf(url, filename)
                
                # Extract text and store
                text_chunks = self.extract_text_from_pdf(filepath)
                if text_chunks:
                    self.store_in_qdrant(
                        pdf_url=url,
                        pdf_title=title,
                        text_chunks=text_chunks,
                        filepath=filepath,
                        date=pdf_info.get('date', ''),
                        doc_type=pdf_info.get('type', '')
                    )
                    print(f"  ✓ Stored {len(text_chunks)} chunks")
                else:
                    print(f"  ⚠ No text extracted from PDF")
                    
            except Exception as e:
                print(f"  ✗ Error processing PDF: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n[SUCCESS] Collection name: {self.collection_name}")