# Context Window Optimization Strategies

## Overview
This document outlines strategies for handling limited LLM context windows using advanced ANN (Approximate Nearest Neighbor) vector search techniques.

## Current Implementation
- **Vector Database**: Qdrant (uses HNSW for ANN)
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Retrieval**: Simple cosine similarity search
- **Context Limit**: 6000 characters (hard limit)

## Optimization Strategies

### 1. **Multi-Stage Retrieval (Coarse-to-Fine)**
- **Stage 1**: Retrieve more candidates (e.g., 20-50) using fast ANN search
- **Stage 2**: Re-rank top candidates using more expensive but accurate methods
- **Benefits**: Better precision while maintaining speed

### 2. **Query Expansion**
- Generate multiple query variations using LLM
- Search with each variation and merge results
- **Benefits**: Captures semantic variations and synonyms

### 3. **Re-ranking with Cross-Encoders**
- Use cross-encoder models (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Re-rank top N candidates for better relevance
- **Benefits**: Significantly improves retrieval quality

### 4. **Diversity in Retrieval**
- Ensure retrieved chunks come from different documents/sections
- Use MMR (Maximal Marginal Relevance) algorithm
- **Benefits**: Reduces redundancy, increases information coverage

### 5. **Hierarchical Retrieval**
- Retrieve at document level first, then chunk level
- Or retrieve at different granularities (paragraph, section, document)
- **Benefits**: Better context understanding

### 6. **Hybrid Search**
- Combine vector search with keyword/BM25 search
- Weighted combination of both results
- **Benefits**: Captures both semantic and exact matches

### 7. **Context Compression**
- Summarize retrieved chunks before sending to LLM
- Use extractive or abstractive summarization
- **Benefits**: Reduces context size while preserving key information

### 8. **Adaptive Retrieval**
- Adjust retrieval parameters based on query complexity
- Simple queries: fewer, high-quality results
- Complex queries: more results, broader search
- **Benefits**: Optimizes for different query types

### 9. **Semantic Chunking**
- Use semantic similarity for chunking instead of fixed-size
- Ensures chunks are semantically coherent
- **Benefits**: Better retrieval quality, more meaningful chunks

### 10. **Smart Context Prioritization**
- Score and rank chunks by relevance + diversity
- Prioritize high-scoring, diverse chunks
- **Benefits**: Maximizes information density in limited context

## Implementation Priority

### Phase 1 (Quick Wins)
1. ✅ Multi-stage retrieval with re-ranking
2. ✅ Diversity filtering (MMR)
3. ✅ Adaptive retrieval based on query length/complexity

### Phase 2 (Medium Effort)
4. Query expansion
5. Context compression/summarization
6. Hybrid search (if keyword search needed)

### Phase 3 (Advanced)
7. Hierarchical retrieval
8. Semantic chunking (requires re-indexing)
9. Cross-encoder re-ranking

## Configuration Options

```python
# Enhanced RAG Configuration
ENABLE_RERANKING = True
ENABLE_QUERY_EXPANSION = False
ENABLE_DIVERSITY_FILTERING = True
ENABLE_CONTEXT_COMPRESSION = False
ENABLE_HYBRID_SEARCH = False

# Retrieval Parameters
INITIAL_RETRIEVAL_COUNT = 20  # Retrieve more initially
FINAL_RETRIEVAL_COUNT = 5     # After re-ranking/filtering
MIN_SIMILARITY_SCORE = 0.5
DIVERSITY_THRESHOLD = 0.7     # MMR lambda parameter

# Context Management
MAX_CONTEXT_LENGTH = 6000     # Characters
ENABLE_SMART_TRUNCATION = True
CONTEXT_COMPRESSION_RATIO = 0.5  # Compress to 50% if enabled
```

## Performance Considerations

- **ANN Search**: Fast (milliseconds) with HNSW
- **Re-ranking**: Slower but more accurate (100-500ms)
- **Query Expansion**: Adds latency but improves recall
- **Context Compression**: Adds latency but reduces context size

## Trade-offs

| Strategy | Latency Impact | Quality Impact | Complexity |
|----------|---------------|----------------|------------|
| Multi-stage retrieval | Low | High | Medium |
| Re-ranking | Medium | Very High | Medium |
| Query expansion | High | High | High |
| Diversity filtering | Low | Medium | Low |
| Context compression | High | Medium | High |
| Hybrid search | Medium | High | High |
