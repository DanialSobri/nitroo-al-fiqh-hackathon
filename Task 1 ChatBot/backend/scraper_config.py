"""Scraper configuration management for custom sources"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

CONFIG_FILE = Path(__file__).parent / "scraper_sources.json"

# Default sources
DEFAULT_SOURCES = {
    "bnm": {
        "id": "bnm",
        "name": "Bank Negara Malaysia",
        "url": "https://www.bnm.gov.my/banking-islamic-banking",
        "collection_name": "bnm_pdfs",
        "output_dir": "pdfs/bnm",
        "type": "default",
        "scraping_strategy": "direct_links",
        "form_selector": None,
        "form_button_selector": None,
        "created_at": None
    },
    "iifa": {
        "id": "iifa",
        "name": "IIFA Resolutions",
        "url": "https://iifa-aifi.org/en/resolutions",
        "collection_name": "iifa_resolutions",
        "output_dir": "pdfs/iifa",
        "type": "default",
        "scraping_strategy": "direct_links",
        "form_selector": None,
        "form_button_selector": None,
        "created_at": None
    },
    "sc": {
        "id": "sc",
        "name": "Securities Commission",
        "url": "https://www.sc.com.my/development/icm/shariah/resolutions-of-the-shariah-advisory-council-of-the-sc",
        "collection_name": "sc_resolutions",
        "output_dir": "pdfs/sc",
        "type": "default",
        "scraping_strategy": "direct_links",
        "form_selector": None,
        "form_button_selector": None,
        "created_at": None
    }
}


def load_sources() -> Dict:
    """Load scraper sources from config file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Merge with defaults to ensure all default sources exist
                merged = {**DEFAULT_SOURCES, **data.get("custom_sources", {})}
                return {
                    "default_sources": DEFAULT_SOURCES,
                    "custom_sources": {k: v for k, v in merged.items() if k not in DEFAULT_SOURCES},
                    "all_sources": merged
                }
        except Exception as e:
            print(f"Error loading scraper sources: {e}")
            return {
                "default_sources": DEFAULT_SOURCES,
                "custom_sources": {},
                "all_sources": DEFAULT_SOURCES
            }
    else:
        # Create initial config file
        save_sources({"custom_sources": {}})
        return {
            "default_sources": DEFAULT_SOURCES,
            "custom_sources": {},
            "all_sources": DEFAULT_SOURCES
        }


def save_sources(config: Dict):
    """Save scraper sources to config file"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def add_custom_source(
    name: str,
    url: str,
    collection_name: str,
    output_dir: Optional[str] = None,
    scraping_strategy: str = "direct_links",
    form_selector: Optional[str] = None,
    form_button_selector: Optional[str] = None
) -> Dict:
    """Add a new custom scraper source"""
    config = load_sources()
    
    # Generate ID from collection name (sanitize)
    source_id = collection_name.lower().replace(' ', '_').replace('-', '_')
    
    # Ensure unique ID
    if source_id in config["all_sources"]:
        counter = 1
        original_id = source_id
        while source_id in config["all_sources"]:
            source_id = f"{original_id}_{counter}"
            counter += 1
    
    # Default output directory if not provided
    if not output_dir:
        output_dir = f"pdfs/{source_id}"
    
    new_source = {
        "id": source_id,
        "name": name,
        "url": url,
        "collection_name": collection_name,
        "output_dir": output_dir,
        "type": "custom",
        "scraping_strategy": scraping_strategy,  # "direct_links", "form_based", "table_based"
        "form_selector": form_selector,  # CSS selector for form (e.g., "#download-file")
        "form_button_selector": form_button_selector,  # CSS selector for submit button (e.g., "#muat-turun")
        "created_at": datetime.now().isoformat()
    }
    
    config["custom_sources"][source_id] = new_source
    config["all_sources"][source_id] = new_source
    
    save_sources({
        "custom_sources": config["custom_sources"]
    })
    
    return new_source


def update_custom_source(
    source_id: str,
    name: Optional[str] = None,
    url: Optional[str] = None,
    collection_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    scraping_strategy: Optional[str] = None,
    form_selector: Optional[str] = None,
    form_button_selector: Optional[str] = None
) -> Optional[Dict]:
    """Update an existing custom scraper source"""
    config = load_sources()
    
    if source_id in DEFAULT_SOURCES:
        return None  # Cannot update default sources
    
    if source_id not in config["custom_sources"]:
        return None  # Source not found
    
    source = config["custom_sources"][source_id].copy()
    
    # Update only provided fields
    if name is not None:
        source["name"] = name
    if url is not None:
        source["url"] = url
    if collection_name is not None:
        source["collection_name"] = collection_name
    if output_dir is not None:
        source["output_dir"] = output_dir
    if scraping_strategy is not None:
        source["scraping_strategy"] = scraping_strategy
    if form_selector is not None:
        source["form_selector"] = form_selector
    if form_button_selector is not None:
        source["form_button_selector"] = form_button_selector
    
    # Update timestamp
    source["updated_at"] = datetime.now().isoformat()
    
    config["custom_sources"][source_id] = source
    config["all_sources"][source_id] = source
    
    save_sources({
        "custom_sources": config["custom_sources"]
    })
    
    return source


def delete_custom_source(source_id: str) -> bool:
    """Delete a custom scraper source"""
    config = load_sources()
    
    if source_id in DEFAULT_SOURCES:
        return False  # Cannot delete default sources
    
    if source_id in config["custom_sources"]:
        del config["custom_sources"][source_id]
        if source_id in config["all_sources"]:
            del config["all_sources"][source_id]
        
        save_sources({
            "custom_sources": config["custom_sources"]
        })
        return True
    
    return False


def get_source(source_id: str) -> Optional[Dict]:
    """Get a specific source by ID"""
    config = load_sources()
    return config["all_sources"].get(source_id)


def get_all_sources() -> List[Dict]:
    """Get all sources (default + custom)"""
    config = load_sources()
    return list(config["all_sources"].values())
