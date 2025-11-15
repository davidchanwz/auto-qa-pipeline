#!/usr/bin/env python3
"""
Comprehensive test demonstrating all evidence bubbling scenarios:
- MERGE_TO_EXISTING bubbles evidence to parent
- CREATE_CODE (MERGE_TO_CANDIDATE) bubbles evidence to parent
- CREATE_PARENT aggregates evidence from children AND bubbles to parent
"""

from collections import defaultdict
from classes import Code, Codebook, Operation, OperationType, Function


def test_comprehensive_evidence_bubbling():
    """Test all evidence bubbling scenarios together"""
    print("=== Comprehensive Evidence Bubbling Test ===")

    codebook = Codebook()

    # Create root parent
    root = Code(
        code_id=1,
        name="Research Topics",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article1": ["Research overview"]}),
    )
    codebook.add_code(root)

    # Test 1: CREATE_CODE with evidence bubbling
    print("\n1. Testing CREATE_CODE evidence bubbling...")
    create_op = Operation(
        operation_type=OperationType.CREATE_CODE,
        new_code_data={
            "code_id": 2,
            "name": "Health Research",
            "function": Function.PROBLEM_DEFINITION.value,
            "parent_code_id": 1,
            "evidence": defaultdict(
                list, {"article2": ["Health study A", "Health study B"]}
            ),
        },
    )
    codebook.execute_operation(create_op)

    print(f"  Root evidence after CREATE_CODE: {dict(codebook.codes[1].evidence)}")

    # Test 2: MERGE_TO_EXISTING with evidence bubbling
    print("\n2. Testing MERGE_TO_EXISTING evidence bubbling...")
    merge_op = Operation(
        operation_type=OperationType.MERGE_TO_EXISTING,
        target_code_id=2,  # Health Research
        new_code_data={
            "evidence": defaultdict(
                list,
                {
                    "article2": ["Health study A", "Health study B", "Health study C"],
                    "article3": ["Mental health research"],
                },
            ),
            "name": "Health & Mental Health Research",
        },
    )
    codebook.execute_operation(merge_op)

    print(
        f"  Root evidence after MERGE_TO_EXISTING: {dict(codebook.codes[1].evidence)}"
    )

    # Test 3: CREATE_PARENT with evidence aggregation AND bubbling
    print("\n3. Testing CREATE_PARENT evidence aggregation and bubbling...")

    # Create another child for comparison
    child2 = Code(
        code_id=3,
        name="Social Research",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article4": ["Social study data"]}),
    )
    codebook.add_code(child2)

    # CREATE_PARENT targeting one of the children
    create_parent_op = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=2,  # Health & Mental Health Research
        source_code_id=3,  # Social Research
        new_code_data={
            "code_id": 4,
            "name": "Behavioral Research",
            "function": Function.PROBLEM_DEFINITION.value,
            "evidence": defaultdict(list, {"initial": ["Parent category evidence"]}),
        },
    )
    codebook.execute_operation(create_parent_op)

    print(f"  Root evidence after CREATE_PARENT: {dict(codebook.codes[1].evidence)}")
    print(
        f"  New parent 'Behavioral Research' evidence: {dict(codebook.codes[4].evidence)}"
    )

    # Test 4: Verify final hierarchy and evidence flow
    print("\n4. Final hierarchy and evidence summary:")

    def print_evidence_hierarchy(code, indent=0):
        prefix = "  " * indent
        evidence_count = sum(len(quotes) for quotes in code.evidence.values())
        children = [
            c for c in codebook.codes.values() if c.parent_code_id == code.code_id
        ]

        print(f"{prefix}{code.name} [{evidence_count} evidence pieces]")
        for child in children:
            print_evidence_hierarchy(child, indent + 1)

    root_codes = [c for c in codebook.codes.values() if c.parent_code_id is None]
    for root in root_codes:
        print_evidence_hierarchy(root)

    # Verify evidence accumulation at root
    root_evidence_count = sum(
        len(quotes) for quotes in codebook.codes[1].evidence.values()
    )
    print(f"\nRoot total evidence pieces: {root_evidence_count}")

    # Expected evidence flow:
    # 1. Initial: 1 piece
    # 2. CREATE_CODE: +2 pieces → 3 total
    # 3. MERGE_TO_EXISTING: +2 pieces → 5 total
    # 4. CREATE_PARENT: +1 piece from Social Research → 6 total

    if root_evidence_count >= 6:
        print(
            f"✅ All evidence bubbling successful! Root accumulated {root_evidence_count} pieces"
        )
    else:
        print(
            f"❌ Evidence bubbling incomplete. Expected ≥6, got {root_evidence_count}"
        )

    return codebook


if __name__ == "__main__":
    test_comprehensive_evidence_bubbling()
