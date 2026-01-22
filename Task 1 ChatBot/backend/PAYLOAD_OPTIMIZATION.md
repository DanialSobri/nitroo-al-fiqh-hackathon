# Payload Size Optimization Guide

## Overview
This guide explains how to reduce the total character count in API payloads sent to the LLM.

## Current Optimizations

### 1. **Compact Prompt Template** ✅
- **Before**: ~250 characters of verbose instructions
- **After**: ~30 characters minimal prompt
- **Savings**: ~220 characters per request

**Compact Format:**
```
Answer based on the context:

{context}

Q: {question}
A:
```

**Full Format (if disabled):**
```
You are an expert in Islamic finance and Shariah compliance. Answer the following question based on the provided context from official documents.

Context from documents:
{context}

Question: {question}

Provide a clear, accurate, and comprehensive answer based on the context...
```

### 2. **Compact Context Formatting** ✅
- **Before**: `From {title}:\n{doc_text}` (~10 chars overhead per doc)
- **After**: `[{title}] {doc_text}` (~3 chars overhead per doc)
- **Savings**: ~7 characters per document × 5 docs = ~35 characters

### 3. **Shorter Separators** ✅
- **Before**: `\n\n---\n\n` (7 characters)
- **After**: `\n\n` (2 characters)
- **Savings**: ~5 characters per separator × 4 = ~20 characters

### 4. **Reduced Context Length** ✅
- **Before**: 6000 characters max
- **After**: 4000 characters max (configurable)
- **Savings**: Up to 2000 characters

### 5. **Reduced Prompt Limit** ✅
- **Before**: 8000 characters max prompt
- **After**: 5000 characters max prompt
- **Savings**: Prevents oversized requests

## Total Estimated Savings

| Optimization | Savings |
|--------------|---------|
| Compact prompt | ~220 chars |
| Compact formatting | ~35 chars |
| Shorter separators | ~20 chars |
| Reduced context | ~2000 chars |
| **Total** | **~2275 chars** |

## Configuration

Add to your `.env` file:

```bash
# Enable compact prompt (recommended)
USE_COMPACT_PROMPT=True

# Reduce context length
MAX_CONTEXT_LENGTH=4000  # Default was 6000

# Other optimizations are automatic when compact prompt is enabled
```

## Example Payload Comparison

### Before (Full Format)
```json
{
  "model": "gemma3:27b",
  "messages": [{
    "role": "user",
    "content": "You are an expert in Islamic finance and Shariah compliance. Answer the following question based on the provided context from official documents.\n\nContext from documents:\nFrom Detail information on the resolution is available here.:\nTHE 281ST SHARIAH ADVISORY COUNCIL...\n\n---\n\nFrom Another Document:\nMore content here...\n\nQuestion: What is Shariah non-tolerable income threshold?\n\nProvide a clear, accurate, and comprehensive answer..."
  }]
}
```
**Size**: ~6420 characters

### After (Compact Format)
```json
{
  "model": "gemma3:27b",
  "messages": [{
    "role": "user",
    "content": "Answer based on the context:\n\n[Detail information on the resolution is available here.] THE 281ST SHARIAH ADVISORY COUNCIL...\n\n[Another Document] More content here...\n\nQ: What is Shariah non-tolerable income threshold?\nA:"
  }]
}
```
**Size**: ~4145 characters (**~35% reduction**)

## Additional Optimization Strategies

### 1. **Further Reduce Context Length**
```bash
MAX_CONTEXT_LENGTH=3000  # Even smaller for very limited APIs
```

### 2. **Reduce Number of Documents**
```bash
MAX_RETRIEVAL_RESULTS=3  # Instead of 5
```

### 3. **Increase Similarity Threshold**
```bash
MIN_SIMILARITY_SCORE=0.6  # Only high-quality matches
```

### 4. **Enable Context Compression** (Future)
```bash
ENABLE_CONTEXT_COMPRESSION=True  # Summarize chunks before sending
```

## Monitoring

Watch the logs for:
- `Prompt size: X characters` - Shows actual payload size
- `⚠ Context limit reached` - Indicates truncation is working
- `⚠ Warning: Prompt is X chars, truncating` - Shows API-level truncation

## Trade-offs

| Optimization | Benefit | Trade-off |
|--------------|---------|-----------|
| Compact prompt | Smaller payload | Less explicit instructions |
| Reduced context | Smaller payload | Less information available |
| Fewer documents | Smaller payload | May miss relevant info |
| Higher similarity threshold | Better quality | Fewer results |

## Recommendations

1. **Enable compact prompt** - Minimal quality impact, significant size reduction
2. **Set context length to 4000** - Good balance between size and quality
3. **Keep 5 documents** - Good coverage without being too large
4. **Monitor answer quality** - Adjust if answers become less accurate

## Testing

Test the optimizations:

```bash
# Test with compact prompt
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Shariah non-tolerable income threshold?",
    "max_results": 5
  }'
```

Compare the payload size in the debug logs before and after enabling optimizations.
