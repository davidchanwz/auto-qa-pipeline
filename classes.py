from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from typing import Optional, List
from datetime import datetime


# Entman's 4 frame functions
class Function(Enum):
    PROBLEM_DEFINITION = "PROBLEM_DEFINITION"
    CAUSAL_ATTRIBUTION = "CAUSAL_ATTRIBUTION"
    MORAL_EVALUATION = "MORAL_EVALUATION"
    TREATMENT_ADVOCACY = "TREATMENT_ADVOCACY"
    
class Operation:
    # create new code
    # merge code
    # delete code
    pass

# Individual code dataclass
@dataclass
class Code:
    code_id: int
    name: str
    function: Function
    evidence: defaultdict[int, list[str]] = field(default_factory=lambda: defaultdict(list)) # article id : list of quotes
    embedding: Optional[List[float]] = None  # Semantic embedding vector
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    parent_code_id: int = None

class Codebook:
    def __init__(self):
        self.codes = {} # code id : code

    def add_code(self, code: Code):
        self.codes[code.code_id] = code

    def delete_code(self, code_id: int):
        del self.codes[code_id]

    def merge_codes(self, code1: Code, code2: Code):
        pass

    def get_similiar_codes(self, code: Code) -> List[Code]:
        # use semantic similiarity search based on code embedding
        pass

    def get_json(self):
        # convert to json
        pass

    def execute_operation(operation: Operation):
        pass
