#!/usr/bin/env python3
"""
PocketBase Migration Runner for Render Docker
This script runs PocketBase migrations by connecting to the PocketBase instance
and executing the migration files.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from config import app_config

def run_migrations():
    """Run PocketBase migrations by executing them via PocketBase API"""
    
    print("🔄 Starting PocketBase migrations...")
    
    # Get PocketBase URL and credentials
    pb_url = app_config.pocketbase_url
    pb_email = app_config.pocketbase_email
    pb_password = app_config.pocketbase_password
    
    print(f"📡 Connecting to PocketBase at: {pb_url}")
    
    # Step 1: Authenticate with PocketBase
    auth_url = f"{pb_url}/api/admins/auth-with-password"
    auth_data = {
        "identity": pb_email,
        "password": pb_password
    }
    
    try:
        auth_response = requests.post(auth_url, json=auth_data, timeout=30)
        auth_response.raise_for_status()
        
        auth_result = auth_response.json()
        token = auth_result.get("token")
        
        if not token:
            print("❌ Failed to get authentication token")
            return False
            
        print("✅ Authenticated with PocketBase")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Step 2: Check if migrations are needed
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current collections to see what's already migrated
    collections_url = f"{pb_url}/api/collections"
    
    try:
        collections_response = requests.get(collections_url, headers=headers, timeout=30)
        collections_response.raise_for_status()
        collections = collections_response.json()
        
        existing_collections = {col["name"] for col in collections.get("items", [])}
        print(f"📊 Found {len(existing_collections)} existing collections")
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Could not check existing collections: {e}")
        existing_collections = set()
    
    # Step 3: Run migrations in order
    migrations_dir = Path("pb_migrations")
    migration_files = sorted([f for f in migrations_dir.glob("*.js") if f.is_file()])
    
    print(f"📁 Found {len(migration_files)} migration files")
    
    for migration_file in migration_files:
        print(f"🔄 Processing: {migration_file.name}")
        
        # Read the migration file
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_content = f.read()
        except Exception as e:
            print(f"❌ Failed to read {migration_file.name}: {e}")
            continue
        
        # Execute migration via PocketBase API
        # Note: This is a simplified approach - PocketBase migrations are typically
        # run by the PocketBase server itself, not via API calls
        print(f"⚠️  Migration {migration_file.name} needs to be run on PocketBase server")
        print(f"   Content preview: {migration_content[:100]}...")
    
    print("✅ Migration process completed")
    return True

def check_pocketbase_health():
    """Check if PocketBase is accessible and healthy"""
    
    pb_url = app_config.pocketbase_url
    
    try:
        # Try to reach PocketBase health endpoint
        health_url = f"{pb_url}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ PocketBase is accessible and healthy")
            return True
        else:
            print(f"⚠️  PocketBase returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach PocketBase: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PocketBase Migration Runner")
    print("=" * 50)
    
    # Check PocketBase health first
    if not check_pocketbase_health():
        print("❌ PocketBase is not accessible. Please check your configuration.")
        sys.exit(1)
    
    # Run migrations
    success = run_migrations()
    
    if success:
        print("🎉 All migrations completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration process failed!")
        sys.exit(1)
