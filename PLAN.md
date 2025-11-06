# Implementation Plan: Automatic Qualitative Analysis Pipeline

## Strategic and Exploration Layers

### Project Overview

This plan outlines the implementation of the first two stages of an automatic qualitative analysis pipeline using a human-in-the-loop approach:

1. **Strategic Layer**: Defines research framework and prompt templates
2. **Exploration Layer**: Uses AI agents to code articles and manage the evolving codebook

### Current State Analysis

#### Existing Components

- ✅ Basic project structure with `services/` directory
- ✅ Core data models (`Code`, `Codebook`, `Function` enum)
- ✅ LLM Agent with JSON response capabilities
- ✅ Sample articles and codes based on Entman's framing theory
- ✅ Configuration management

#### Missing Components

- ❌ Strategic layer implementation
- ❌ Exploration layer implementation
- ❌ RAG system for similarity search
- ❌ Operation decision logic
- ❌ Embedding generation and management
- ❌ Pipeline orchestration

---

## Phase 1: Strategic Layer Implementation

### 1.1 Research Framework Management

**File**: `services/strategic.py`

**Components to implement**:

- `ResearchFramework` class to encapsulate Entman's theory
- Framework validation and configuration
- Default framework definitions

**Tasks**:

- [ ] Create `ResearchFramework` dataclass with:
  - Framework name and description
  - Function definitions (Entman's 4 functions)
  - Basic validation rules
- [ ] Implement framework loader from JSON/config files
- [ ] Add framework validation methods
- [ ] Create default Entman framework configuration

### 1.2 Prompt Template System

**Components to implement**:

- `PromptTemplate` class for structured prompts
- Template rendering with variables
- Context-aware prompt generation

**Tasks**:

- [ ] Create `PromptTemplate` dataclass with:
  - Template content with placeholders
  - Required variables
  - Output format specifications
  - Function-specific prompts
- [ ] Implement template rendering engine
- [ ] Create default Entman coding prompts
- [ ] Add template validation and testing

### 1.3 Codebook Initialization

**Components to implement**:

- Sample codebook generation
- Codebook loading and validation
- Integration with existing `Codebook` class

**Tasks**:

- [ ] Enhance `Codebook` class with:
  - Load from JSON functionality
  - Save to JSON functionality
  - Validation methods
  - Statistics generation
- [ ] Create codebook initialization logic
- [ ] Implement codebook versioning
- [ ] Add backup and restore functionality

### 1.4 Strategic Layer Interface

**Tasks**:

- [ ] Create `StrategicLayer` orchestrator class
- [ ] Implement configuration management
- [ ] Add framework switching capabilities
- [ ] Create initialization and setup methods

---

## Phase 2: Exploration Layer Implementation

### 2.1 Article Processing Engine

**File**: `services/exploration.py`

**Components to implement**:

- Article loader and preprocessor
- Batch processing capabilities
- Progress tracking

**Tasks**:

- [ ] Create `ArticleProcessor` class with:
  - Article loading from JSON
  - Text preprocessing and cleaning
  - Batch processing support
  - Progress tracking and logging
- [ ] Implement article validation
- [ ] Add support for different article formats
- [ ] Create article metadata extraction

### 2.2 AI-Powered Coding Agent

**Components to implement**:

- Specialized coding agent using existing LLM client
- Candidate code generation
- Context management for coding sessions

**Tasks**:

- [ ] Create `CodingAgent` class extending base `Agent`:
  - Specialized for qualitative coding
  - Template-driven prompting
  - Structured code output
  - Context preservation
- [ ] Implement candidate code generation:
  - Extract quotes and evidence
  - Generate code names and descriptions
  - Assign function classifications
  - Create embeddings
- [ ] Add quality validation for generated codes
- [ ] Implement retry logic for failed coding attempts

### 2.3 RAG-based Similarity System

**Components to implement**:

- Embedding generation and storage
- Vector similarity search
- Code comparison and ranking

**Tasks**:

- [ ] Create `SimilarityEngine` class:
  - Generate embeddings for codes
  - Vector storage and indexing
  - Similarity search algorithms
  - Ranking and scoring
- [ ] Implement embedding models:
  - Code name embeddings
  - Evidence text embeddings
  - Combined semantic embeddings
- [ ] Create similarity threshold configuration
- [ ] Add caching for performance optimization

### 2.4 Operation Decision System

**Components to implement**:

- Decision agent for codebook operations
- Rule-based and AI-powered decision logic
- Human-in-the-loop integration points

**Tasks**:

- [ ] Enhance `Operation` class with:
  - CREATE_CODE operation
  - MERGE_CODES operation
  - UPDATE_CODE operation
  - NO_ACTION operation
- [ ] Create `DecisionAgent` class:
  - Analyze candidate vs similar codes
  - Apply decision rules
  - Generate operation recommendations
  - Confidence scoring
- [ ] Implement decision logic:
  - Similarity threshold rules
  - Conflict resolution
  - Evidence aggregation
  - Quality assessment
- [ ] Add human review integration points

### 2.5 Codebook Management

**Tasks**:

- [ ] Implement `Codebook.merge_codes()` method
- [ ] Create `Codebook.get_similar_codes()` using embeddings
- [ ] Add `Codebook.execute_operation()` method
- [ ] Implement code ID management and auto-increment
- [ ] Add codebook statistics and reporting

---

## Phase 3: Integration and Orchestration

### 3.1 Pipeline Orchestrator

**File**: `main.py`

**Tasks**:

- [ ] Create `Pipeline` class to orchestrate both layers
- [ ] Implement configuration loading
- [ ] Add progress tracking and logging
- [ ] Create resume/restart capabilities
- [ ] Add result reporting and export

### 3.2 Enhanced Data Models

**File**: `classes.py`

**Tasks**:

- [ ] Add embedding support to `Code` class
- [ ] Enhance `Codebook` with persistence methods
- [ ] Create `ProcessingSession` class for tracking
- [ ] Add validation methods to all classes
- [ ] Implement serialization/deserialization

### 3.3 Configuration Management

**File**: `config.py`

**Tasks**:

- [ ] Add pipeline-specific configurations
- [ ] Create embedding model settings
- [ ] Add similarity threshold configurations
- [ ] Implement environment-based config loading

---

## Phase 4: Testing and Validation

### 4.1 Unit Testing

**Tasks**:

- [ ] Create test suite for Strategic Layer
- [ ] Create test suite for Exploration Layer
- [ ] Mock external dependencies (OpenAI API)
- [ ] Test edge cases and error handling

### 4.2 Integration Testing

**Tasks**:

- [ ] End-to-end pipeline testing
- [ ] Performance benchmarking
- [ ] Quality assessment of generated codes
- [ ] Validation against expert-coded samples

### 4.3 Documentation

**Tasks**:

- [ ] Update README with pipeline documentation
- [ ] Create API documentation
- [ ] Add usage examples and tutorials
- [ ] Document configuration options

---

## Implementation Timeline

### Week 1-2: Strategic Layer

- Research framework implementation
- Prompt template system
- Codebook initialization
- Basic testing

### Week 3-4: Core Exploration Layer

- Article processing
- AI coding agent
- Basic operation system
- Integration with strategic layer

### Week 5-6: Advanced Features

- RAG similarity system
- Decision agent implementation
- Human-in-the-loop integration
- Advanced codebook operations

### Week 7-8: Integration & Polish

- Pipeline orchestration
- Comprehensive testing
- Performance optimization
- Documentation and examples

---

## Key Dependencies

### External Libraries

```toml
dependencies = [
    "openai>=1.0.0",
    "python-dotenv>=1.0.0",
    "numpy>=1.24.0",
    "scikit-learn>=1.3.0",
    "sentence-transformers>=2.2.0",
    "faiss-cpu>=1.7.0",  # for vector similarity search
    "pydantic>=2.0.0",   # for data validation
    "rich>=13.0.0",      # for beautiful CLI output
]
```

### Development Dependencies

```toml
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
]
```

---

## Success Criteria

1. **Strategic Layer**:

   - ✅ Configurable research frameworks
   - ✅ Flexible prompt templates
   - ✅ Robust codebook initialization

2. **Exploration Layer**:

   - ✅ Accurate candidate code generation
   - ✅ Effective similarity detection
   - ✅ Intelligent operation decisions
   - ✅ Quality preservation in codebook evolution

3. **Overall Pipeline**:
   - ✅ End-to-end automated processing
   - ✅ Human review integration points
   - ✅ Scalable and maintainable architecture
   - ✅ Comprehensive testing and documentation

---

## Risk Mitigation

1. **LLM Reliability**: Implement retry logic and quality validation
2. **Similarity Accuracy**: Use multiple similarity metrics and thresholds
3. **Performance**: Implement caching and batch processing
4. **Code Quality**: Comprehensive testing and code review processes
5. **User Experience**: Clear documentation and error messaging

This plan provides a structured approach to implementing your automatic qualitative analysis pipeline while maintaining flexibility for future enhancements and different research frameworks.
