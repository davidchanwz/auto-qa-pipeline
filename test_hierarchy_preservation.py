#!/usr/bin/env python3
"""
Test the improved CREATE_PARENT logic that:
1. Maintains hierarchical chains (original_parent -> new_parent -> children)
2. Aggregates evidence from children into parent
"""

from collections import defaultdict
from classes import Code, Codebook, Operation, OperationType, Function


def test_hierarchical_preservation_and_evidence():
    """Test that CREATE_PARENT preserves hierarchy and aggregates evidence"""
    print("Testing hierarchical preservation and evidence aggregation...")

    codebook = Codebook()

    # Create existing parent with evidence
    existing_parent = Code(
        code_id=1,
        name="Government Issues",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article1": ["Government problems in general"]}),
    )

    # Create child with specific evidence
    existing_child = Code(
        code_id=2,
        name="Corruption Cases",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(
            list,
            {
                "article1": ["Specific corruption case A"],
                "article2": ["Corruption case B details"],
            },
        ),
    )

    # Create sibling to ensure parent isn't abandoned
    sibling = Code(
        code_id=3,
        name="Policy Issues",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article3": ["Policy problem evidence"]}),
    )

    # Add codes to codebook
    codebook.add_code(existing_parent)
    codebook.add_code(existing_child)
    codebook.add_code(sibling)

    print(f"Initial hierarchy:")
    print(f"  Government Issues -> [Corruption Cases, Policy Issues]")

    # Create candidate code with its own evidence
    candidate = Code(
        code_id=4,
        name="Bribery Scandals",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(
            list,
            {
                "article2": ["Bribery scandal details"],
                "article4": ["New bribery case evidence"],
            },
        ),
    )
    codebook.add_code(candidate)

    print(f"\nBefore CREATE_PARENT:")
    print(f"  Corruption Cases evidence: {dict(existing_child.evidence)}")
    print(f"  Bribery Scandals evidence: {dict(candidate.evidence)}")

    # CREATE_PARENT operation
    create_parent_op = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=2,  # Corruption Cases
        source_code_id=4,  # Bribery Scandals
        new_code_data={
            "code_id": 5,
            "name": "Corruption Subtypes",
            "function": Function.PROBLEM_DEFINITION.value,
            "evidence": defaultdict(list, {"initial": ["Parent-specific evidence"]}),
        },
        reasoning="Both codes are specific types of corruption",
    )

    print(f"\nExecuting CREATE_PARENT operation...")
    result = codebook.execute_operation(create_parent_op)
    print(f"Operation result: {result}")

    # Analyze final hierarchy
    print(f"\nFinal hierarchy:")
    root_codes = [c for c in codebook.codes.values() if c.parent_code_id is None]

    def print_hierarchy(code, indent=0):
        prefix = "  " * indent
        children = [
            c for c in codebook.codes.values() if c.parent_code_id == code.code_id
        ]
        print(f"{prefix}{code.name} (id={code.code_id}) [{len(children)} children]")
        if hasattr(code, "evidence") and code.evidence:
            evidence_summary = {}
            for art_id, quotes in code.evidence.items():
                evidence_summary[art_id] = len(quotes)
            print(f"{prefix}  Evidence: {evidence_summary}")
        for child in children:
            print_hierarchy(child, indent + 1)

    for root in root_codes:
        print_hierarchy(root)

    # Verify evidence aggregation
    corruption_subtypes = None
    for code in codebook.codes.values():
        if code.name == "Corruption Subtypes":
            corruption_subtypes = code
            break

    if corruption_subtypes:
        print(f"\nEvidence aggregation verification:")
        print(f"  Corruption Subtypes evidence: {dict(corruption_subtypes.evidence)}")

        # Count total evidence pieces
        total_evidence = sum(
            len(quotes) for quotes in corruption_subtypes.evidence.values()
        )
        print(f"  Total evidence pieces in parent: {total_evidence}")

        # Should have evidence from:
        # - Initial parent evidence (1 piece)
        # - Corruption Cases evidence (2 pieces from 2 articles)
        # - Bribery Scandals evidence (2 pieces from 2 articles)
        expected_evidence = 1 + 2 + 2  # 5 total pieces
        if total_evidence >= expected_evidence:
            print(
                f"  ✅ Evidence aggregation successful: {total_evidence} >= {expected_evidence}"
            )
        else:
            print(
                f"  ❌ Evidence aggregation incomplete: {total_evidence} < {expected_evidence}"
            )

    return codebook


def test_nested_hierarchy_preservation():
    """Test CREATE_PARENT on already nested hierarchies"""
    print("\n" + "=" * 80)
    print("Testing nested hierarchy preservation...")

    codebook = Codebook()

    # Create 3-level hierarchy: Root -> Middle -> Child
    root = Code(
        code_id=1,
        name="Social Issues",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article1": ["Social problems overview"]}),
    )

    middle = Code(
        code_id=2,
        name="Economic Problems",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article2": ["Economic issues details"]}),
    )

    child = Code(
        code_id=3,
        name="Unemployment",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=2,
        evidence=defaultdict(list, {"article3": ["Unemployment specifics"]}),
    )

    # Add sibling to middle to prevent abandonment
    middle_sibling = Code(
        code_id=4,
        name="Healthcare Problems",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=1,
        evidence=defaultdict(list, {"article4": ["Healthcare issues"]}),
    )

    # Add sibling to child to prevent abandonment
    child_sibling = Code(
        code_id=5,
        name="Inflation",
        function=Function.PROBLEM_DEFINITION,
        parent_code_id=2,
        evidence=defaultdict(list, {"article5": ["Inflation data"]}),
    )

    for code in [root, middle, child, middle_sibling, child_sibling]:
        codebook.add_code(code)

    print(f"Initial 3-level hierarchy:")
    print(f"  Social Issues -> [Economic Problems, Healthcare Problems]")
    print(f"    Economic Problems -> [Unemployment, Inflation]")

    # Create candidate similar to unemployment
    candidate = Code(
        code_id=6,
        name="Job Market Crisis",
        function=Function.PROBLEM_DEFINITION,
        evidence=defaultdict(list, {"article6": ["Job market analysis"]}),
    )
    codebook.add_code(candidate)

    # CREATE_PARENT targeting the nested child
    create_parent_op = Operation(
        operation_type=OperationType.CREATE_PARENT,
        target_code_id=3,  # Unemployment (nested child)
        source_code_id=6,  # Job Market Crisis
        new_code_data={
            "code_id": 7,
            "name": "Employment Issues",
            "function": Function.PROBLEM_DEFINITION.value,
            "evidence": defaultdict(list),
        },
        reasoning="Both unemployment and job market crisis are employment issues",
    )

    print(f"\nExecuting CREATE_PARENT on nested child...")
    result = codebook.execute_operation(create_parent_op)
    print(f"Operation result: {result}")

    # Show final nested structure
    print(f"\nFinal nested hierarchy:")
    root_codes = [c for c in codebook.codes.values() if c.parent_code_id is None]

    def print_hierarchy(code, indent=0):
        prefix = "  " * indent
        children = [
            c for c in codebook.codes.values() if c.parent_code_id == code.code_id
        ]
        print(f"{prefix}{code.name} [{len(children)} children]")
        for child in children:
            print_hierarchy(child, indent + 1)

    for root in root_codes:
        print_hierarchy(root)

    return codebook


if __name__ == "__main__":
    test_hierarchical_preservation_and_evidence()
    test_nested_hierarchy_preservation()
