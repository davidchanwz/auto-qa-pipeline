#!/usr/bin/env python3
"""
Test scenarios where the parent-stealing prevention fix might create problems:
1. Similar parents created instead of merging
2. Blocked valid parent assignments
"""

from collections import defaultdict
from classes import Code, Codebook, Operation, OperationType, Function


def test_similar_parents_scenario():
    """Test scenario for similar parents being created"""
    print("Testing similar parents scenario...")

    codebook = Codebook()

    # Create existing parent with 2 children
    existing_parent = Code(
        code_id=1,
        name="Government Corruption",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article1": ["Evidence of government corruption"]}),
    )

    child1 = Code(
        code_id=2,
        name="Bribery",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article1": ["Evidence of bribery"]}),
    )

    child2 = Code(
        code_id=3,
        name="Nepotism",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article1": ["Evidence of nepotism"]}),
    )

    # Add codes to codebook
    codebook.add_code(existing_parent)
    codebook.add_code(child1)
    codebook.add_code(child2)

    print(
        f"Initial state: Parent '{existing_parent.name}' has {len([c for c in codebook.codes.values() if c.parent_code_id == 1])} children"
    )

    # New candidate code similar to child1 (Bribery)
    candidate_code = Code(
        code_id=4,
        name="Political Bribes",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article2": ["Evidence of political bribes"]}),
    )
    codebook.add_code(candidate_code)

    # CREATE_PARENT operation targeting child1 (Bribery)
    create_parent_op = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=2,
        source_code_id=4,
        new_code_data={
            "code_id": 5,
            "name": "Corruption Payments",
            "function": Function.PROBLEM_DEFINITION.value,
            "evidence": defaultdict(list),
        },
        reasoning="Both Bribery and Political Bribes are specific types of corruption payments",
    )

    print(f"\nExecuting CREATE_PARENT operation...")
    result = codebook.execute_operation(create_parent_op)
    print(f"Operation result: {result}")

    # Check final state
    print(f"\nFinal hierarchy:")
    for code in codebook.codes.values():
        parent_name = (
            codebook.codes[code.parent_code_id].name if code.parent_code_id else "ROOT"
        )
        print(f"  {code.name} (id={code.code_id}) -> parent: {parent_name}")

    # Count children of each parent
    parent_child_counts = {}
    for code in codebook.codes.values():
        if code.parent_code_id:
            parent_id = code.parent_code_id
            parent_name = codebook.codes[parent_id].name
            parent_child_counts[parent_name] = (
                parent_child_counts.get(parent_name, 0) + 1
            )

    print(f"\nParent-child counts:")
    for parent_name, count in parent_child_counts.items():
        print(f"  {parent_name}: {count} children")

    # Identify potential problems
    corruption_parents = [
        name for name in parent_child_counts.keys() if "Corruption" in name
    ]
    if len(corruption_parents) > 1:
        print(
            f"\n⚠️  POTENTIAL PROBLEM: Multiple similar parents created: {corruption_parents}"
        )
        print(
            f"    This might indicate that the fix prevented a valid merge/reorganization"
        )

    return codebook


if __name__ == "__main__":
    test_similar_parents_scenario()
