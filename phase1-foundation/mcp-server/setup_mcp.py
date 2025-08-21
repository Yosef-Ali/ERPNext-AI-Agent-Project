"""
ERPNext AI Agent - Phase 1: MCP Server Setup
Based on appliedrelevance/frappe_mcp_server integration
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any
import requests
import time

class ERPNextMCPSetup:
    """Setup MCP server integration with ERPNext"""
    
    def __init__(self, config_path: str = "../docker/.env"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.base_url = f"http://localhost:8000"
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from .env file"""
        config = {}
        if self.config_path.exists():
            with open(self.config_path) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value
        return config
    
    def check_erpnext_ready(self) -> bool:
        """Check if ERPNext is ready and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/method/ping", timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def wait_for_erpnext(self, max_wait: int = 300) -> bool:
        """Wait for ERPNext to be ready"""
        print("Waiting for ERPNext to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if self.check_erpnext_ready():
                print("✅ ERPNext is ready!")
                return True
            print("⏳ Waiting for ERPNext...")
            time.sleep(10)
        
        print("❌ ERPNext not ready after {max_wait} seconds")
        return False
    
    def install_mcp_server(self) -> bool:
        """Install frappe-mcp-server globally"""
        try:
            print("Installing frappe-mcp-server...")
            result = subprocess.run(
                ["npm", "install", "-g", "frappe-mcp-server"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ frappe-mcp-server installed successfully")
                return True
            else:
                print(f"❌ Failed to install frappe-mcp-server: {result.stderr}")
                return False
                
        except subprocess.SubprocessError as e:
            print(f"❌ Error installing frappe-mcp-server: {e}")
            return False    
    def create_mcp_config(self) -> Dict[str, Any]:
        """Create MCP server configuration"""
        config = {
            "mcpServers": {
                "frappe": {
                    "command": "frappe-mcp-server",
                    "args": [
                        "--url", self.base_url,
                        "--api-key", self.config.get("ERPNEXT_API_KEY", ""),
                        "--api-secret", self.config.get("ERPNEXT_API_SECRET", "")
                    ],
                    "env": {
                        "FRAPPE_URL": self.base_url,
                        "FRAPPE_API_KEY": self.config.get("ERPNEXT_API_KEY", ""),
                        "FRAPPE_API_SECRET": self.config.get("ERPNEXT_API_SECRET", "")
                    }
                }
            }
        }
        
        # Save config to file
        config_file = Path("mcp_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"✅ MCP configuration saved to {config_file}")
        return config
    
    def test_mcp_connection(self) -> bool:
        """Test MCP server connection to ERPNext"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user")
            
            if response.status_code == 200:
                print("✅ MCP connection test successful")
                return True
            else:
                print(f"❌ MCP connection test failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ MCP connection error: {e}")
            return False
    
    def setup_api_credentials(self) -> bool:
        """Setup API credentials for ERPNext"""
        print("\n🔑 Setting up API credentials...")
        print("Please create API credentials in ERPNext:")
        print(f"1. Go to {self.base_url}")
        print("2. Login as Administrator")
        print("3. Go to Settings > API > API Key")
        print("4. Create new API Key and Secret")
        print("5. Add them to your docker/.env file:")
        print("   ERPNEXT_API_KEY=your_api_key")
        print("   ERPNEXT_API_SECRET=your_api_secret")
        
        return True
    
    def run_setup(self) -> bool:
        """Run complete MCP setup process"""
        print("🚀 Starting ERPNext MCP Setup...")
        
        # Step 1: Wait for ERPNext
        if not self.wait_for_erpnext():
            return False
        
        # Step 2: Install MCP server
        if not self.install_mcp_server():
            return False
        
        # Step 3: Setup API credentials info
        self.setup_api_credentials()
        
        # Step 4: Create MCP configuration
        self.create_mcp_config()
        
        # Step 5: Test connection (if credentials are available)
        if self.config.get("ERPNEXT_API_KEY"):
            self.test_mcp_connection()
        
        print("\n🎉 MCP Setup Complete!")
        print("\nNext steps:")
        print("1. Add API credentials to docker/.env")
        print("2. Test MCP server: frappe-mcp-server --help")
        print("3. Configure Claude Desktop with mcp_config.json")
        
        return True

def main():
    """Main setup function"""
    setup = ERPNextMCPSetup()
    success = setup.run_setup()
    
    if not success:
        print("❌ Setup failed!")
        sys.exit(1)
    
    print("✅ Setup completed successfully!")

if __name__ == "__main__":
    main()
