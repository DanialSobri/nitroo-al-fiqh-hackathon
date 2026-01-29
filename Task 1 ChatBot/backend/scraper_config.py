"""Scraper configuration management for custom sources"""
# This module now uses SQLite database via database.py
# Keeping this file for backward compatibility and easy imports

from typing import List, Dict, Optional
from database import (
    get_all_sources as db_get_all_sources,
    get_source as db_get_source,
    add_custom_source as db_add_custom_source,
    update_custom_source as db_update_custom_source,
    delete_custom_source as db_delete_custom_source
)


def get_all_sources() -> List[Dict]:
    """Get all sources (default + custom)"""
    return db_get_all_sources()


def get_source(source_id: str) -> Optional[Dict]:
    """Get a specific source by ID"""
    return db_get_source(source_id)


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
    source_data = {
        'name': name,
        'url': url,
        'collection_name': collection_name,
        'output_dir': output_dir,
        'scraping_strategy': scraping_strategy,
        'form_selector': form_selector,
        'form_button_selector': form_button_selector
    }
    
    # Generate ID from collection name (sanitize)
    source_id = collection_name.lower().replace(' ', '_').replace('-', '_')
    
    # Check if ID already exists
    existing = db_get_source(source_id)
    if existing:
        # Ensure unique ID
        counter = 1
        original_id = source_id
        while existing:
            source_id = f"{original_id}_{counter}"
            existing = db_get_source(source_id)
            counter += 1
    
    source_data['id'] = source_id
    
    # Default output directory if not provided
    if not output_dir:
        source_data['output_dir'] = f"pdfs/{source_id}"
    
    return db_add_custom_source(source_data)


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
    # Check if it's a default source (cannot update)
    existing = db_get_source(source_id)
    if not existing or existing.get('type') == 'default':
        return None
    
    # Build update dict with only provided fields
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if url is not None:
        update_data['url'] = url
    if collection_name is not None:
        update_data['collection_name'] = collection_name
    if output_dir is not None:
        update_data['output_dir'] = output_dir
    if scraping_strategy is not None:
        update_data['scraping_strategy'] = scraping_strategy
    if form_selector is not None:
        update_data['form_selector'] = form_selector
    if form_button_selector is not None:
        update_data['form_button_selector'] = form_button_selector
    
    if not update_data:
        return existing
    
    # Merge with existing data
    update_data = {**existing, **update_data}
    
    return db_update_custom_source(source_id, update_data)


def delete_custom_source(source_id: str) -> bool:
    """Delete a custom scraper source"""
    return db_delete_custom_source(source_id)
