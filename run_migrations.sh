#!/bin/bash
# PocketBase Migration Runner for Render Docker
# This script runs PocketBase migrations during container startup

set -e  # Exit on any error

echo "🚀 Starting PocketBase Migration Process"
echo "========================================"

# Check if we have the required environment variables
if [ -z "$POCKETBASE_URL" ]; then
    echo "❌ POCKETBASE_URL environment variable is not set"
    exit 1
fi

if [ -z "$POCKETBASE_EMAIL" ]; then
    echo "❌ POCKETBASE_EMAIL environment variable is not set"
    exit 1
fi

if [ -z "$POCKETBASE_PASSWORD" ]; then
    echo "❌ POCKETBASE_PASSWORD environment variable is not set"
    exit 1
fi

echo "📡 PocketBase URL: $POCKETBASE_URL"
echo "📧 PocketBase Email: $POCKETBASE_EMAIL"

# Wait for PocketBase to be ready (with retries)
echo "⏳ Waiting for PocketBase to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "$POCKETBASE_URL/api/health" > /dev/null 2>&1; then
        echo "✅ PocketBase is ready!"
        break
    else
        echo "⏳ PocketBase not ready yet, waiting... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ PocketBase is not accessible after $MAX_RETRIES attempts"
    echo "⚠️  Continuing without migrations - PocketBase may not be ready"
    exit 0
fi

# Run the Python migration script
echo "🔄 Setting up PocketBase collections..."
python3 migrate_pocketbase.py

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "⚠️  Migration process had issues, but continuing..."
fi

echo "🎉 Migration process finished!"
