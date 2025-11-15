#!/usr/bin/env python3
"""
Test script to verify CREATE_PARENT operations create parents with 2 children
"""

import sys
import os
from datetime import datetime
from collections import defaultdict

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes import Code, Function, Codebook, Operation, OperationType


def test_create_parent_operation():
    """Test that CREATE_PARENT operations create parents with 2 children"""
    print("Testing CREATE_PARENT operation...")

    # Create a codebook with an existing code
    codebook = Codebook()

    existing_code = Code(
        code_id=1,
        name="Existing Test Code",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    existing_code.evidence[1] = ["Some evidence for existing code"]
    codebook.add_code(existing_code)

    # Simulate the CREATE_PARENT multi-step operation sequence
    operations = []

    # Step 1: Create candidate code
    candidate_operation = Operation(
        operation_type=OperationType.CREATE_CODE,
        new_code_data={
            "code_id": None,
            "name": "Candidate Test Code",
            "function": Function.PROBLEM_DEFINITION,
            "evidence": defaultdict(list, {2: ["Evidence from candidate"]}),
            "embedding": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parent_code_id": None,
        },
        confidence=0.8,
        reasoning="Test candidate creation",
    )

    # Step 2: Create parent code
    parent_operation = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=1,  # Existing code
        source_code_id=None,  # Will be set to candidate after creation
        new_code_data={
            "code_id": None,
            "name": "Parent Test Category",
            "function": Function.PROBLEM_DEFINITION,
            "evidence": defaultdict(list),
            "embedding": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parent_code_id": None,
        },
        confidence=0.8,
        reasoning="Test parent creation",
    )

    operations = [candidate_operation, parent_operation]

    print(f"Initial codes: {len(codebook.codes)}")

    # Simulate the update_codebook logic
    candidate_code_id = None

    for i, operation in enumerate(operations):
        print(f"\nExecuting operation {i+1}: {operation.operation_type.value}")

        success = codebook.execute_operation(operation)

        # Track newly created codes
        if (
            success
            and operation.operation_type == OperationType.CREATE_CODE
            and operation.new_code_data
        ):
            # Find the newly created code
            max_id = max(codebook.codes.keys()) if codebook.codes else 0
            candidate_code_id = max_id
            print(f"  Created candidate code with ID: {candidate_code_id}")

        # Handle delayed parent-child linking
        if (
            success
            and operation.operation_type == OperationType.CREATE_PARENT
            and candidate_code_id is not None
        ):
            # Link the recently created candidate to the parent
            parent_id = max(codebook.codes.keys())
            if candidate_code_id in codebook.codes and parent_id in codebook.codes:
                candidate_code = codebook.codes[candidate_code_id]
                candidate_code.parent_code_id = parent_id
                candidate_code.updated_at = datetime.utcnow()
                print(f"  Linked candidate {candidate_code_id} to parent {parent_id}")

            candidate_code_id = None

        print(f"  Operation {'succeeded' if success else 'failed'}")

    print(f"\nFinal codes: {len(codebook.codes)}")

    # Count children for each parent
    children_count = defaultdict(int)
    for code_id, code in codebook.codes.items():
        if code.parent_code_id is not None:
            children_count[code.parent_code_id] += 1

    print(f"Parents found: {len(children_count)}")
    for parent_id, count in children_count.items():
        parent_name = codebook.codes[parent_id].name
        print(f"  Parent {parent_id} '{parent_name}': {count} children")
        if count == 2:
            print("  ✅ SUCCESS: Parent has 2 children as expected")
        else:
            print("  ❌ FAILURE: Parent should have 2 children")

    # List all codes and their relationships
    print(f"\nAll codes:")
    for code_id, code in codebook.codes.items():
        parent_info = (
            f" (parent: {code.parent_code_id})" if code.parent_code_id else " (root)"
        )
        evidence_count = sum(len(v) for v in code.evidence.values())
        print(f"  {code_id}: '{code.name}'{parent_info} - {evidence_count} evidence")


if __name__ == "__main__":
    test_create_parent_operation()
    print("\n🎉 Test completed!")
