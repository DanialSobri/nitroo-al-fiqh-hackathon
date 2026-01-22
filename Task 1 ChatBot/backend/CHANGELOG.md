# Changelog

## LangChain 1.x Compatibility Fix

### Fixed Issues

1. **Removed deprecated imports**:
   - Removed `from langchain.chains import RetrievalQA` (not needed)
   - Removed `from langchain.prompts import PromptTemplate` (not used)
   - Removed `from langchain.schema import Document` (not used)

2. **Updated configuration**:
   - Made `openai_api_key` optional in config (defaults to empty string)
   - Validation still occurs when LLM is actually initialized

3. **Removed unused code**:
   - Removed `_create_qa_chain` method that was never used

### Compatibility

- ✅ LangChain 1.2.6+
- ✅ langchain-community 0.4.1+
- ✅ langchain-openai 1.1.7+
- ✅ langchain-qdrant 1.1.0+

### Notes

The code now uses direct Qdrant client calls for retrieval instead of relying on LangChain's vector store methods, which provides more control and better compatibility.
