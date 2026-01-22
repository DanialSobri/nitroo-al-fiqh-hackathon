# Neo AI Frontend

A modern chat interface for Islamic Finance and Shariah Compliance Q&A, built with Next.js and shadcn/ui, styled like Perplexity.ai. Neo AI stands for Next‑Gen Optimized Advisor, driven by Agentic AI.

## Features

- 🎨 **Modern UI**: Clean, Perplexity.ai-inspired design
- 💬 **Chat Interface**: Real-time Q&A with streaming-like experience
- 📚 **Source References**: Display sources with similarity scores
- 🎯 **Responsive**: Works on desktop and mobile
- ⚡ **Fast**: Built with Next.js 14 App Router

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI Components**: shadcn/ui
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **TypeScript**: Full type safety

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Set up environment variables:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and set your backend API URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Troubleshooting 404 Errors

If you see 404 errors for `index.tsx`, `@react-refresh`, or `manifest.json`:

**Quick Fix:**
```bash
# Windows
fix-404-errors.bat

# Mac/Linux
chmod +x fix-404-errors.sh
./fix-404-errors.sh

# Or manually:
rm -rf .next
npm run dev
```

Then **hard refresh** your browser (Ctrl+Shift+R or Cmd+Shift+R).

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more details.

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main chat page
│   └── globals.css         # Global styles
├── components/
│   ├── ui/                 # shadcn/ui components
│   │   ├── button.tsx
│   │   └── scroll-area.tsx
│   └── chat/               # Chat components
│       ├── chat-message.tsx
│       └── chat-input.tsx
├── lib/
│   ├── api.ts              # API client
│   └── utils.ts            # Utility functions
└── public/                 # Static assets
```

## API Integration

The frontend calls the `/ask` endpoint:

```typescript
POST /ask
{
  "question": "What is Shariah non-tolerable income threshold?",
  "collections": ["all"],
  "max_results": 5,
  "min_score": 0.5
}
```

Response includes:
- `answer`: The generated answer
- `references`: Array of source documents
- `total_references_found`: Number of references
- `collections_searched`: Collections that were searched

## Customization

### Change API URL

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

### Modify Colors

Edit `app/globals.css` to customize the color scheme.

### Add More Components

Use shadcn/ui CLI to add more components:

```bash
npx shadcn-ui@latest add [component-name]
```

## Build for Production

```bash
npm run build
npm start
```

## License

MIT
