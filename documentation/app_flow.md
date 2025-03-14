# Application Flow

This document outlines the core flow of the Knowledge Graph Synthesis system, from input to output, with special attention to data provenance and hallucination mitigation.

## Overall Process Flow

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│  Text Input &  │    │ Entity &       │    │ Knowledge      │    │ Recursive      │
│  Segmentation  │───►│ Relationship   │───►│ Graph          │───►│ Graph          │
│                │    │ Extraction     │    │ Construction   │    │ Expansion      │
└────────────────┘    └────────────────┘    └────────────────┘    └────────────────┘
                            │                      │                      │
                            ▼                      ▼                      ▼
                      ┌────────────┐         ┌────────────┐         ┌────────────┐
                      │ Grounding  │         │ Provenance │         │ Verification│
                      │ Validation │         │ Tracking   │         │ & Evidence  │
                      └────────────┘         └────────────┘         └────────────┘
                                                                          │
┌────────────────┐    ┌────────────────┐    ┌────────────────┐           │
│  Output        │    │ Theory &       │    │ Meta-graph     │           │
│  Generation    │◄───│ Hypothesis     │◄───│ Creation       │◄──────────┘
│  with Citations│    │ Generation     │    │                │
└────────────────┘    └────────────────┘    └────────────────┘
        │                    │                      │
        ▼                    ▼                      ▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Source         │    │ Evidence       │    │ Abstraction    │
│ References     │    │ Validation     │    │ Verification   │
└────────────────┘    └────────────────┘    └────────────────┘
```

## Detailed Flow Description

### 1. Text Input & Segmentation
- **Input**: Text files (TXT format)
- **Process**:
  1. Load text files
  2. Normalize text (encoding, formatting)
  3. Split text into logical segments
  4. Generate contextual summaries for each segment
  5. Identify cross-segment references
  6. Assign unique identifiers to segments for provenance tracking
- **Output**: Structured collection of text segments with contextual information and tracking IDs

### 2. Entity & Relationship Extraction
- **Input**: Structured text segments
- **Process**:
  1. For each segment, query Gemini to extract entities using structured response schemas
  2. For each segment, query Gemini to extract relationships between entities using structured response schemas
  3. Resolve coreferences across segments
  4. Merge duplicate entities
  5. Validate entity and relationship consistency
  6. Ground all entities in source text (verify their existence in original content)
- **Output**: Collection of entities and relationships with metadata and source references

### 3. Knowledge Graph Construction
- **Input**: Entities and relationships with provenance data
- **Process**:
  1. Create nodes for each unique entity
  2. Create edges for each relationship
  3. Assign attributes and metadata to nodes and edges
  4. Attach provenance data to all graph elements
  5. Perform initial graph analysis (centrality, clustering)
  6. Identify key nodes and structural patterns
  7. Verify graph consistency and source grounding
- **Output**: Initial knowledge graph with provenance tracking

### 4. Recursive Graph Expansion
- **Input**: Initial knowledge graph
- **Process**:
  1. Identify areas for further exploration (low connectivity, high centrality)
  2. Generate questions to explore these areas
  3. Process Gemini responses to these questions
  4. Extract new entities and relationships
  5. Ground new extractions in source text
  6. Integrate verified new knowledge into the graph
  7. Update provenance tracking for new elements
  8. Repeat until sufficient coverage is achieved
- **Output**: Expanded knowledge graph with comprehensive provenance tracking

### 5. Meta-graph Creation
- **Input**: Expanded knowledge graph
- **Process**:
  1. Identify clusters of related entities
  2. Generate meta-concepts for each cluster
  3. Define relationships between meta-concepts
  4. Create bidirectional links between meta-concepts and original entities
  5. Validate meta-graph consistency
  6. Preserve evidence links from original entities to source text
  7. Verify that all meta-concepts have sufficient grounding
- **Output**: Meta-graph with links to the detailed graph and provenance data

### 6. Theory & Hypothesis Generation
- **Input**: Expanded graph and meta-graph
- **Process**:
  1. Identify patterns in the graph structure
  2. Generate theories explaining these patterns
  3. Link theories to supporting evidence in source text
  4. Formulate testable hypotheses
  5. Evaluate hypotheses against existing data
  6. Track evidence for each hypothesis
  7. Refine theories based on evaluation and evidence
  8. Verify all theories have adequate source support
- **Output**: Theories and hypotheses with explicit supporting evidence

### 7. Output Generation
- **Input**: Knowledge graph, meta-graph, theories, and hypotheses with provenance
- **Process**:
  1. Determine appropriate output format based on domain
  2. Generate main document with insights and findings
  3. Insert source citations for all claims
  4. Create visualizations of the graph and meta-graph
  5. Compile supporting evidence and examples
  6. Include critical evaluation and limitations
  7. Generate evidence index linking claims to source text
- **Output**: Final report with visualizations, citations, and evidence index

## Hallucination Mitigation Checkpoints

### Grounding Validation (After Extraction)
- Verify all extracted entities and relationships exist in source text
- Calculate confidence scores based on textual evidence
- Reject or flag extractions without clear source support
- Maintain direct links to source passages

### Provenance Tracking (During Graph Construction)
- Attach source segment IDs to all graph elements
- Record extraction confidence scores
- Maintain extraction timestamps and model details
- Create audit trail for all information

### Verification & Evidence (During Expansion)
- Validate new additions against source text
- Require minimum confidence threshold for inclusion
- Link all inferences to supporting evidence
- Track inference chains for complex reasoning

### Evidence Validation (During Theory Generation)
- Require multiple evidence points for theory formation
- Calculate evidence coverage metrics
- Flag theories with weak evidential support
- Maintain explicit links to all supporting passages

### Source References (During Output Generation)
- Generate citations for all claims
- Create evidence index for fact-checking
- Include confidence levels in output
- Provide direct links to source material

## Control Flow

- The system will process steps 1-3 sequentially for initial graph construction
- Step 4 is iterative and will continue until a termination condition is met:
  - Reaching a predefined number of iterations
  - Minimal new knowledge being added
  - User interruption
- Each step includes verification checkpoints to ensure data quality
- Steps 5-7 are executed after the graph expansion phase is complete

## Error Handling

- LLM API failures will trigger retries with exponential backoff
- Parsing errors will be logged and problematic segments flagged for review
- Inconsistencies in the knowledge graph will be reported and, where possible, automatically resolved
- All operations will maintain checkpoints to allow resuming from failures
- Provenance tracking enables identification of problematic data sources

## User Interaction Points

- Initial configuration (language, LLM provider, analysis depth)
- Optional domain-specific guidance at the start
- Progress monitoring during processing
- Review of intermediate outputs (optional)
- Final output format selection
- Evidence review and validation

## Specialized Gemini Model Usage

- **gemini-2.0-flash**: Used for simple extraction tasks and routine operations
- **gemini-2.0-flash-thinking-exp-01-21**: Used for complex reasoning tasks like theory generation
- **gemini-2.0-pro-exp-02-05**: Used for critical tasks requiring high accuracy