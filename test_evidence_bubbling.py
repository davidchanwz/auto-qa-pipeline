#!/usr/bin/env python3
"""
Test evidence bubbling for MERGE_TO_EXISTING and MERGE_TO_CANDIDATE operations
"""

from collections import defaultdict
from classes import Code, Codebook, Operation, OperationType, Function
from datetime import datetime


def test_merge_to_existing_evidence_bubbling():
    """Test that MERGE_TO_EXISTING bubbles evidence to parent"""
    print("Testing MERGE_TO_EXISTING evidence bubbling...")

    codebook = Codebook()

    # Create parent code
    parent = Code(
        code_id=1,
        name="Social Issues",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article1": ["General social problems"]}),
    )

    # Create child code that will be the merge target
    existing_child = Code(
        code_id=2,
        name="Economic Issues",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article2": ["Economic problem A"]}),
    )

    # Add codes to codebook
    codebook.add_code(parent)
    codebook.add_code(existing_child)

    print(f"Before merge:")
    print(f"  Parent '{parent.name}' evidence: {dict(parent.evidence)}")
    print(f"  Child '{existing_child.name}' evidence: {dict(existing_child.evidence)}")

    # MERGE_TO_EXISTING operation - merges candidate evidence into existing child
    merge_operation = Operation(
        operation_type=OperationType.MERGE_TO_EXISTING,
        target_code_id=2,  # Economic Issues
        new_code_data={
            "evidence": defaultdict(
                list,
                {
                    "article2": [
                        "Economic problem A",
                        "Economic problem B",
                    ],  # Merged evidence
                    "article3": ["New economic evidence"],
                },
            ),
            "name": "Economic & Financial Issues",  # Updated name
        },
        reasoning="Merging candidate into existing",
    )

    result = codebook.execute_operation(merge_operation)
    print(f"\nMERGE_TO_EXISTING result: {result}")

    # Check results
    updated_parent = codebook.codes[1]
    updated_child = codebook.codes[2]

    print(f"\nAfter merge:")
    print(f"  Parent '{updated_parent.name}' evidence: {dict(updated_parent.evidence)}")
    print(f"  Child '{updated_child.name}' evidence: {dict(updated_child.evidence)}")

    # Verify evidence bubbling
    parent_evidence_count = sum(
        len(quotes) for quotes in updated_parent.evidence.values()
    )
    child_evidence_count = sum(
        len(quotes) for quotes in updated_child.evidence.values()
    )

    print(f"\nEvidence counts:")
    print(f"  Parent: {parent_evidence_count} pieces")
    print(f"  Child: {child_evidence_count} pieces")

    # Parent should have original evidence + child's evidence
    expected_parent_evidence = 1 + 3  # 1 original + 3 from child
    if parent_evidence_count >= expected_parent_evidence:
        print(
            f"  ✅ Evidence bubbling successful: Parent has {parent_evidence_count} >= {expected_parent_evidence}"
        )
    else:
        print(
            f"  ❌ Evidence bubbling failed: Parent has {parent_evidence_count} < {expected_parent_evidence}"
        )

    return codebook


def test_create_code_evidence_bubbling():
    """Test that CREATE_CODE (used in MERGE_TO_CANDIDATE) bubbles evidence to parent"""
    print("\n" + "=" * 80)
    print("Testing CREATE_CODE evidence bubbling (used in MERGE_TO_CANDIDATE)...")

    codebook = Codebook()

    # Create parent code
    parent = Code(
        code_id=1,
        name="Health Issues",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article1": ["General health problems"]}),
    )

    # Add parent to codebook
    codebook.add_code(parent)

    print(f"Before CREATE_CODE:")
    print(f"  Parent '{parent.name}' evidence: {dict(parent.evidence)}")

    # CREATE_CODE operation - creates new child with evidence
    create_operation = Operation(
        operation_type=OperationType.CREATE_CODE,
        new_code_data={
            "code_id": 2,
            "name": "Mental Health Issues",
            "function": Function.PROBLEM_DEFINITION.value,
            "parent_code_id": 1,
            "evidence": defaultdict(
                list,
                {
                    "article2": ["Mental health issue A", "Mental health issue B"],
                    "article3": ["Depression statistics"],
                },
            ),
        },
        reasoning="Creating new child code",
    )

    result = codebook.execute_operation(create_operation)
    print(f"\nCREATE_CODE result: {result}")

    # Check results
    updated_parent = codebook.codes[1]
    new_child = codebook.codes[2]

    print(f"\nAfter CREATE_CODE:")
    print(f"  Parent '{updated_parent.name}' evidence: {dict(updated_parent.evidence)}")
    print(f"  Child '{new_child.name}' evidence: {dict(new_child.evidence)}")

    # Verify evidence bubbling
    parent_evidence_count = sum(
        len(quotes) for quotes in updated_parent.evidence.values()
    )
    child_evidence_count = sum(len(quotes) for quotes in new_child.evidence.values())

    print(f"\nEvidence counts:")
    print(f"  Parent: {parent_evidence_count} pieces")
    print(f"  Child: {child_evidence_count} pieces")

    # Parent should have original evidence + child's evidence
    expected_parent_evidence = 1 + 3  # 1 original + 3 from child
    if parent_evidence_count >= expected_parent_evidence:
        print(
            f"  ✅ Evidence bubbling successful: Parent has {parent_evidence_count} >= {expected_parent_evidence}"
        )
    else:
        print(
            f"  ❌ Evidence bubbling failed: Parent has {parent_evidence_count} < {expected_parent_evidence}"
        )

    return codebook


def test_nested_evidence_bubbling():
    """Test evidence bubbling in nested hierarchies"""
    print("\n" + "=" * 80)
    print("Testing nested evidence bubbling...")

    codebook = Codebook()

    # Create 3-level hierarchy
    root = Code(
        code_id=1,
        name="Social Problems",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article1": ["Root level evidence"]}),
    )

    middle = Code(
        code_id=2,
        name="Urban Issues",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article2": ["Urban problems overview"]}),
    )

    leaf = Code(
        code_id=3,
        name="Traffic Problems",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=2,
        evidence=defaultdict(list, {"article3": ["Traffic congestion data"]}),
    )

    # Add all codes
    for code in [root, middle, leaf]:
        codebook.add_code(code)

    print(f"Initial hierarchy evidence:")
    print(f"  Root '{root.name}': {dict(root.evidence)}")
    print(f"  Middle '{middle.name}': {dict(middle.evidence)}")
    print(f"  Leaf '{leaf.name}': {dict(leaf.evidence)}")

    # Merge operation on leaf node
    merge_operation = Operation(
        operation_type=OperationType.MERGE_TO_EXISTING,
        target_code_id=3,  # Traffic Problems
        new_code_data={
            "evidence": defaultdict(
                list,
                {
                    "article3": ["Traffic congestion data", "New traffic study"],
                    "article4": ["Parking issues"],
                },
            ),
            "name": "Traffic & Parking Problems",
        },
        reasoning="Merging traffic data",
    )

    result = codebook.execute_operation(merge_operation)
    print(f"\nMerge operation result: {result}")

    # Check final state
    final_root = codebook.codes[1]
    final_middle = codebook.codes[2]
    final_leaf = codebook.codes[3]

    print(f"\nFinal hierarchy evidence:")
    print(f"  Root '{final_root.name}': {dict(final_root.evidence)}")
    print(f"  Middle '{final_middle.name}': {dict(final_middle.evidence)}")
    print(f"  Leaf '{final_leaf.name}': {dict(final_leaf.evidence)}")

    # Verify evidence counts
    root_count = sum(len(quotes) for quotes in final_root.evidence.values())
    middle_count = sum(len(quotes) for quotes in final_middle.evidence.values())
    leaf_count = sum(len(quotes) for quotes in final_leaf.evidence.values())

    print(f"\nEvidence counts:")
    print(f"  Root: {root_count} pieces")
    print(f"  Middle: {middle_count} pieces (should have bubbled from leaf)")
    print(f"  Leaf: {leaf_count} pieces")

    # Middle should now have evidence from leaf
    if middle_count > 1:  # Original 1 + bubbled evidence
        print(f"  ✅ Evidence bubbled up from leaf to middle")
    else:
        print(f"  ❌ Evidence did not bubble up to middle parent")

    return codebook


if __name__ == "__main__":
    test_merge_to_existing_evidence_bubbling()
    test_create_code_evidence_bubbling()
    test_nested_evidence_bubbling()
