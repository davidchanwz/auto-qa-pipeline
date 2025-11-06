import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from classes import ResearchFramework, Function


class StrategicLayer:
    """Simple strategic layer for MVP - just provides framework and basic prompt."""

    def __init__(self):
        self.framework = ResearchFramework.create_entman_framework()
        self.coding_prompt = self._get_default_prompt()

    def get_framework(self) -> ResearchFramework:
        """Get the research framework."""
        return self.framework

    def get_coding_prompt(
        self, article_title: str = None, article_content: str = None
    ) -> str:
        """Get the coding prompt template, optionally formatted with article data."""
        if article_title and article_content:
            return self.coding_prompt.format(
                article_title=article_title, article_content=article_content
            )
        return self.coding_prompt

    def get_framework_context(self) -> str:
        """Get the framework context for setting agent context."""
        framework = self.framework

        # Build function descriptions dynamically from framework
        function_descriptions = []
        for func in framework.functions:
            if func == Function.PROBLEM_DEFINITION:
                function_descriptions.append(
                    "- PROBLEM_DEFINITION: How the issue is framed as a problem"
                )
            elif func == Function.CAUSAL_ATTRIBUTION:
                function_descriptions.append(
                    "- CAUSAL_ATTRIBUTION: What/who is identified as the cause"
                )
            elif func == Function.MORAL_EVALUATION:
                function_descriptions.append(
                    "- MORAL_EVALUATION: Value judgments about the issue"
                )
            elif func == Function.TREATMENT_ADVOCACY:
                function_descriptions.append(
                    "- TREATMENT_ADVOCACY: What solutions or actions are promoted"
                )

        return f"""You are analyzing this article using {framework.name} with these functions:
{chr(10).join(function_descriptions)}

Research Framework: {framework.name}
Description: {framework.description}"""

    def get_response_schema(self) -> dict:
        """Get the JSON schema for structured responses."""
        # Build enum values dynamically from framework functions
        function_enum = [func.value for func in self.framework.functions]

        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "function": {"type": "string", "enum": function_enum},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "explanation": {"type": "string"},
                },
                "required": ["name", "function", "evidence", "explanation"],
            },
        }

    def get_decision_prompt(
        self,
        existing_code_name: str,
        existing_code_function: str,
        existing_code_evidence: str,
        existing_code_created: str,
        candidate_code_name: str,
        candidate_code_function: str,
        candidate_code_evidence: str,
    ) -> str:
        """Get the prompt for LLM-based operation decisions."""
        return f"""You are an expert qualitative researcher analyzing codes for similarity and deciding operations.

EXISTING CODE:
- Name: {existing_code_name}
- Function: {existing_code_function}
- Evidence: {existing_code_evidence}
- Created: {existing_code_created}

CANDIDATE CODE:
- Name: {candidate_code_name}
- Function: {candidate_code_function}
- Evidence: {candidate_code_evidence}

DECISION TASK:
Analyze these two codes and decide the best operation:

1. MERGE - The codes are essentially the same or similar concept and should be combined. You can optionally update the name if the candidate provides a better conceptualization.
2. SPLIT - The candidate code represents a distinct subset/aspect of the existing code that would benefit from being separated into two distinct codes
3. CREATE_NEW - Despite similarity, they represent distinct concepts worth keeping separate
4. NO_ACTION - The existing code already covers this adequately

Consider:
- Conceptual similarity vs word similarity
- Evidence quality and uniqueness
- Whether they represent the same underlying phenomenon vs distinct aspects
- Whether the candidate represents a meaningful subset that should be split out
- Value of maintaining separate vs combined codes

Respond with ONLY valid JSON:
{{
    "operation": "MERGE|SPLIT|CREATE_NEW|NO_ACTION",
    "confidence": 0.1-1.0,
    "reasoning": "Brief explanation of your decision",
    "new_name": "Optional: new name for the code if MERGE operation and name should be updated"
}}"""

    def get_decision_schema(self) -> dict:
        """Get the JSON schema for operation decision responses."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["MERGE", "SPLIT", "CREATE_NEW", "NO_ACTION"],
                },
                "confidence": {"type": "number", "minimum": 0.1, "maximum": 1.0},
                "reasoning": {"type": "string"},
                "new_name": {
                    "type": "string",
                    "description": "Optional: new name for the code if MERGE operation and name should be updated",
                },
            },
            "required": ["operation", "confidence", "reasoning"],
        }

    def get_decision_context(self) -> str:
        """Get the specialized context for LLM-based operation decisions."""
        return """You are an expert qualitative researcher specializing in code comparison and qualitative data analysis.

Your expertise includes:
- Identifying conceptual similarity vs superficial word overlap
- Evaluating evidence quality and uniqueness across different sources
- Understanding when codes represent the same underlying phenomenon vs distinct concepts
- Recognizing when a new code represents a meaningful subset that should be split from a broader existing code
- Making strategic decisions about code consolidation, separation, or splitting for analytical clarity

You analyze pairs of qualitative codes and decide the best operation to maintain a high-quality, well-organized codebook that facilitates meaningful analysis while avoiding redundancy.

Operations available:
- MERGE: Combine similar/same concepts, optionally updating the name for better clarity
- SPLIT: Create a new specific code when the candidate represents a meaningful subset of the existing broader code
- CREATE_NEW: Keep codes separate when they represent distinct concepts
- NO_ACTION: When existing code already adequately covers the candidate

Focus on:
- Conceptual coherence and analytical value
- Evidence distinctiveness and complementarity  
- Maintaining clear boundaries between different phenomena
- Identifying hierarchical relationships (general vs specific concepts)
- Optimizing the codebook for downstream qualitative analysis"""

    def _get_default_prompt(self) -> str:
        """Get the default Entman coding prompt."""
        return """You are analyzing text using Entman's framing theory with these 4 functions:

1. PROBLEM_DEFINITION - How the issue/problem is defined
2. CAUSAL_ATTRIBUTION - What causes are identified  
3. MORAL_EVALUATION - Moral judgments made
4. TREATMENT_ADVOCACY - Solutions suggested

Article Title: {article_title}
Article Content: {article_content}

Identify codes for each function with supporting quotes. Respond with JSON:

[
  {{
    "name": "Code name",
    "function": "PROBLEM_DEFINITION|CAUSAL_ATTRIBUTION|MORAL_EVALUATION|TREATMENT_ADVOCACY", 
    "evidence": ["quote 1", "quote 2"],
    "explanation": "Brief explanation"
  }}
]"""
