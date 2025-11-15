"""
Test script for new bidirectional merge operations

This script tests the new operation types:
- MERGE_TO_EXISTING
- MERGE_TO_CANDIDATE
- CREATE_PARENT
- DELETE_CODE
"""

from classes import Code, Codebook, Function, OperationType, Operation
from collections import defaultdict
from datetime import datetime


def test_merge_to_existing():
    """Test merging candidate into existing code"""
    print("Testing MERGE_TO_EXISTING...")

    # Create codebook with existing code
    codebook = Codebook()
    existing_code = Code(
        code_id=1,
        name="Media Problems",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {1: ["Traditional media bias"]}),
        embedding=[0.1, 0.2, 0.3],
    )
    codebook.add_code(existing_code)

    # Create operation to merge candidate into existing
    merged_evidence = defaultdict(
        list, {1: ["Traditional media bias"], 2: ["Social media misinformation"]}
    )

    operation = Operation(
        operation_type=OperationType.MERGE_TO_EXISTING,
        target_code_id=1,
        new_code_data={
            "evidence": merged_evidence,
            "name": "Media Problems (enhanced)",
            "updated_at": datetime.utcnow(),
        },
        confidence=0.8,
        reasoning="Test merge to existing",
    )

    success = codebook.execute_operation(operation)
    print(f"Operation success: {success}")
    print(f"Updated code: {codebook.codes[1].name}")
    print(f"Evidence count: {len(list(codebook.codes[1].evidence.values())[0])}")
    print()


def test_create_parent():
    """Test creating parent code with children"""
    print("Testing CREATE_PARENT...")

    # Create codebook with existing code
    codebook = Codebook()
    existing_code = Code(
        code_id=1,
        name="Social Media Issues",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {1: ["Facebook problems"]}),
        embedding=[0.1, 0.2, 0.3],
    )
    codebook.add_code(existing_code)

    # Add candidate code
    candidate_code = Code(
        code_id=2,
        name="Traditional Media Bias",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {2: ["TV news bias"]}),
        embedding=[0.2, 0.3, 0.4],
    )
    codebook.add_code(candidate_code)

    # Create parent operation
    operation = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=1,  # existing code
        source_code_id=2,  # candidate code
        new_code_data={
            "code_id": None,
            "name": "Media Information Problems",
            "function": Function.PROBLEM_DEFINITION,
            "evidence": defaultdict(list),
            "embedding": [0.15, 0.25, 0.35],  # average embedding
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parent_code_id": None,
        },
        confidence=0.9,
        reasoning="Test create parent",
    )

    success = codebook.execute_operation(operation)
    print(f"Operation success: {success}")

    # Check results
    print(f"Total codes: {len(codebook.codes)}")
    parent_code = codebook.codes[3]  # Should be the new parent
    print(f"Parent code: {parent_code.name}")
    print(f"Child 1 parent_id: {codebook.codes[1].parent_code_id}")
    print(f"Child 2 parent_id: {codebook.codes[2].parent_code_id}")
    print()


def test_delete_code():
    """Test deleting a code"""
    print("Testing DELETE_CODE...")

    # Create codebook with code to delete
    codebook = Codebook()
    code_to_delete = Code(
        code_id=1,
        name="Test Code",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {1: ["Some evidence"]}),
        embedding=[0.1, 0.2, 0.3],
    )
    codebook.add_code(code_to_delete)

    print(f"Codes before delete: {len(codebook.codes)}")

    # Create delete operation
    operation = Operation(
        operation_type=OperationType.DELETE_CODE,
        target_code_id=1,
        confidence=1.0,
        reasoning="Test delete",
    )

    success = codebook.execute_operation(operation)
    print(f"Operation success: {success}")
    print(f"Codes after delete: {len(codebook.codes)}")
    print()


if __name__ == "__main__":
    print("=== Testing New Codebook Operations ===\n")

    test_merge_to_existing()
    test_create_parent()
    test_delete_code()

    print("=== All Tests Complete ===")
