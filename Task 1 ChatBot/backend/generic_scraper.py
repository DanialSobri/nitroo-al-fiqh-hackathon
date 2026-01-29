"""Generic scraper class for custom sources"""
import sys
import time
import requests
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
    
    def find_pdf_links_direct(self, soup: BeautifulSoup, base_url: str) -> list:
        """Find PDF links directly from all links on the page"""
        pdf_links = []
        
        # Find all links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if not href or href.strip() in ['', '#', 'about:blank', 'javascript:void(0)']:
                continue
            
            # Skip invalid URLs
            if href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            href_lower = href.lower()
            
            # Check if it's a PDF link by extension
            is_pdf_by_extension = (href_lower.endswith('.pdf') or '.pdf' in href_lower)
            
            # Check if link text suggests it's a PDF
            link_text = link.get_text(strip=True).lower()
            is_pdf_by_text = ('pdf' in link_text or 'muat turun' in link_text or 'download' in link_text)
            
            # Check content type
            is_pdf_by_type = 'application/pdf' in link.get('type', '').lower()
            
            # Check if it's likely a PDF (has download attribute or specific classes)
            has_download_attr = link.get('download', '').lower().endswith('.pdf')
            has_pdf_class = any('pdf' in str(c).lower() for c in link.get('class', []))
            
            # Exclude non-PDF file types
            excluded_extensions = ['.html', '.htm', '.aspx', '.php', '.jsp', '.xlsx', '.xls', '.doc', '.docx', '.zip', '.rar', '.txt', '.xml', '.jpg', '.jpeg', '.png', '.gif']
            is_excluded = any(href_lower.endswith(ext) for ext in excluded_extensions)
            
            # Consider it a PDF if:
            # 1. Has .pdf extension, OR
            # 2. Link text suggests PDF and doesn't have excluded extension, OR
            # 3. Has PDF content type, OR
            # 4. Has download attribute or PDF class
            if (is_pdf_by_extension or 
                (is_pdf_by_text and not is_excluded and not any(ext in href_lower for ext in excluded_extensions)) or
                is_pdf_by_type or 
                has_download_attr or 
                has_pdf_class):
                
                try:
                    full_url = urljoin(base_url, href)
                    # Skip invalid URLs
                    if not full_url.startswith(('http://', 'https://')):
                        continue
                    
                    # Skip if already in list
                    if not any(p['url'] == full_url for p in pdf_links):
                        link_text_display = link.get_text(strip=True) or link.get('title', '') or 'Untitled PDF'
                        pdf_links.append({
                            'url': full_url,
                            'text': link_text_display,
                            'date': '',
                            'type': ''
                        })
                except Exception as e:
                    print(f"  Warning: Invalid URL {href}: {e}")
                    continue
        
        # Also check for iframes with PDFs (skip about:blank)
        iframes = soup.find_all('iframe', src=True)
        for iframe in iframes:
            src = iframe.get('src', '')
            if not src or src.strip() in ['', 'about:blank']:
                continue
            
            if '.pdf' in src.lower() or 'application/pdf' in iframe.get('type', '').lower():
                try:
                    full_url = urljoin(base_url, src)
                    if full_url.startswith(('http://', 'https://')) and not any(p['url'] == full_url for p in pdf_links):
                        pdf_links.append({
                            'url': full_url,
                            'text': iframe.get('title', '') or 'Embedded PDF',
                            'date': '',
                            'type': ''
                        })
                except Exception:
                    continue
        
        # Check for embed/object tags
        embeds = soup.find_all(['embed', 'object'], src=True)
        for embed in embeds:
            src = embed.get('src', '') or embed.get('data', '')
            if not src or src.strip() in ['', 'about:blank']:
                continue
            
            if src and ('.pdf' in src.lower() or 'application/pdf' in embed.get('type', '').lower()):
                try:
                    full_url = urljoin(base_url, src)
                    if full_url.startswith(('http://', 'https://')) and not any(p['url'] == full_url for p in pdf_links):
                        pdf_links.append({
                            'url': full_url,
                            'text': embed.get('title', '') or 'Embedded PDF',
                            'date': '',
                            'type': ''
                        })
                except Exception:
                    continue
        
        return pdf_links
    
    def find_pdf_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """Find PDF links based on scraping strategy"""
        if self.scraping_strategy == "form_based":
            return self.find_pdf_links_from_form(soup, base_url)
        elif self.scraping_strategy == "table_based":
            return self.find_pdf_links_from_table(soup, base_url)
        else:
            # Default: direct links - search all links, iframes, embeds
            return self.find_pdf_links_direct(soup, base_url)
    
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
        
        # First, check if the URL itself serves a PDF (before parsing HTML)
        print("Checking if URL serves PDF directly...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*'
            }
            response = requests.head(self.base_url, headers=headers, timeout=10, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' in content_type:
                print(f"  ✓ URL directly serves PDF! Content-Type: {content_type}")
                pdf_links = [{
                    'url': self.base_url,
                    'text': 'PDF Document',
                    'date': '',
                    'type': ''
                }]
            else:
                print(f"  URL serves: {content_type}")
                # Also check first bytes to see if it's actually a PDF
                try:
                    response_get = requests.get(self.base_url, headers=headers, timeout=10, stream=True, allow_redirects=True)
                    first_bytes = response_get.content[:4] if len(response_get.content) >= 4 else b''
                    if first_bytes == b'%PDF':
                        print(f"  ✓ URL serves PDF (detected by magic bytes)!")
                        pdf_links = [{
                            'url': self.base_url,
                            'text': 'PDF Document',
                            'date': '',
                            'type': ''
                        }]
                    else:
                        pdf_links = []
                except:
                    pdf_links = []
        except Exception as e:
            print(f"  Could not check URL directly: {e}")
            pdf_links = []
        
        # If URL doesn't serve PDF directly, parse HTML
        if not pdf_links:
            # Get page content
            soup = self.get_page_content(self.base_url, use_selenium=use_selenium)
            
            # Find PDF links based on strategy
            pdf_links = self.find_pdf_links(soup, self.base_url)
            print(f"Found {len(pdf_links)} PDF links")
            
            # If no PDFs found and not using Selenium, try with Selenium (for JS-rendered content)
            if not pdf_links and not use_selenium and SELENIUM_AVAILABLE:
                print("No PDFs found with basic scraping. Trying with Selenium (JavaScript rendering)...")
                soup = self.get_page_content(self.base_url, use_selenium=True)
                pdf_links = self.find_pdf_links(soup, self.base_url)
                print(f"Found {len(pdf_links)} PDF links with Selenium")
            
            # Save HTML for debugging if no links found
            if not pdf_links:
                debug_file = self.output_dir / "debug_page.html"
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(str(soup.prettify()))
                    print(f"  Saved page HTML to: {debug_file} for inspection")
                except:
                    pass
        
        # Check if the page itself serves a PDF (some sites serve PDFs without .pdf extension)
        if not pdf_links:
            print("No PDF links found. Checking if page URL itself serves a PDF...")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/octet-stream,*/*'
                }
                response = requests.head(self.base_url, headers=headers, timeout=10, allow_redirects=True)
                content_type = response.headers.get('Content-Type', '').lower()
                if 'application/pdf' in content_type:
                    print(f"  Page itself serves PDF! Content-Type: {content_type}")
                    pdf_links.append({
                        'url': self.base_url,
                        'text': soup.title.string if soup.title else 'Page PDF',
                        'date': '',
                        'type': ''
                    })
            except Exception as e:
                print(f"  Page is not a PDF: {e}")
        
        # Check for common PDF URL patterns (e.g., adding ?download or /pdf to URL)
        if not pdf_links:
            print("Trying common PDF URL patterns...")
            base_url_clean = self.base_url.rstrip('?').rstrip('/')
            pdf_url_variants = [
                f"{base_url_clean}.pdf",
                f"{base_url_clean}/download",
                f"{base_url_clean}?download=1",
                f"{base_url_clean}?format=pdf",
                f"{base_url_clean}/pdf",
            ]
            
            for variant_url in pdf_url_variants:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/pdf,application/octet-stream,*/*'
                    }
                    response = requests.head(variant_url, headers=headers, timeout=5, allow_redirects=True)
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'application/pdf' in content_type:
                        pdf_links.append({
                            'url': variant_url,
                            'text': 'PDF Document',
                            'date': '',
                            'type': ''
                        })
                        print(f"  Found PDF via URL variant: {variant_url}")
                        break
                except:
                    continue
        
        # Look for download buttons/links with common patterns
        if not pdf_links:
            print("Checking for download buttons and links...")
            download_keywords = ['muat turun', 'download', 'pdf', 'unduh', 'muatnaik', 'muat', 'turun']
            all_links = soup.find_all('a', href=True)
            buttons = soup.find_all(['button', 'input'], type='button') + soup.find_all(['button', 'input'], type='submit')
            
            # Check all links
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Skip invalid URLs
                if not href or href.strip() in ['', '#', 'about:blank', 'javascript:void(0)']:
                    continue
                
                # Check if link text suggests download
                if any(keyword in text for keyword in download_keywords):
                    try:
                        full_url = urljoin(self.base_url, href)
                        if full_url.startswith(('http://', 'https://')):
                            # Verify it's actually a PDF by checking headers
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'Accept': 'application/pdf,application/octet-stream,*/*'
                            }
                            try:
                                response = requests.head(full_url, headers=headers, timeout=10, allow_redirects=True)
                                content_type = response.headers.get('Content-Type', '').lower()
                                if 'application/pdf' in content_type or 'pdf' in content_type:
                                    pdf_links.append({
                                        'url': full_url,
                                        'text': link.get_text(strip=True) or 'Download PDF',
                                        'date': '',
                                        'type': ''
                                    })
                                    print(f"  Found PDF via download link: {full_url}")
                            except:
                                # Try GET request if HEAD fails
                                try:
                                    response = requests.get(full_url, headers=headers, timeout=10, stream=True, allow_redirects=True)
                                    content_type = response.headers.get('Content-Type', '').lower()
                                    first_bytes = response.content[:4] if len(response.content) >= 4 else b''
                                    if first_bytes == b'%PDF' or 'application/pdf' in content_type:
                                        pdf_links.append({
                                            'url': full_url,
                                            'text': link.get_text(strip=True) or 'Download PDF',
                                            'date': '',
                                            'type': ''
                                        })
                                        print(f"  Found PDF via download link (GET): {full_url}")
                                except:
                                    pass
                    except:
                        pass
        
        if not pdf_links:
            print("\n" + "="*60)
            print("No PDF links found on the page")
            print("="*60)
            print("Debug: Page title:", soup.title.string if soup.title else "No title")
            print("Debug: Total links on page:", len(soup.find_all('a', href=True)))
            print("Debug: Total buttons on page:", len(soup.find_all(['button', 'input'])))
            
            # Print first few links for debugging
            all_links = soup.find_all('a', href=True)[:10]
            print("Debug: Sample links:")
            if all_links:
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)[:50]
                    print(f"  - {href[:80]} ({text})")
            else:
                print("  - No links found on page")
            
            # Print page structure
            print("Debug: Page structure:")
            print(f"  - Has body: {soup.body is not None}")
            if soup.body:
                body_text = soup.body.get_text()
                print(f"  - Body text length: {len(body_text)}")
                print(f"  - Body text preview: {body_text[:200]}")
                
                # Check for common PDF indicators in page content
                if 'P.U.' in body_text or 'FATWA' in body_text or 'WARTA KERAJAAN' in body_text:
                    print("\n  ⚠ Page appears to contain fatwa/gazette content")
                    print("  ⚠ Note: This page displays content directly, not as a PDF link")
                    print("  💡 Suggestion: This website may:")
                    print("     - Display fatwa content on the page (not as downloadable PDF)")
                    print("     - Require a different URL pattern to access PDFs")
                    print("     - Have PDFs available at a different endpoint")
                    print("     - Need form submission to generate/download PDFs")
                    print("\n  💡 Try:")
                    print("     - Check the website's main page for PDF download links")
                    print("     - Look for a 'Download PDF' or 'Muat Turun PDF' button")
                    print("     - Check if PDFs are available via a different URL structure")
                    print("     - Consider using 'form_based' strategy if there's a download form")
            
            # Save HTML for manual inspection
            debug_file = self.output_dir / "debug_page.html"
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(str(soup.prettify()))
                print(f"\n  📄 Saved page HTML to: {debug_file}")
                print("     You can open this file in a browser to inspect the page structure")
            except Exception as e:
                print(f"  ⚠ Could not save debug file: {e}")
            
            print("="*60 + "\n")
            return
        
        # Process each PDF
        for idx, pdf_info in enumerate(pdf_links, 1):
            try:
                print(f"\n[{idx}/{len(pdf_links)}] Processing: {pdf_info.get('text', 'Unknown')}")
                
                # Generate filename
                title = pdf_info.get('text', 'Untitled')
                url = pdf_info.get('url', '')
                
                # Verify URL is valid before processing
                if not url or url.strip() in ['', 'about:blank', '#']:
                    print(f"  ⚠ Skipping invalid URL: {url}")
                    continue
                
                if not url.startswith(('http://', 'https://')):
                    print(f"  ⚠ Skipping non-HTTP URL: {url}")
                    continue
                
                filename = self.sanitize_filename(url, title)
                
                # Download PDF
                if self.scraping_strategy == "form_based":
                    filepath = self.download_pdf_from_form(pdf_info, filename)
                else:
                    # Verify URL is valid before downloading
                    if url.startswith(('http://', 'https://')):
                        filepath = self.download_pdf(url, filename)
                    else:
                        print(f"  ⚠ Skipping invalid URL: {url}")
                        continue
                
                # Extract text with page numbers and store
                page_texts = self.extract_text_with_pages(filepath)
                if page_texts:
                    # Chunk text with page tracking
                    chunked_data = self.chunk_text_with_pages(page_texts)
                    if chunked_data:
                        self.store_in_qdrant(
                            pdf_url=url,
                            pdf_title=title,
                            text_chunks=chunked_data,  # Pass list of dicts with 'text' and 'page_number'
                            filepath=filepath,
                            date=pdf_info.get('date', ''),
                            doc_type=pdf_info.get('type', '')
                        )
                        print(f"  ✓ Stored {len(chunked_data)} chunks with page numbers")
                    else:
                        print(f"  ⚠ No chunks created from PDF")
                else:
                    print(f"  ⚠ No text extracted from PDF")
                    
            except Exception as e:
                print(f"  ✗ Error processing PDF: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n[SUCCESS] Collection name: {self.collection_name}")