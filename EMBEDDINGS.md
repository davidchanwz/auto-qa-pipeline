# Embedding Generation System

## Overview

The auto-qa-pipeline now includes automatic embedding generation for all codes created during the qualitative analysis process. This enables semantic similarity comparison and advanced code relationship analysis.

## Implementation

### Agent.add_embedding() Method

The `Agent` class now includes an `add_embedding()` method that:

1. **Creates Rich Text Representation**: Combines code name, function, and evidence into a comprehensive text
2. **Generates Embeddings**: Uses OpenAI's `text-embedding-3-small` model for high-quality vector representations
3. **Error Handling**: Gracefully handles embedding generation failures by returning the original code
4. **Preserves Code Structure**: Returns a new Code object with the embedding added

### Text Representation Format

```
Name: [Code Name] | Function: [Function Type] | Evidence: Evidence from article [ID]: [Quote] | Evidence from article [ID]: [Quote]...
```

### Integration Points

#### 1. **Article Analysis** (`analyze_article`)

- Every candidate code generated from LLM analysis gets an embedding
- Embeddings are generated immediately after code creation
- Process is logged with embedding dimensions and success status

#### 2. **Code Operations** (`compare_with_existing_codes`)

- New codes in CREATE_CODE operations include embeddings
- CREATE_NEW operations (despite similarity) include embeddings
- Existing similarity comparison can leverage embeddings

#### 3. **Incremental Processing**

- Each article's codes get embeddings before codebook updates
- Subsequent articles can compare against embedded codes
- Cumulative embedding-based knowledge building

## Benefits

### 1. **Enhanced Similarity Detection**

- Semantic similarity beyond simple text matching
- Better merge/update decisions based on conceptual overlap
- Reduced false negatives in code relationship detection

### 2. **Scalable Code Comparison**

- Vector-based similarity calculation
- Efficient comparison against large codebooks
- Support for advanced clustering and categorization

### 3. **Future AI Capabilities**

- Foundation for semantic search within codebooks
- Support for concept clustering and hierarchy detection
- Enables embedding-based code recommendations

### 4. **Research Reproducibility**

- Consistent vector representations across sessions
- Trackable similarity metrics and thresholds
- Audit trail of embedding generation process

## Usage Examples

### Direct Embedding Generation

```python
from services.agent import Agent
from classes import Code, Function

# Create agent
agent = Agent(llm_config)

# Create code
code = Code(
    name="Communication Challenges",
    function=Function.DESCRIPTIVE,
    evidence=evidence_dict,
    embedding=None
)

# Generate embedding
code_with_embedding = agent.add_embedding(code)
print(f"Embedding dimensions: {len(code_with_embedding.embedding)}")
```

### Automatic Integration

```python
# Embeddings are generated automatically during analysis
exploration = ExplorationLayer(agent, strategic)
codebook = exploration.analyze_articles(articles)

# All codes in final codebook have embeddings
for code in codebook.codes:
    assert code.embedding is not None
    print(f"Code '{code.name}' has {len(code.embedding)}-dimensional embedding")
```

## Technical Specifications

### Embedding Model

- **Model**: `text-embedding-3-small`
- **Dimensions**: 1536 (standard OpenAI embedding size)
- **Input**: Rich text representation of code (name + function + evidence)
- **Output**: Float vector array

### Error Handling

- Network failures: Returns original code without embedding
- API errors: Logs warning and continues processing
- Invalid responses: Graceful degradation to non-embedded code

### Performance Considerations

- **API Calls**: One embedding call per candidate code (~2-5 per article)
- **Processing Time**: ~100-200ms per embedding generation
- **Cost**: Minimal cost per embedding (~$0.00002 per code)
- **Caching**: No caching implemented (embeddings generated fresh each time)

## Logging Integration

### New Log Events

- `code_created`: Now includes embedding generation status and dimensions
- `embedding_generated`: Detailed embedding creation metrics
- `embedding_error`: Failed embedding generation attempts

### Log Data Structure

```json
{
  "step_type": "code_created",
  "data": {
    "code_name": "Remote Work Challenges",
    "embedding_generated": true,
    "embedding_dimensions": 1536,
    "evidence_count": 3
  }
}
```

## Testing

Run the embedding test suite:

```bash
python test_embeddings.py
```

This will:

1. Test direct embedding generation
2. Verify integration with article analysis
3. Check full pipeline embedding coverage
4. Generate test codebook with embeddings

## Future Enhancements

### Planned Features

1. **Embedding-based Similarity**: Replace simple text similarity with vector cosine similarity
2. **Code Clustering**: Automatic grouping of semantically similar codes
3. **Semantic Search**: Find codes by concept rather than exact text match
4. **Embedding Caching**: Cache embeddings to reduce API calls and improve performance

### Advanced Use Cases

1. **Cross-Study Comparison**: Compare codes across different research projects
2. **Concept Evolution**: Track how code meanings change over time
3. **Theme Hierarchy**: Automatic detection of parent-child relationships between codes
4. **Quality Metrics**: Embedding-based measures of code distinctiveness and coherence
