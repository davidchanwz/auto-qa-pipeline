#!/usr/bin/env python3
"""
Test script to verify the parent-stealing scenario where an existing code
with a parent gets moved to a new parent, leaving the original parent orphaned.
"""

import sys
import os
from datetime import datetime
from collections import defaultdict

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes import Code, Function, Codebook, Operation, OperationType


def test_parent_stealing_scenario():
    """Test parent-stealing scenario"""
    print("Testing parent-stealing scenario...")
    print("=" * 50)

    # Create a codebook with existing parent-child structure
    codebook = Codebook()

    # Create original parent with 2 children
    original_parent = Code(
        code_id=1,
        name="Original Parent Category",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=None,
    )
    codebook.add_code(original_parent)

    # Child 1 - this will be "stolen" by new parent
    child1 = Code(
        code_id=2,
        name="Child Code 1",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {1: ["Evidence 1"]}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=1,  # Child of original parent
    )
    codebook.add_code(child1)

    # Child 2 - will remain with original parent
    child2 = Code(
        code_id=3,
        name="Child Code 2",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {2: ["Evidence 2"]}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=1,  # Child of original parent
    )
    codebook.add_code(child2)

    print("INITIAL STATE:")
    print_parent_child_relationships(codebook)

    # Now simulate CREATE_PARENT where child1 gets moved to new parent
    # This simulates: candidate_code similar to child1, LLM decides CREATE_PARENT

    # Step 1: Create candidate code (similar to child1)
    candidate_operation = Operation(
        operation_type=OperationType.CREATE_CODE,
        new_code_data={
            "code_id": None,
            "name": "Similar Candidate Code",
            "function": Function.PROBLEM_DEFINITION,
            "evidence": defaultdict(list, {3: ["Candidate evidence"]}),
            "embedding": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parent_code_id": None,
        },
        confidence=0.8,
        reasoning="Creating candidate similar to existing child",
    )

    # Step 2: CREATE_PARENT - this will steal child1 from original parent
    steal_parent_operation = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=2,  # child1 - existing code that already has parent!
        source_code_id=None,  # Will be set to candidate after creation
        new_code_data={
            "code_id": None,
            "name": "New Stealing Parent",
            "function": Function.PROBLEM_DEFINITION,
            "evidence": defaultdict(list),
            "embedding": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parent_code_id": None,
        },
        confidence=0.8,
        reasoning="LLM decided to create parent for existing child + candidate",
    )

    operations = [candidate_operation, steal_parent_operation]

    # Execute operations with same logic as exploration layer
    candidate_code_id = None

    for i, operation in enumerate(operations):
        print(f"\nExecuting operation {i+1}: {operation.operation_type.value}")
        if operation.operation_type == OperationType.CREATE_PARENT:
            print(
                f"  Target: {operation.target_code_id} ('{codebook.codes[operation.target_code_id].name}')"
            )
            existing_parent = codebook.codes[operation.target_code_id].parent_code_id
            print(f"  Target's current parent: {existing_parent}")

        success = codebook.execute_operation(operation)

        # Track newly created codes
        if (
            success
            and operation.operation_type == OperationType.CREATE_CODE
            and operation.new_code_data
        ):
            max_id = max(codebook.codes.keys()) if codebook.codes else 0
            candidate_code_id = max_id
            print(f"  Created candidate code with ID: {candidate_code_id}")

        # Handle delayed parent-child linking
        if (
            success
            and operation.operation_type == OperationType.CREATE_PARENT
            and candidate_code_id is not None
        ):
            parent_id = max(codebook.codes.keys())
            if candidate_code_id in codebook.codes and parent_id in codebook.codes:
                candidate_code = codebook.codes[candidate_code_id]
                candidate_code.parent_code_id = parent_id
                candidate_code.updated_at = datetime.utcnow()
                print(
                    f"  Linked candidate {candidate_code_id} to new parent {parent_id}"
                )

            candidate_code_id = None

        print(f"  Operation {'succeeded' if success else 'failed'}")

    print(f"\nFINAL STATE:")
    print_parent_child_relationships(codebook)

    # Check for single-child parents (orphaned parents)
    children_count = defaultdict(int)
    for code_id, code in codebook.codes.items():
        if code.parent_code_id is not None:
            children_count[code.parent_code_id] += 1

    print(f"\nPARENT ANALYSIS:")
    single_child_parents = []
    for parent_id, count in children_count.items():
        parent_name = codebook.codes[parent_id].name
        print(f"  Parent {parent_id} '{parent_name}': {count} children")
        if count == 1:
            single_child_parents.append((parent_id, parent_name))
            print(f"    ⚠️  SINGLE CHILD PARENT (potentially orphaned)")
        elif count >= 2:
            print(f"    ✅ Multiple children")

    if single_child_parents:
        print(
            f"\n❌ ISSUE CONFIRMED: {len(single_child_parents)} parent(s) left with only 1 child"
        )
        for parent_id, parent_name in single_child_parents:
            print(f"   - Parent {parent_id}: '{parent_name}'")
    else:
        print(f"\n✅ No single-child parents found")


def print_parent_child_relationships(codebook):
    """Helper to print parent-child relationships"""
    children_by_parent = defaultdict(list)
    root_codes = []

    for code_id, code in codebook.codes.items():
        if code.parent_code_id is None:
            root_codes.append((code_id, code.name))
        else:
            children_by_parent[code.parent_code_id].append((code_id, code.name))

    print(f"Root codes: {len(root_codes)}")
    for code_id, name in root_codes:
        print(f"  {code_id}: '{name}'")
        children = children_by_parent.get(code_id, [])
        for child_id, child_name in children:
            print(f"    └─ {child_id}: '{child_name}'")

    total_codes = len(codebook.codes)
    parent_codes = len(children_by_parent)
    child_codes = sum(len(children) for children in children_by_parent.values())

    print(
        f"Summary: {total_codes} total, {parent_codes} parents, {child_codes} children, {len(root_codes)} roots"
    )


if __name__ == "__main__":
    test_parent_stealing_scenario()
    print("\n🎯 Test completed!")
