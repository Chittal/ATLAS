#!/usr/bin/env python3
"""
PocketBase Migration Helper for Render Docker
This script helps ensure PocketBase is properly set up with required collections.
Since PocketBase migrations are JavaScript files that run inside PocketBase,
this script creates the collections via API calls instead.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from config import app_config

def create_collection_via_api(token, pb_url, collection_data):
    """Create a collection via PocketBase API"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    collections_url = f"{pb_url}/api/collections"
    
    try:
        response = requests.post(collections_url, json=collection_data, headers=headers, timeout=30)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Created collection: {collection_data['name']}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"⚠️  Collection already exists: {collection_data['name']}")
            return True
        else:
            print(f"❌ Failed to create collection {collection_data['name']}: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating collection {collection_data['name']}: {e}")
        return False

def run_migrations():
    """Run PocketBase setup by creating required collections"""
    
    print("🔄 Setting up PocketBase collections...")
    
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
    
    # Step 2: Define required collections based on your migration files
    collections_to_create = [
        {
            "name": "roadmaps",
            "type": "base",
            "schema": [
                {"name": "title", "type": "text", "required": True},
                {"name": "description", "type": "text", "required": False},
                {"name": "skills", "type": "json", "required": False},
                {"name": "created", "type": "date", "required": True}
            ]
        },
        {
            "name": "roadmap_paths", 
            "type": "base",
            "schema": [
                {"name": "roadmap_id", "type": "relation", "required": True, "options": {"collectionId": "", "cascadeDelete": True}},
                {"name": "title", "type": "text", "required": True},
                {"name": "description", "type": "text", "required": False},
                {"name": "order", "type": "number", "required": True}
            ]
        },
        {
            "name": "roadmap_path_skills",
            "type": "base", 
            "schema": [
                {"name": "path_id", "type": "relation", "required": True, "options": {"collectionId": "", "cascadeDelete": True}},
                {"name": "skill_name", "type": "text", "required": True},
                {"name": "skill_level", "type": "text", "required": True},
                {"name": "order", "type": "number", "required": True}
            ]
        },
        {
            "name": "user_roadmap_path",
            "type": "auth",
            "schema": [
                {"name": "path_id", "type": "relation", "required": True, "options": {"collectionId": "", "cascadeDelete": True}},
                {"name": "progress", "type": "number", "required": True},
                {"name": "completed", "type": "bool", "required": True},
                {"name": "started_at", "type": "date", "required": False},
                {"name": "completed_at", "type": "date", "required": False}
            ]
        },
        {
            "name": "user_learning_node_progress",
            "type": "auth",
            "schema": [
                {"name": "skill_name", "type": "text", "required": True},
                {"name": "progress", "type": "number", "required": True},
                {"name": "completed", "type": "bool", "required": True},
                {"name": "last_updated", "type": "date", "required": True}
            ]
        },
        {
            "name": "notes",
            "type": "auth",
            "schema": [
                {"name": "title", "type": "text", "required": True},
                {"name": "content", "type": "text", "required": True},
                {"name": "skill_name", "type": "text", "required": False},
                {"name": "created", "type": "date", "required": True}
            ]
        }
    ]
    
    # Step 3: Create collections
    success_count = 0
    for collection in collections_to_create:
        if create_collection_via_api(token, pb_url, collection):
            success_count += 1
    
    print(f"📊 Created {success_count}/{len(collections_to_create)} collections")
    
    # Step 4: Create super user if needed
    print("👤 Setting up super user...")
    try:
        # Check if super user already exists
        users_url = f"{pb_url}/api/collections/users/records"
        users_response = requests.get(users_url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        
        if users_response.status_code == 200:
            users = users_response.json()
            if users.get("totalItems", 0) == 0:
                print("👤 Creating super user...")
                # Create super user
                super_user_data = {
                    "email": "admin@learningmap.com",
                    "password": "admin123",
                    "passwordConfirm": "admin123",
                    "name": "Super Admin"
                }
                
                create_user_url = f"{pb_url}/api/collections/users/records"
                user_response = requests.post(create_user_url, json=super_user_data, headers={"Authorization": f"Bearer {token}"}, timeout=30)
                
                if user_response.status_code == 200 or user_response.status_code == 201:
                    print("✅ Super user created successfully")
                else:
                    print(f"⚠️  Could not create super user: {user_response.status_code}")
            else:
                print("✅ Users already exist, skipping super user creation")
        else:
            print("⚠️  Could not check existing users")
            
    except Exception as e:
        print(f"⚠️  Error setting up super user: {e}")
    
    print("✅ PocketBase setup completed!")
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
    print("🚀 PocketBase Setup Runner")
    print("=" * 50)
    
    # Check PocketBase health first
    if not check_pocketbase_health():
        print("❌ PocketBase is not accessible. Please check your configuration.")
        sys.exit(1)
    
    # Run setup
    success = run_migrations()
    
    if success:
        print("🎉 PocketBase setup completed successfully!")
        sys.exit(0)
    else:
        print("❌ PocketBase setup failed!")
        sys.exit(1)
