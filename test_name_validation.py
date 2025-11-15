#!/usr/bin/env python3
"""
Test script to validate name handling in Code operations
"""

import sys
import os
from datetime import datetime
from collections import defaultdict

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes import Code, Function, Codebook, Operation, OperationType


def test_empty_name_validation():
    """Test that empty names are handled properly"""
    print("Testing empty name validation...")

    # Test 1: Code with empty name
    try:
        code1 = Code(
            code_id=1,
            name="",  # Empty name
            function=Function.PROBLEM_DEFINITION,
            evidence=defaultdict(list),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        print(f"✅ Code with empty name created: '{code1.name}'")
    except Exception as e:
        print(f"❌ Failed to create code with empty name: {e}")

    # Test 2: Code with None name
    try:
        code2 = Code(
            code_id=2,
            name=None,  # None name
            function=Function.CAUSAL_ATTRIBUTION,
            evidence=defaultdict(list),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        print(f"✅ Code with None name created: '{code2.name}'")
    except Exception as e:
        print(f"❌ Failed to create code with None name: {e}")

    # Test 3: Code with whitespace-only name
    try:
        code3 = Code(
            code_id=3,
            name="   ",  # Whitespace only
            function=Function.MORAL_EVALUATION,
            evidence=defaultdict(list),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        print(f"✅ Code with whitespace name created: '{code3.name}'")
    except Exception as e:
        print(f"❌ Failed to create code with whitespace name: {e}")


def test_merge_operation_names():
    """Test that merge operations preserve names properly"""
    print("\nTesting merge operation name handling...")

    # Create a codebook
    codebook = Codebook()

    # Add a code with a proper name
    existing_code = Code(
        code_id=1,
        name="Existing Code Name",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    codebook.add_code(existing_code)

    # Test merge operation with empty new_name
    operation = Operation(
        operation_type=OperationType.MERGE_TO_EXISTING,
        target_code_id=1,
        new_code_data={
            "name": "",  # Empty name
            "evidence": defaultdict(list),
            "updated_at": datetime.utcnow(),
        },
        confidence=0.8,
        reasoning="Test operation with empty name",
    )

    success = codebook.execute_operation(operation)
    if success:
        updated_code = codebook.codes[1]
        print(f"✅ Merge operation succeeded. Name: '{updated_code.name}'")
    else:
        print("❌ Merge operation failed")


def test_code_with_multiple_evidence():
    """Test creating code with multiple evidence sources"""
    print("\nTesting code with multiple evidence sources...")

    evidence = defaultdict(list)
    evidence[1] = ["Evidence from article 1", "More evidence from article 1"]
    evidence[2] = ["Evidence from article 2"]
    evidence[5] = ["Evidence from article 5", "Additional evidence from 5"]

    code = Code(
        code_id=10,
        name="Multi-Evidence Code",
        function=Function.TREATMENT_ADVOCACY,
        evidence=evidence,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    print(f"✅ Code created with evidence from {len(evidence)} articles")
    print(f"   Name: '{code.name}'")
    print(f"   Evidence articles: {list(evidence.keys())}")

    # Test that evidence from multiple sources doesn't affect name
    if code.name and code.name.strip():
        print("✅ Name preserved with multiple evidence sources")
    else:
        print("❌ Name lost with multiple evidence sources")


if __name__ == "__main__":
    test_empty_name_validation()
    test_merge_operation_names()
    test_code_with_multiple_evidence()
    print("\n🎉 All tests completed!")
