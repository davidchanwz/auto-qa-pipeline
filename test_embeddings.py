#!/usr/bin/env python3

"""
Test script to verify that embeddings are being generated for codes
"""

import json
from config import LLMConfig
from services.agent import Agent
from services.strategic import StrategicLayer
from services.exploration import ExplorationLayer
from classes import ResearchFramework, Code, Function
from collections import defaultdict
from datetime import datetime


def test_embedding_generation():
    """
    Test that embeddings are generated for codes
    """
    print("=== Testing Embedding Generation ===\n")

    # Initialize components
    print("1. Initializing components...")
    agent = Agent()  # Use default config
    strategic = StrategicLayer()  # Uses default Entman framework
    exploration = ExplorationLayer(agent, strategic)

    print("   ✓ Components initialized")

    # Test direct embedding generation
    print("\n2. Testing direct embedding generation...")

    # Create a test code
    evidence = defaultdict(list)
    evidence[1] = [
        "Workers struggled with communication in remote settings",
        "Video calls were often disrupted",
    ]

    test_code = Code(
        code_id=None,
        name="Remote Communication Challenges",
        function=Function.DESCRIPTIVE,
        evidence=evidence,
        embedding=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    print(f"   Original code: {test_code.name}")
    print(f"   Has embedding: {test_code.embedding is not None}")

    # Generate embedding
    code_with_embedding = agent.add_embedding(test_code)

    print(f"   After embedding generation:")
    print(f"   Has embedding: {code_with_embedding.embedding is not None}")
    if code_with_embedding.embedding:
        print(f"   Embedding dimensions: {len(code_with_embedding.embedding)}")
        print(f"   First 5 values: {code_with_embedding.embedding[:5]}")

    # Test with article analysis
    print("\n3. Testing embedding generation during article analysis...")

    sample_article = {
        "id": 1,
        "title": "Remote Work Productivity Study",
        "content": "Research shows that remote workers face significant challenges with productivity. Communication barriers, technological issues, and work-life balance problems were the most commonly reported issues. However, many workers also reported increased flexibility and job satisfaction.",
    }

    # Analyze article (this should generate codes with embeddings)
    candidate_codes = exploration.analyze_article(sample_article)

    print(f"   Generated {len(candidate_codes)} candidate codes:")
    for i, code in enumerate(candidate_codes):
        print(f"   Code {i+1}: {code.name}")
        print(f"     Function: {code.function.value}")
        print(f"     Has embedding: {code.embedding is not None}")
        if code.embedding:
            print(f"     Embedding dimensions: {len(code.embedding)}")
        print(
            f"     Evidence count: {len(list(code.evidence.values())[0]) if code.evidence else 0}"
        )
        print()

    # Test full pipeline
    print("4. Testing full incremental analysis pipeline...")
    articles = [
        {
            "id": 1,
            "title": "Remote Work Challenges",
            "content": "The pandemic forced rapid remote work adoption. Communication, collaboration, and work-life balance emerged as key challenges.",
        },
        {
            "id": 2,
            "title": "Digital Learning Adaptation",
            "content": "Educational institutions struggled with online learning. Technology barriers and student engagement were major concerns.",
        },
    ]

    # Run full analysis
    final_codebook = exploration.analyze_articles(articles)

    # Check final codebook for embeddings
    print(f"\n5. Final codebook analysis:")
    stats = final_codebook.get_statistics()
    print(f"   Total codes: {stats['total_codes']}")

    codes_with_embeddings = 0
    for code in final_codebook.codes:
        if code.embedding is not None:
            codes_with_embeddings += 1

    print(
        f"   Codes with embeddings: {codes_with_embeddings}/{len(final_codebook.codes)}"
    )
    print(
        f"   Embedding coverage: {codes_with_embeddings/len(final_codebook.codes)*100:.1f}%"
        if final_codebook.codes
        else "N/A"
    )

    # Save test results
    exploration.save_updated_codebook(
        final_codebook, "test_codebook_with_embeddings.json"
    )
    session_log_path = exploration.finalize_session()

    print(f"\n✓ Embedding test completed!")
    print(f"  Check logs for detailed embedding generation process:")
    print(f"  - {exploration.log_file}")
    print(f"  - {session_log_path}")
    print(f"  - test_codebook_with_embeddings.json")


if __name__ == "__main__":
    test_embedding_generation()
