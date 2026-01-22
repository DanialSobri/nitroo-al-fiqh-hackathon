# Frontend Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env.local
   ```
   
   Edit `.env.local` and set:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Features

- ✅ Perplexity.ai-inspired design
- ✅ Real-time chat interface
- ✅ Source references with similarity scores
- ✅ Responsive design
- ✅ TypeScript support
- ✅ shadcn/ui components

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main chat page
│   └── globals.css        # Global styles
├── components/
│   ├── ui/                # shadcn/ui components
│   └── chat/              # Chat-specific components
├── lib/
│   ├── api.ts             # API client
│   └── utils.ts           # Utilities
└── public/                # Static assets
```

## Customization

### Change API URL

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

### Add More shadcn/ui Components

```bash
npx shadcn-ui@latest add [component-name]
```

## Troubleshooting

### CORS Issues

Make sure your backend has CORS enabled for `http://localhost:3000`:
```python
# In backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    ...
)
```

### API Connection Failed

1. Check if backend is running on port 8000
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for errors
