#!/usr/bin/env python3
"""
ERPNext Real Data Connector
Establishes connection to existing ERPNext instance and provides data access
"""

import os
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPNextConnector:
    """Real connection to existing ERPNext instance"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.api_key = None
        self.api_secret = None
        self.connected = False
        
    def discover_erpnext_instances(self) -> List[Dict[str, Any]]:
        """Discover running ERPNext instances on the system"""
        instances = []
        
        # Check common ports
        ports = [8000, 8001, 8080, 9000]
        for port in ports:
            try:
                url = f"http://localhost:{port}"
                response = requests.get(f"{url}/api/method/ping", timeout=5)
                if response.status_code == 200:
                    instances.append({
                        "url": url,
                        "status": "active",
                        "response": response.json()
                    })
            except:
                continue
                
        # Check for bench processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'frappe' in result.stdout or 'bench' in result.stdout:
                logger.info("Found Frappe/Bench processes running")
        except:
            pass
            
        return instances
    
    def connect_to_existing_bench(self) -> bool:
        """Connect to existing bench installation"""
        bench_paths = [
            "/Users/mekdesyared/frappe-bench",
            "/Users/mekdesyared/erpnext-mcp-builder/bench-setup/frappe-bench"
        ]
        
        for bench_path in bench_paths:
            if Path(bench_path).exists():
                try:
                    # Get site list
                    result = subprocess.run([
                        'bench', '--site', 'all', 'list-apps'
                    ], cwd=bench_path, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        logger.info(f"Found active bench at: {bench_path}")
                        return self._setup_bench_connection(bench_path)
                except Exception as e:
                    logger.debug(f"Bench at {bench_path} not responsive: {e}")
                    continue
                    
        return False
    
    def _setup_bench_connection(self, bench_path: str) -> bool:
        """Setup connection via bench CLI"""
        try:
            # Get sites
            result = subprocess.run([
                'find', f"{bench_path}/sites", '-name', 'site_config.json', '-not', '-path', '*/assets/*'
            ], capture_output=True, text=True)
            
            site_configs = result.stdout.strip().split('\n')
            for config_path in site_configs:
                if config_path and Path(config_path).exists():
                    site_dir = Path(config_path).parent
                    site_name = site_dir.name
                    
                    # Try to get site info
                    logger.info(f"Found site: {site_name}")
                    self.bench_path = bench_path
                    self.site_name = site_name
                    return True
                    
        except Exception as e:
            logger.error(f"Error setting up bench connection: {e}")
            
        return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to ERPNext"""
        status = {
            "connected": False,
            "method": None,
            "details": {},
            "instances_found": []
        }
        
        # 1. Try to discover running instances
        instances = self.discover_erpnext_instances()
        status["instances_found"] = instances
        
        if instances:
            # Try connecting to first instance
            instance = instances[0]
            self.base_url = instance["url"]
            try:
                # Test basic API access
                response = self.session.get(f"{self.base_url}/api/method/ping")
                if response.status_code == 200:
                    status["connected"] = True
                    status["method"] = "api"
                    status["details"] = instance
                    self.connected = True
                    
            except Exception as e:
                status["details"]["error"] = str(e)
        
        # 2. Try bench connection if API failed
        if not status["connected"]:
            if self.connect_to_existing_bench():
                status["connected"] = True
                status["method"] = "bench"
                status["details"] = {
                    "bench_path": getattr(self, 'bench_path', None),
                    "site_name": getattr(self, 'site_name', None)
                }
                self.connected = True
        
        return status
    
    def get_doctypes(self) -> List[Dict[str, Any]]:
        """Get list of all DocTypes"""
        if not self.connected:
            return []
            
        try:
            if hasattr(self, 'bench_path'):
                # Use bench CLI
                result = subprocess.run([
                    'bench', '--site', self.site_name, 'console'
                ], input='frappe.get_all("DocType", fields=["name", "module", "custom", "is_virtual"])',
                cwd=self.bench_path, capture_output=True, text=True)
                
                # Parse result (simplified)
                return []  # Will implement proper parsing
            else:
                # Use API
                response = self.session.get(f"{self.base_url}/api/resource/DocType")
                if response.status_code == 200:
                    return response.json().get('data', [])
                    
        except Exception as e:
            logger.error(f"Error getting DocTypes: {e}")
            
        return []
    
    def get_doctype_schema(self, doctype: str) -> Dict[str, Any]:
        """Get schema for a specific DocType"""
        try:
            if hasattr(self, 'bench_path'):
                # Use bench CLI to get doctype metadata
                cmd = f'frappe.get_doc("DocType", "{doctype}").as_dict()'
                result = subprocess.run([
                    'bench', '--site', self.site_name, 'console'
                ], input=cmd, cwd=self.bench_path, capture_output=True, text=True)
                
                # Will parse the result properly
                return {}
            else:
                # Use API
                response = self.session.get(f"{self.base_url}/api/resource/DocType/{doctype}")
                if response.status_code == 200:
                    return response.json().get('data', {})
                    
        except Exception as e:
            logger.error(f"Error getting DocType schema for {doctype}: {e}")
            
        return {}
    
    def get_sample_documents(self, doctype: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample documents from a DocType"""
        try:
            if hasattr(self, 'bench_path'):
                # Use bench CLI
                cmd = f'frappe.get_all("{doctype}", limit={limit})'
                result = subprocess.run([
                    'bench', '--site', self.site_name, 'console'  
                ], input=cmd, cwd=self.bench_path, capture_output=True, text=True)
                
                return []  # Will parse properly
            else:
                # Use API
                response = self.session.get(f"{self.base_url}/api/resource/{doctype}?limit={limit}")
                if response.status_code == 200:
                    return response.json().get('data', [])
                    
        except Exception as e:
            logger.error(f"Error getting sample documents for {doctype}: {e}")
            
        return []

def main():
    """Test the connector"""
    connector = ERPNextConnector()
    
    print("🔍 Testing ERPNext Connection...")
    status = connector.test_connection()
    
    print(f"Connection Status: {'✅ Connected' if status['connected'] else '❌ Not Connected'}")
    if status['connected']:
        print(f"Method: {status['method']}")
        print(f"Details: {status['details']}")
        
        # Test getting DocTypes
        print("\n📋 Testing DocType Access...")
        doctypes = connector.get_doctypes()
        print(f"Found {len(doctypes)} DocTypes")
        
    else:
        print("Available instances:", status['instances_found'])

if __name__ == "__main__":
    main()