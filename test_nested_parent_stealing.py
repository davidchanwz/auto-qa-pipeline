#!/usr/bin/env python3
"""
Test script to verify parent-stealing prevention in nested hierarchy scenarios.
"""

import sys
import os
from datetime import datetime
from collections import defaultdict

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes import Code, Function, Codebook, Operation, OperationType


def test_nested_parent_stealing_scenario():
    """Test parent-stealing prevention with nested hierarchy"""
    print("Testing nested parent-stealing scenario...")
    print("=" * 60)

    # Create a nested hierarchy:
    # Root Parent
    #   ├─ Middle Parent
    #   │   ├─ Child Code 1 (will be stolen)
    #   │   └─ Child Code 2 (will remain)
    #   └─ Sibling Code

    codebook = Codebook()

    # Root parent
    root_parent = Code(
        code_id=1,
        name="Root Parent Category",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=None,
    )
    codebook.add_code(root_parent)

    # Middle parent (child of root)
    middle_parent = Code(
        code_id=2,
        name="Middle Parent Category",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=1,  # Child of root parent
    )
    codebook.add_code(middle_parent)

    # Sibling code (also child of root)
    sibling_code = Code(
        code_id=3,
        name="Sibling Code",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {1: ["Sibling evidence"]}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=1,  # Child of root parent
    )
    codebook.add_code(sibling_code)

    # Child 1 of middle parent - this will be "stolen"
    child1 = Code(
        code_id=4,
        name="Child Code 1",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {2: ["Evidence 1"]}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=2,  # Child of middle parent
    )
    codebook.add_code(child1)

    # Child 2 of middle parent - will remain
    child2 = Code(
        code_id=5,
        name="Child Code 2",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {3: ["Evidence 2"]}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        parent_code_id=2,  # Child of middle parent
    )
    codebook.add_code(child2)

    print("INITIAL NESTED STATE:")
    print_parent_child_relationships(codebook)

    # CREATE_PARENT targeting child1 (which has middle parent 2, which has root parent 1)
    candidate_operation = Operation(
        operation_type=OperationType.CREATE_CODE,
        new_code_data={
            "code_id": None,
            "name": "Similar Candidate Code",
            "function": Function.PROBLEM_DEFINITION,
            "evidence": defaultdict(list, {4: ["Candidate evidence"]}),
            "embedding": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parent_code_id": None,
        },
        confidence=0.8,
        reasoning="Creating candidate similar to existing nested child",
    )

    steal_parent_operation = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=4,  # child1 - existing nested code
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
        reasoning="LLM decided to create parent for nested child + candidate",
    )

    operations = [candidate_operation, steal_parent_operation]
    candidate_code_id = None

    for i, operation in enumerate(operations):
        print(f"\nExecuting operation {i+1}: {operation.operation_type.value}")
        if operation.operation_type == OperationType.CREATE_PARENT:
            print(
                f"  Target: {operation.target_code_id} ('{codebook.codes[operation.target_code_id].name}')"
            )
            existing_parent = codebook.codes[operation.target_code_id].parent_code_id
            if existing_parent:
                parent_name = codebook.codes[existing_parent].name
                print(f"  Target's current parent: {existing_parent} ('{parent_name}')")
            else:
                print(f"  Target's current parent: None (root)")

        success = codebook.execute_operation(operation)

        if (
            success
            and operation.operation_type == OperationType.CREATE_CODE
            and operation.new_code_data
        ):
            max_id = max(codebook.codes.keys()) if codebook.codes else 0
            candidate_code_id = max_id
            print(f"  Created candidate code with ID: {candidate_code_id}")

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

    print(f"\nFINAL NESTED STATE:")
    print_parent_child_relationships(codebook)

    # Analysis
    children_count = defaultdict(int)
    for code_id, code in codebook.codes.items():
        if code.parent_code_id is not None:
            children_count[code.parent_code_id] += 1

    print(f"\nNESTED HIERARCHY ANALYSIS:")
    single_child_parents = []
    for parent_id, count in children_count.items():
        parent_name = codebook.codes[parent_id].name
        print(f"  Parent {parent_id} '{parent_name}': {count} children")
        if count == 1:
            single_child_parents.append((parent_id, parent_name))
            print(f"    ⚠️  SINGLE CHILD PARENT")
        elif count >= 2:
            print(f"    ✅ Multiple children")

    if single_child_parents:
        print(
            f"\n❌ NESTED ISSUE: {len(single_child_parents)} parent(s) left with only 1 child"
        )
    else:
        print(f"\n✅ Nested hierarchy properly maintained - no single-child parents")


def print_parent_child_relationships(codebook):
    """Helper to print parent-child relationships with nesting"""
    children_by_parent = defaultdict(list)
    root_codes = []

    for code_id, code in codebook.codes.items():
        if code.parent_code_id is None:
            root_codes.append((code_id, code.name))
        else:
            children_by_parent[code.parent_code_id].append((code_id, code.name))

    def print_hierarchy(code_id, name, depth=0):
        indent = "  " * depth
        print(f"{indent}{code_id}: '{name}'")
        children = children_by_parent.get(code_id, [])
        for child_id, child_name in children:
            print_hierarchy(child_id, child_name, depth + 1)

    print(f"Hierarchy:")
    for code_id, name in root_codes:
        print_hierarchy(code_id, name)

    total_codes = len(codebook.codes)
    parent_codes = len(children_by_parent)
    child_codes = sum(len(children) for children in children_by_parent.values())

    print(
        f"Summary: {total_codes} total, {parent_codes} parents, {child_codes} children, {len(root_codes)} roots"
    )


if __name__ == "__main__":
    test_nested_parent_stealing_scenario()
    print("\n🎯 Nested test completed!")
