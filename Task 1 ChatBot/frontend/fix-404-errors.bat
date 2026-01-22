@echo off
REM Fix 404 Errors Script for Windows

echo Fixing 404 errors...

REM 1. Stop any running Next.js dev server
echo 1. Stopping dev server...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *next dev*" 2>nul || echo No dev server running

REM 2. Clear Next.js cache
echo 2. Clearing Next.js cache...
if exist .next rmdir /s /q .next

REM 3. Clear node_modules (optional - uncomment if needed)
REM echo 3. Clearing node_modules...
REM if exist node_modules rmdir /s /q node_modules
REM if exist package-lock.json del /q package-lock.json

REM 4. Reinstall dependencies (if node_modules was cleared)
REM echo 4. Reinstalling dependencies...
REM call npm install

echo Done! Now run: npm run dev
pause
