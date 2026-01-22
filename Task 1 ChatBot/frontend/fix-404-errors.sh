#!/bin/bash

# Fix 404 Errors Script
echo "🔧 Fixing 404 errors..."

# 1. Stop any running Next.js dev server
echo "1. Stopping dev server..."
pkill -f "next dev" || true

# 2. Clear Next.js cache
echo "2. Clearing Next.js cache..."
rm -rf .next

# 3. Clear node_modules (optional - uncomment if needed)
# echo "3. Clearing node_modules..."
# rm -rf node_modules package-lock.json

# 4. Reinstall dependencies (if node_modules was cleared)
# echo "4. Reinstalling dependencies..."
# npm install

echo "✅ Done! Now run: npm run dev"
