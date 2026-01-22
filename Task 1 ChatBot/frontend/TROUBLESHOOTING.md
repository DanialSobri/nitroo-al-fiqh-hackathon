# Troubleshooting Guide

## Common 404 Errors

### 1. `index.tsx` 404 Error

**Problem**: Browser is looking for `index.tsx` which doesn't exist in Next.js App Router.

**Solution**: 
- Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- This is likely a cached reference from an old build
- Next.js App Router uses `page.tsx`, not `index.tsx`

### 2. `@react-refresh` 404 Error

**Problem**: Next.js internal module not found.

**Solutions**:
1. **Clear Next.js cache:**
   ```bash
   rm -rf .next
   npm run dev
   ```

2. **Reinstall dependencies:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Check Node.js version:**
   ```bash
   node --version  # Should be 18.x or higher
   ```

### 3. `manifest.json` 404 Error

**Problem**: Browser is looking for PWA manifest file.

**Solution**: 
- The `manifest.json` file has been created in `/public/manifest.json`
- Clear browser cache
- Hard refresh the page

## Fix All Issues at Once

Run these commands in order:

```bash
# 1. Stop the dev server (Ctrl+C)

# 2. Clear Next.js cache
rm -rf .next

# 3. Clear node_modules (optional, if issues persist)
rm -rf node_modules package-lock.json

# 4. Reinstall dependencies
npm install

# 5. Restart dev server
npm run dev
```

## Browser Cache Issues

If errors persist after clearing Next.js cache:

1. **Chrome/Edge:**
   - Press F12 to open DevTools
   - Right-click the refresh button
   - Select "Empty Cache and Hard Reload"

2. **Firefox:**
   - Press Ctrl+Shift+Delete
   - Select "Cache" and "Clear Now"
   - Hard refresh (Ctrl+F5)

3. **Safari:**
   - Press Cmd+Option+E to empty cache
   - Hard refresh (Cmd+Shift+R)

## Port Already in Use

If port 3000 is already in use:

```bash
# Kill process on port 3000 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Kill process on port 3000 (Mac/Linux)
lsof -ti:3000 | xargs kill -9

# Or use a different port
npm run dev -- -p 3001
```

## Module Resolution Issues

If you see "Cannot find module" errors:

1. **Check TypeScript paths:**
   ```json
   // tsconfig.json should have:
   "paths": {
     "@/*": ["./*"]
   }
   ```

2. **Verify imports:**
   - Use `@/components/...` not `../components/...`
   - Use `@/lib/...` not `../lib/...`

3. **Restart TypeScript server:**
   - In VS Code: Cmd/Ctrl+Shift+P → "TypeScript: Restart TS Server"

## Build Errors

If `npm run build` fails:

1. **Check for TypeScript errors:**
   ```bash
   npx tsc --noEmit
   ```

2. **Check for ESLint errors:**
   ```bash
   npm run lint
   ```

3. **Clear all caches:**
   ```bash
   rm -rf .next node_modules
   npm install
   npm run build
   ```

## API Connection Issues

If the frontend can't connect to the backend:

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify environment variable:**
   ```bash
   # Check .env.local exists
   cat .env.local
   
   # Should contain:
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Check CORS settings:**
   - Backend should allow `http://localhost:3000`
   - Check `backend/main.py` CORS configuration

4. **Test API directly:**
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "test"}'
   ```

## Still Having Issues?

1. Check the browser console for specific error messages
2. Check the terminal where `npm run dev` is running
3. Verify all files exist in the correct locations
4. Ensure Node.js version is 18+ (`node --version`)
