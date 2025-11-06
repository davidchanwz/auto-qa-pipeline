from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


# Entman's 4 frame functions
class Function(Enum):
    PROBLEM_DEFINITION = "PROBLEM_DEFINITION"
    CAUSAL_ATTRIBUTION = "CAUSAL_ATTRIBUTION"
    MORAL_EVALUATION = "MORAL_EVALUATION"
    TREATMENT_ADVOCACY = "TREATMENT_ADVOCACY"


@dataclass
class ResearchFramework:
    """Defines a research framework for qualitative analysis."""

    name: str
    description: str
    functions: List[Function]

    def validate(self) -> bool:
        """Validate that the framework is complete and valid."""
        if not self.name or not self.description:
            return False
        if not self.functions:
            return False
        # Ensure no duplicate functions
        if len(set(self.functions)) != len(self.functions):
            return False
        return True

    @classmethod
    def create_entman_framework(cls) -> "ResearchFramework":
        """Create the default Entman framing framework."""
        return cls(
            name="Entman Framing Theory",
            description="Entman's framing theory focuses on four key functions: defining problems, diagnosing causes, making moral evaluations, and suggesting remedies.",
            functions=[
                Function.PROBLEM_DEFINITION,
                Function.CAUSAL_ATTRIBUTION,
                Function.MORAL_EVALUATION,
                Function.TREATMENT_ADVOCACY,
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert framework to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "functions": [func.value for func in self.functions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchFramework":
        """Create framework from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            functions=[Function(func) for func in data["functions"]],
        )


class OperationType(Enum):
    CREATE_CODE = "CREATE_CODE"
    MERGE_CODES = "MERGE_CODES"
    UPDATE_CODE = "UPDATE_CODE"
    SPLIT_CODE = "SPLIT_CODE"
    NO_ACTION = "NO_ACTION"


@dataclass
class Operation:
    """Represents an operation to be performed on the codebook."""

    operation_type: OperationType
    target_code_id: Optional[int] = None
    source_code_id: Optional[int] = None  # For merge operations
    new_code_data: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    reasoning: str = ""


# Individual code dataclass
@dataclass
class Code:
    code_id: int
    name: str
    function: Function
    evidence: defaultdict[int, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )  # article id : list of quotes
    embedding: Optional[List[float]] = None  # Semantic embedding vector
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    parent_code_id: int = None


class Codebook:
    def __init__(self):
        self.codes: Dict[int, Code] = {}
        self._next_id = 1

    def add_code(self, code: Code) -> None:
        """Add a code to the codebook."""
        if code.code_id is None:
            code.code_id = self._next_id
            self._next_id += 1
        self.codes[code.code_id] = code
        if code.code_id >= self._next_id:
            self._next_id = code.code_id + 1

    def delete_code(self, code_id: int) -> bool:
        """Delete a code from the codebook."""
        if code_id in self.codes:
            del self.codes[code_id]
            return True
        return False

    def merge_codes(self, code1_id: int, code2_id: int) -> Optional[Code]:
        """Merge two codes into one, combining their evidence."""
        if code1_id not in self.codes or code2_id not in self.codes:
            return None

        code1 = self.codes[code1_id]
        code2 = self.codes[code2_id]

        # Merge evidence
        merged_evidence = defaultdict(list)
        for article_id, quotes in code1.evidence.items():
            merged_evidence[article_id].extend(quotes)
        for article_id, quotes in code2.evidence.items():
            merged_evidence[article_id].extend(quotes)

        # Create merged code
        merged_code = Code(
            code_id=code1_id,  # Keep the first code's ID
            name=f"{code1.name} (merged with {code2.name})",
            function=code1.function,  # Keep the first code's function
            evidence=merged_evidence,
            embedding=code1.embedding,  # Keep the first code's embedding for now
            created_at=code1.created_at,
            updated_at=datetime.utcnow(),
            parent_code_id=code1.parent_code_id,
        )

        # Replace code1 and delete code2
        self.codes[code1_id] = merged_code
        del self.codes[code2_id]

        return merged_code

    def get_similar_codes_with_scores(
        self, code: Code, threshold: float = 0.6
    ) -> List[tuple]:
        """
        Get similar codes with their similarity scores.

        Args:
            code: The code to find similarities for
            threshold: Cosine similarity threshold (0.0 to 1.0, default 0.6)

        Returns:
            List of tuples (similar_code, similarity_score) sorted by score (highest first)
        """
        similar_codes = []

        # If the input code doesn't have an embedding, fall back to simple text matching
        if code.embedding is None:
            fallback_codes = self._fallback_text_similarity(code)
            return [
                (code, 0.9) for code in fallback_codes
            ]  # Assign high score for text matches

        for existing_code in self.codes.values():
            # Skip self-comparison
            if existing_code.code_id == code.code_id:
                continue

            # Skip codes with different functions (only compare within same function)
            if existing_code.function != code.function:
                continue

            # Skip codes without embeddings
            if existing_code.embedding is None:
                continue

            # Calculate cosine similarity between embeddings
            similarity = self._cosine_similarity(
                code.embedding, existing_code.embedding
            )

            # Add to results if above threshold
            if similarity >= threshold:
                similar_codes.append((existing_code, similarity))

        # Sort by similarity score (highest first)
        similar_codes.sort(key=lambda x: x[1], reverse=True)
        return similar_codes

    def get_similar_codes(self, code: Code, threshold: float = 0.6) -> List[Code]:
        """
        Get similar codes based on semantic similarity using embeddings.

        Args:
            code: The code to find similarities for
            threshold: Cosine similarity threshold (0.0 to 1.0, default 0.6)

        Returns:
            List of similar codes sorted by similarity score (highest first)
        """
        similar_codes = []

        # If the input code doesn't have an embedding, fall back to simple text matching
        if code.embedding is None:
            return self._fallback_text_similarity(code)

        for existing_code in self.codes.values():
            # Skip self-comparison
            if existing_code.code_id == code.code_id:
                continue

            # Skip codes without embeddings
            if existing_code.embedding is None:
                continue

            # Calculate cosine similarity between embeddings
            similarity = self._cosine_similarity(
                code.embedding, existing_code.embedding
            )

            # Add to results if above threshold
            if similarity >= threshold:
                similar_codes.append((existing_code, similarity))

        # Sort by similarity score (highest first) and return just the codes
        similar_codes.sort(key=lambda x: x[1], reverse=True)
        return [code for code, similarity in similar_codes]

    def _cosine_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embedding vectors.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between 0 and 1
        """
        import math

        # Ensure both embeddings have the same dimensions
        if len(embedding1) != len(embedding2):
            return 0.0

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(a * a for a in embedding2))

        # Avoid division by zero
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        # Calculate cosine similarity
        return dot_product / (magnitude1 * magnitude2)

    def _fallback_text_similarity(self, code: Code) -> List[Code]:
        """
        Fallback method for text-based similarity when embeddings are not available.

        Args:
            code: The code to find similarities for

        Returns:
            List of similar codes based on text matching
        """
        similar_codes = []
        for existing_code in self.codes.values():
            if (
                existing_code.code_id != code.code_id
                and existing_code.function == code.function
            ):
                # Simple name similarity as fallback
                if (
                    code.name.lower() in existing_code.name.lower()
                    or existing_code.name.lower() in code.name.lower()
                ):
                    similar_codes.append(existing_code)
        return similar_codes

    def to_json(self) -> str:
        """Convert codebook to JSON string."""
        codebook_data = {
            "metadata": {
                "total_codes": len(self.codes),
                "next_id": self._next_id,
                "created_at": datetime.utcnow().isoformat(),
            },
            "codes": {},
        }

        for code_id, code in self.codes.items():
            codebook_data["codes"][str(code_id)] = {
                "code_id": code.code_id,
                "name": code.name,
                "function": code.function.value,
                "evidence": dict(code.evidence),
                "embedding": code.embedding,
                "created_at": code.created_at.isoformat(),
                "updated_at": code.updated_at.isoformat(),
                "parent_code_id": code.parent_code_id,
            }

        return json.dumps(codebook_data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Codebook":
        """Create codebook from JSON string."""
        data = json.loads(json_str)
        codebook = cls()

        if "metadata" in data:
            codebook._next_id = data["metadata"].get("next_id", 1)

        for code_id, code_data in data.get("codes", {}).items():
            evidence = defaultdict(list)
            for article_id, quotes in code_data["evidence"].items():
                evidence[int(article_id)] = quotes

            code = Code(
                code_id=code_data["code_id"],
                name=code_data["name"],
                function=Function(code_data["function"]),
                evidence=evidence,
                embedding=code_data.get("embedding"),
                created_at=datetime.fromisoformat(code_data["created_at"]),
                updated_at=datetime.fromisoformat(code_data["updated_at"]),
                parent_code_id=code_data.get("parent_code_id"),
            )
            codebook.codes[code.code_id] = code

        return codebook

    def save_to_file(self, filepath: str) -> None:
        """Save codebook to JSON file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, filepath: str) -> "Codebook":
        """Load codebook from JSON file."""
        with open(filepath, "r") as f:
            return cls.from_json(f.read())

    def execute_operation(self, operation: Operation) -> bool:
        """Execute an operation on the codebook."""
        if operation.operation_type == OperationType.CREATE_CODE:
            if operation.new_code_data:
                code = Code(**operation.new_code_data)
                self.add_code(code)
                return True
        elif operation.operation_type == OperationType.MERGE_CODES:
            if operation.target_code_id and operation.source_code_id:
                result = self.merge_codes(
                    operation.target_code_id, operation.source_code_id
                )
                return result is not None
        elif operation.operation_type == OperationType.UPDATE_CODE:
            if operation.target_code_id and operation.target_code_id in self.codes:
                code = self.codes[operation.target_code_id]
                if operation.new_code_data:
                    for key, value in operation.new_code_data.items():
                        if hasattr(code, key):
                            setattr(code, key, value)
                code.updated_at = datetime.utcnow()
                return True
        elif operation.operation_type == OperationType.SPLIT_CODE:
            if (
                operation.target_code_id
                and operation.target_code_id in self.codes
                and operation.new_code_data
            ):
                # Create a new code from the subset data
                new_code = Code(**operation.new_code_data)
                self.add_code(new_code)

                # Note: The original code remains unchanged in a SPLIT operation
                # This allows both the original broader code and the new specific subset to coexist
                # If evidence needs to be redistributed, that should be handled by the calling logic
                return True
        elif operation.operation_type == OperationType.NO_ACTION:
            return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the codebook."""
        function_counts = defaultdict(int)
        total_evidence = 0

        for code in self.codes.values():
            function_counts[code.function.value] += 1
            total_evidence += sum(len(quotes) for quotes in code.evidence.values())

        return {
            "total_codes": len(self.codes),
            "function_distribution": dict(function_counts),
            "total_evidence_quotes": total_evidence,
            "codes_with_embeddings": sum(
                1 for code in self.codes.values() if code.embedding
            ),
            "next_available_id": self._next_id,
        }
