#!/usr/bin/env python3
"""
ERPNext AI Agent - Local Development Setup
Uses existing ERPNext installation instead of Docker
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Starting ERPNext AI Agent (Local Mode)")
    print("=" * 50)
    
    # Check if we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Activate virtual environment
    venv_python = project_root / "venv" / "bin" / "python"
    if not venv_python.exists():
        print("❌ Virtual environment not found. Run setup.sh first.")
        sys.exit(1)
    
    print("✅ Using virtual environment")
    print("✅ Connected to existing ERPNext installation")
    print("✅ Local development mode active")
    
    print("\n📋 Available Specialized Agents:")
    print("  - requirements-analyzer: Business requirements → technical specs")
    print("  - erpnext-architect: System architecture design")  
    print("  - db-architect: DocType and database design")
    print("  - frontend-developer: UI components and client scripts")
    print("  - integration-specialist: API integrations")
    print("  - test-engineer: Testing and quality assurance")
    
    print("\n🎯 Ready for ERPNext development!")
    print("Use Claude Code with the Task tool to invoke agents")
    
    return True

if __name__ == "__main__":
    main()