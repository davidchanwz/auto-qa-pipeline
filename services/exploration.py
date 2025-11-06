"""
Exploration Layer for Qualitative Analysis Pipeline

This layer uses the Agent to analyze articles using Strategic layer guidance
and updates the codebook with new findings.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from .agent import Agent
from .strategic import StrategicLayer
from classes import Code, Codebook, Function, OperationType, Operation


class ExplorationLayer:
    """
    Handles article analysis and codebook updates using AI-driven exploration
    """

    def __init__(self, agent: Agent, strategic: StrategicLayer):
        self.agent = agent
        self.strategic = strategic
        self.current_codebook = Codebook()

        # Initialize logging
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/exploration_session_{self.session_id}.json"

        # Store initial codebook stats for comparison
        initial_stats = self.get_codebook_summary()

        self.session_log = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "agent_config": {},
            "initial_stats": initial_stats,
            "articles_processed": [],
            "operations_performed": [],
            "decisions_made": [],
            "errors": [],
            "summary": {},
        }

        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Log initial setup
        self._log_step(
            "session_start",
            {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "agent_model": getattr(self.agent, "model", "unknown"),
                "strategic_framework": self.strategic.get_framework().name,
            },
        )

    def load_reference_codebook(self, codebook_path: str) -> None:
        """Load existing codebook for reference"""
        try:
            self.current_codebook = Codebook.load_from_file(codebook_path)
            stats = self.current_codebook.get_statistics()
            print(f"Loaded reference codebook with {stats['total_codes']} codes")
        except FileNotFoundError:
            print(f"No reference codebook found at {codebook_path}")
            self.current_codebook = Codebook()

    def analyze_article(self, article: Dict[str, Any]) -> List[Code]:
        """
        Analyze a single article using the strategic layer's framework and prompts

        Returns a list of candidate codes identified in the article
        """
        article_start_time = datetime.now().isoformat()

        # Log article analysis start
        self._log_step(
            "article_analysis_start",
            {
                "article_id": article["id"],
                "article_title": article["title"],
                "article_length": len(article["content"]),
                "timestamp": article_start_time,
            },
        )

        # Get the coding prompt template with article data
        prompt = self.strategic.get_coding_prompt(
            article_title=article["title"], article_content=article["content"]
        )

        # Log prompt generation
        self._log_step(
            "prompt_generated",
            {
                "article_id": article["id"],
                "prompt_length": len(prompt),
                "framework": self.strategic.get_framework().name,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Get framework context from strategic layer and set for article analysis
        framework_context = self.strategic.get_framework_context()
        self.agent.set_context(
            framework_context
        )  # This clears history for clean analysis

        # Log context setting
        self._log_step(
            "context_set",
            {
                "article_id": article["id"],
                "context_length": len(framework_context),
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Send the analysis prompt and get structured JSON response
        try:
            # Get the response schema from strategic layer
            schema = self.strategic.get_response_schema()

            # Try structured output first
            response = self.agent.send_message_structured(prompt, schema)

            # Handle error responses (model doesn't support structured outputs)
            if isinstance(response, str):
                print(f"Structured output not supported, trying fallback method...")
                # Log fallback attempt
                self._log_step(
                    "fallback_method_used",
                    {
                        "article_id": article["id"],
                        "reason": "structured_output_not_supported",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                # Fallback: use basic chat completion and parse JSON manually
                response = self._fallback_json_response(prompt)

            if not isinstance(response, list):
                error_msg = (
                    f"Unexpected response format: expected list, got {type(response)}"
                )
                print(error_msg)
                self._log_step(
                    "analysis_error",
                    {
                        "article_id": article["id"],
                        "error": error_msg,
                        "response_type": str(type(response)),
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return []

            # Log successful response
            self._log_step(
                "llm_response_received",
                {
                    "article_id": article["id"],
                    "response_type": "list",
                    "raw_codes_count": len(response),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Convert response to Code objects using your classes
            candidate_codes = []
            for i, code_data in enumerate(response):
                # Create evidence dict with article ID as key
                evidence = defaultdict(list)
                evidence[article["id"]] = code_data["evidence"]

                # Create initial code without embedding
                code = Code(
                    code_id=None,  # Will be assigned when added to codebook
                    name=code_data["name"],
                    function=Function[code_data["function"]],
                    evidence=evidence,
                    embedding=None,  # Will be added next
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # Generate and add embedding using the agent
                print(f"Generating embedding for code: {code.name}")
                code_with_embedding = self.agent.add_embedding(code)
                candidate_codes.append(code_with_embedding)

                # Log each code creation with embedding info
                self._log_step(
                    "code_created",
                    {
                        "article_id": article["id"],
                        "code_index": i,
                        "code_name": code_data["name"],
                        "code_function": code_data["function"],
                        "evidence_count": len(code_data["evidence"]),
                        "embedding_generated": code_with_embedding.embedding
                        is not None,
                        "embedding_dimensions": (
                            len(code_with_embedding.embedding)
                            if code_with_embedding.embedding
                            else 0
                        ),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            success_msg = f"Generated {len(candidate_codes)} candidate codes from article: {article['title']}"
            print(success_msg)

            # Log article analysis completion
            self._log_step(
                "article_analysis_complete",
                {
                    "article_id": article["id"],
                    "candidate_codes_count": len(candidate_codes),
                    "start_time": article_start_time,
                    "end_time": datetime.now().isoformat(),
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Add to session log
            self.session_log["articles_processed"].append(
                {
                    "article_id": article["id"],
                    "title": article["title"],
                    "codes_generated": len(candidate_codes),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return candidate_codes

        except Exception as e:
            error_msg = f"Error analyzing article {article['title']}: {e}"
            print(error_msg)

            # Log error
            self._log_step(
                "analysis_error",
                {
                    "article_id": article["id"],
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Add to session error log
            self.session_log["errors"].append(
                {
                    "type": "article_analysis_error",
                    "article_id": article["id"],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return []

    def _fallback_json_response(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Fallback method for models that don't support structured outputs
        Uses basic chat completion and manual JSON parsing
        """
        try:
            # Build the messages manually
            messages = []

            # Add system context if set
            if self.agent.system_context:
                messages.append(
                    {"role": "system", "content": self.agent.system_context}
                )

            # Add conversation history
            messages.extend(self.agent.conversation_history)

            # Add current prompt with explicit JSON instruction
            json_prompt = f"{prompt}\n\nIMPORTANT: Respond with ONLY valid JSON array, no other text."
            messages.append({"role": "user", "content": json_prompt})

            # Make basic chat completion call
            response = self.agent.client.chat.completions.create(
                model=self.agent.model,
                messages=messages,
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
            )

            # Extract and parse the response
            content = response.choices[0].message.content.strip()

            # Clean up the content (remove markdown formatting if present)
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            # Parse JSON
            parsed_response = json.loads(content)

            # Add to conversation history
            self.agent.add_to_history("user", json_prompt)
            self.agent.add_to_history("assistant", content)

            return parsed_response

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw content: {content}")
            return []
        except Exception as e:
            print(f"Fallback method error: {e}")
            return []

    def compare_with_existing_codes(
        self, candidate_codes: List[Code]
    ) -> List[Operation]:
        """
        Compare candidate codes with existing codebook and determine operations

        Returns a list of operations to perform using your Operation class
        """
        comparison_start_time = datetime.now().isoformat()

        # Log comparison start
        self._log_step(
            "comparison_start",
            {
                "candidate_codes_count": len(candidate_codes),
                "existing_codes_count": len(self.current_codebook.codes),
                "timestamp": comparison_start_time,
            },
        )

        operations = []

        for i, candidate in enumerate(candidate_codes):
            # Log individual candidate processing
            self._log_step(
                "candidate_processing",
                {
                    "candidate_index": i,
                    "candidate_name": candidate.name,
                    "candidate_function": candidate.function.value,
                    "evidence_count": (
                        len(list(candidate.evidence.values())[0])
                        if candidate.evidence
                        else 0
                    ),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Find similar codes using the codebook's method with similarity scores
            similar_codes_with_scores = (
                self.current_codebook.get_similar_codes_with_scores(
                    candidate, threshold=0.6
                )
            )
            similar_codes = [code for code, score in similar_codes_with_scores]

            # Log similarity search results with scores
            self._log_step(
                "similarity_search",
                {
                    "candidate_index": i,
                    "candidate_name": candidate.name,
                    "candidate_function": candidate.function.value,
                    "similar_codes_found": len(similar_codes),
                    "similar_code_names": [
                        code.name for code in similar_codes[:3]
                    ],  # Top 3
                    "similarity_scores": [
                        round(score, 3) for code, score in similar_codes_with_scores[:3]
                    ],  # Top 3 scores
                    "highest_similarity": (
                        round(similar_codes_with_scores[0][1], 3)
                        if similar_codes_with_scores
                        else 0.0
                    ),
                    "threshold_used": 0.6,
                    "candidate_has_embedding": candidate.embedding is not None,
                    "function_filtered": True,  # Now filtering by function
                    "existing_codes_same_function": sum(
                        1
                        for code in self.current_codebook.codes.values()
                        if code.function == candidate.function
                        and code.embedding is not None
                    ),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            if not similar_codes:
                # New code - create operation to add it
                operation = Operation(
                    operation_type=OperationType.CREATE_CODE,
                    new_code_data={
                        "code_id": None,
                        "name": candidate.name,
                        "function": candidate.function,
                        "evidence": candidate.evidence,
                        "embedding": candidate.embedding,
                        "created_at": candidate.created_at,
                        "updated_at": candidate.updated_at,
                        "parent_code_id": candidate.parent_code_id,
                    },
                    confidence=0.9,
                    reasoning="New code not found in existing codebook",
                )
                operations.append(operation)

                # Log operation creation
                self._log_step(
                    "operation_created",
                    {
                        "candidate_index": i,
                        "operation_type": "CREATE_CODE",
                        "reason": "no_similar_codes",
                        "confidence": 0.9,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
            else:
                # Similar code exists - use LLM to decide what to do
                most_similar = similar_codes[0]  # Take the first similar code
                decision = self._llm_decide_operation(most_similar, candidate)

                if decision["operation"] == "MERGE":
                    # Merge by updating existing code with enhanced evidence
                    merged_evidence = self._merge_evidence(
                        most_similar.evidence, candidate.evidence
                    )
                    # Use new name from LLM decision if provided, otherwise keep original or add "(enhanced)"
                    new_name = decision.get("new_name")
                    if not new_name:
                        new_name = f"{most_similar.name} (enhanced)"

                    operation = Operation(
                        operation_type=OperationType.UPDATE_CODE,
                        target_code_id=most_similar.code_id,
                        new_code_data={
                            "evidence": merged_evidence,
                            "name": new_name,
                            "updated_at": datetime.utcnow(),
                        },
                        confidence=decision["confidence"],
                        reasoning=f"LLM Decision: {decision['reasoning']}",
                    )
                    operations.append(operation)
                elif decision["operation"] == "SPLIT":
                    # Create new code for the subset while keeping the original
                    operation = Operation(
                        operation_type=OperationType.SPLIT_CODE,
                        target_code_id=most_similar.code_id,
                        new_code_data={
                            "code_id": None,
                            "name": candidate.name,
                            "function": candidate.function,
                            "evidence": candidate.evidence,
                            "embedding": candidate.embedding,
                            "created_at": candidate.created_at,
                            "updated_at": candidate.updated_at,
                            "parent_code_id": most_similar.code_id,  # Link to original code
                        },
                        confidence=decision["confidence"],
                        reasoning=f"LLM Decision: {decision['reasoning']}",
                    )
                    operations.append(operation)
                elif decision["operation"] == "CREATE_NEW":
                    # Create new code despite similarity
                    operation = Operation(
                        operation_type=OperationType.CREATE_CODE,
                        new_code_data={
                            "code_id": None,
                            "name": candidate.name,
                            "function": candidate.function,
                            "evidence": candidate.evidence,
                            "embedding": candidate.embedding,
                            "created_at": candidate.created_at,
                            "updated_at": candidate.updated_at,
                            "parent_code_id": candidate.parent_code_id,
                        },
                        confidence=decision["confidence"],
                        reasoning=f"LLM Decision: {decision['reasoning']}",
                    )
                    operations.append(operation)
                else:  # NO_ACTION
                    operation = Operation(
                        operation_type=OperationType.NO_ACTION,
                        target_code_id=most_similar.code_id,
                        confidence=decision["confidence"],
                        reasoning=f"LLM Decision: {decision['reasoning']}",
                    )
                    operations.append(operation)

                # Log operation creation for similar code case
                self._log_step(
                    "operation_created",
                    {
                        "candidate_index": i,
                        "operation_type": decision["operation"],
                        "similar_code_name": most_similar.name,
                        "confidence": decision["confidence"],
                        "reasoning": decision["reasoning"],
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        # Log comparison completion
        self._log_step(
            "comparison_complete",
            {
                "operations_generated": len(operations),
                "operation_types": [op.operation_type.value for op in operations],
                "start_time": comparison_start_time,
                "end_time": datetime.now().isoformat(),
                "timestamp": datetime.now().isoformat(),
            },
        )

        return operations

    def _llm_decide_operation(
        self, existing_code: Code, candidate_code: Code
    ) -> Dict[str, Any]:
        """
        Use LLM to decide what operation to perform when comparing existing and candidate codes
        Uses clean context isolation to ensure valid, uncontaminated decisions.

        Returns:
            Dict with keys: 'operation', 'confidence', 'reasoning'
        """
        decision_start_time = datetime.now().isoformat()

        # Log decision start
        self._log_step(
            "llm_decision_start",
            {
                "existing_code_name": existing_code.name,
                "existing_code_function": existing_code.function.value,
                "candidate_code_name": candidate_code.name,
                "candidate_code_function": candidate_code.function.value,
                "timestamp": decision_start_time,
            },
        )

        # Clear conversation history and set specialized decision context
        self.agent.clear_history()
        decision_context = self.strategic.get_decision_context()
        self.agent.set_context(decision_context)

        # Log context setup
        self._log_step(
            "decision_context_set",
            {
                "context_length": len(decision_context),
                "existing_code_name": existing_code.name,
                "candidate_code_name": candidate_code.name,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Get decision prompt and schema from strategic layer
        decision_prompt = self.strategic.get_decision_prompt(
            existing_code_name=existing_code.name,
            existing_code_function=existing_code.function.value,
            existing_code_evidence=str(dict(existing_code.evidence)),
            existing_code_created=str(existing_code.created_at),
            candidate_code_name=candidate_code.name,
            candidate_code_function=candidate_code.function.value,
            candidate_code_evidence=str(dict(candidate_code.evidence)),
        )

        decision_schema = self.strategic.get_decision_schema()

        # Log prompt generation
        self._log_step(
            "decision_prompt_generated",
            {
                "prompt_length": len(decision_prompt),
                "schema_keys": (
                    list(decision_schema.keys())
                    if isinstance(decision_schema, dict)
                    else "non_dict_schema"
                ),
                "timestamp": datetime.now().isoformat(),
            },
        )

        try:
            # Get LLM decision with clean context
            response = self.agent.send_message_structured(
                decision_prompt, decision_schema
            )

            # Clear history again to prevent decision contamination for next operation
            self.agent.clear_history()

            # Handle error responses (fallback to basic logic)
            if isinstance(response, str):
                print(f"LLM decision failed, using fallback logic")

                # Log fallback usage
                self._log_step(
                    "decision_fallback_used",
                    {
                        "reason": "string_response_received",
                        "existing_code_name": existing_code.name,
                        "candidate_code_name": candidate_code.name,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                return self._fallback_decision_logic(existing_code, candidate_code)

            # Validate response
            if not isinstance(response, dict) or "operation" not in response:
                print(f"Invalid LLM decision format, using fallback logic")

                # Log fallback usage
                self._log_step(
                    "decision_fallback_used",
                    {
                        "reason": "invalid_response_format",
                        "response_type": str(type(response)),
                        "existing_code_name": existing_code.name,
                        "candidate_code_name": candidate_code.name,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                return self._fallback_decision_logic(existing_code, candidate_code)

            print(
                f"LLM Decision: {response['operation']} (confidence: {response.get('confidence', 0.5)}) - {response.get('reasoning', 'No reason provided')}"
            )

            # Log successful decision
            self._log_step(
                "llm_decision_complete",
                {
                    "operation": response["operation"],
                    "confidence": response.get("confidence", 0.5),
                    "reasoning": response.get("reasoning", "No reason provided"),
                    "existing_code_name": existing_code.name,
                    "candidate_code_name": candidate_code.name,
                    "start_time": decision_start_time,
                    "end_time": datetime.now().isoformat(),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Add to session decisions log
            self.session_log["decisions_made"].append(
                {
                    "existing_code": existing_code.name,
                    "candidate_code": candidate_code.name,
                    "decision": response["operation"],
                    "confidence": response.get("confidence", 0.5),
                    "reasoning": response.get("reasoning", "No reason provided"),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return response

        except Exception as e:
            print(f"Error in LLM decision: {e}, using fallback logic")

            # Log decision error
            self._log_step(
                "decision_error",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "existing_code_name": existing_code.name,
                    "candidate_code_name": candidate_code.name,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Add to session error log
            self.session_log["errors"].append(
                {
                    "type": "llm_decision_error",
                    "existing_code": existing_code.name,
                    "candidate_code": candidate_code.name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return self._fallback_decision_logic(existing_code, candidate_code)

    def _fallback_decision_logic(
        self, existing_code: Code, candidate_code: Code
    ) -> Dict[str, Any]:
        """
        Fallback decision logic using simple rules when LLM fails
        """
        # Check if same function
        if existing_code.function != candidate_code.function:
            return {
                "operation": "CREATE_NEW",
                "confidence": 0.8,
                "reasoning": "Different functions - should be separate codes",
            }

        # Simple name similarity check
        existing_words = set(existing_code.name.lower().split())
        candidate_words = set(candidate_code.name.lower().split())
        overlap = len(existing_words.intersection(candidate_words))
        min_words = min(len(existing_words), len(candidate_words))
        similarity = overlap / min_words if min_words > 0 else 0

        if similarity > 0.7:
            return {
                "operation": "MERGE",
                "confidence": 0.7,
                "reasoning": f"High name similarity ({similarity:.2f}) - likely same concept",
            }
        elif similarity > 0.4:
            return {
                "operation": "MERGE",
                "confidence": 0.6,
                "reasoning": f"Moderate similarity ({similarity:.2f}) - merge with existing evidence",
            }
        else:
            return {
                "operation": "CREATE_NEW",
                "confidence": 0.8,
                "reasoning": f"Low similarity ({similarity:.2f}) - distinct concepts",
            }

    def _merge_evidence(
        self, existing_evidence: defaultdict, candidate_evidence: defaultdict
    ) -> defaultdict:
        """Merge evidence from two codes"""
        merged = defaultdict(list)

        # Add existing evidence
        for article_id, quotes in existing_evidence.items():
            merged[article_id].extend(quotes)

        # Add candidate evidence
        for article_id, quotes in candidate_evidence.items():
            merged[article_id].extend(quotes)

        return merged

    def update_codebook(self, operations: List[Operation]) -> Codebook:
        """
        Apply operations to update the codebook using the built-in execute_operation method

        Returns the updated codebook
        """
        update_start_time = datetime.now().isoformat()

        # Log update start
        self._log_step(
            "codebook_update_start",
            {
                "operations_count": len(operations),
                "operation_types": [op.operation_type.value for op in operations],
                "timestamp": update_start_time,
            },
        )

        successful_operations = 0
        failed_operations = 0

        for i, operation in enumerate(operations):
            operation_start_time = datetime.now().isoformat()

            # Log individual operation attempt
            self._log_step(
                "operation_attempt",
                {
                    "operation_index": i,
                    "operation_type": operation.operation_type.value,
                    "target_code_id": operation.target_code_id,
                    "confidence": operation.confidence,
                    "reasoning": operation.reasoning,
                    "timestamp": operation_start_time,
                },
            )

            success = self.current_codebook.execute_operation(operation)

            if success:
                successful_operations += 1
                print(
                    f"Executed {operation.operation_type.value}: {operation.reasoning}"
                )

                # Log successful operation
                self._log_step(
                    "operation_success",
                    {
                        "operation_index": i,
                        "operation_type": operation.operation_type.value,
                        "confidence": operation.confidence,
                        "reasoning": operation.reasoning,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                # Add to session operations log
                self.session_log["operations_performed"].append(
                    {
                        "operation_type": operation.operation_type.value,
                        "confidence": operation.confidence,
                        "reasoning": operation.reasoning,
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                failed_operations += 1
                print(
                    f"Failed to execute {operation.operation_type.value}: {operation.reasoning}"
                )

                # Log failed operation
                self._log_step(
                    "operation_failure",
                    {
                        "operation_index": i,
                        "operation_type": operation.operation_type.value,
                        "confidence": operation.confidence,
                        "reasoning": operation.reasoning,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                # Add to session operations log
                self.session_log["operations_performed"].append(
                    {
                        "operation_type": operation.operation_type.value,
                        "confidence": operation.confidence,
                        "reasoning": operation.reasoning,
                        "success": False,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Add to session error log
                self.session_log["errors"].append(
                    {
                        "type": "operation_execution_failure",
                        "operation_type": operation.operation_type.value,
                        "reasoning": operation.reasoning,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Log update completion
        self._log_step(
            "codebook_update_complete",
            {
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "total_operations": len(operations),
                "success_rate": (
                    successful_operations / len(operations) if operations else 0
                ),
                "start_time": update_start_time,
                "end_time": datetime.now().isoformat(),
                "final_codebook_stats": self.get_codebook_summary(),
                "timestamp": datetime.now().isoformat(),
            },
        )

        return self.current_codebook

    def analyze_articles(self, articles: List[Dict[str, Any]]) -> Codebook:
        """
        Analyze multiple articles and update codebook incrementally

        Main method that orchestrates the entire exploration process.
        Each article is analyzed and the codebook is updated immediately,
        allowing subsequent articles to see and build upon previous changes.
        """
        analysis_start_time = datetime.now().isoformat()

        # Log incremental analysis start
        self._log_step(
            "incremental_analysis_start",
            {
                "total_articles": len(articles),
                "article_titles": [
                    (
                        article["title"][:60] + "..."
                        if len(article["title"]) > 60
                        else article["title"]
                    )
                    for article in articles
                ],
                "initial_codebook_stats": self.get_codebook_summary(),
                "approach": "incremental",
                "timestamp": analysis_start_time,
            },
        )

        print(f"Starting incremental analysis of {len(articles)} articles...")

        total_operations_applied = 0
        article_results = []

        for i, article in enumerate(articles, 1):
            article_start_time = datetime.now().isoformat()

            # Get current codebook state before processing this article
            pre_article_stats = self.get_codebook_summary()

            print(
                f"\n--- Analyzing Article {i}/{len(articles)}: {article['title'][:60]}... ---"
            )
            print(f"Current codebook state: {pre_article_stats['total_codes']} codes")

            # Log individual article start
            self._log_step(
                "incremental_article_start",
                {
                    "article_number": i,
                    "total_articles": len(articles),
                    "article_id": article["id"],
                    "article_title": article["title"],
                    "pre_article_codebook_stats": pre_article_stats,
                    "timestamp": article_start_time,
                },
            )

            # Analyze article to get candidate codes
            candidate_codes = self.analyze_article(article)

            if candidate_codes:
                # Compare with existing codes to determine operations
                operations = self.compare_with_existing_codes(candidate_codes)

                print(f"Generated {len(operations)} operations from this article")

                # Apply operations immediately after each article
                if operations:
                    print(f"Applying {len(operations)} operations to codebook...")

                    # Log incremental update start
                    self._log_step(
                        "incremental_update_start",
                        {
                            "article_number": i,
                            "article_id": article["id"],
                            "operations_count": len(operations),
                            "operation_types": [
                                op.operation_type.value for op in operations
                            ],
                            "pre_update_stats": self.get_codebook_summary(),
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                    # Update codebook incrementally
                    self.current_codebook = self.update_codebook(operations)
                    total_operations_applied += len(operations)

                    # Get stats after update
                    post_article_stats = self.get_codebook_summary()

                    print(
                        f"Codebook updated: {post_article_stats['total_codes']} total codes (+{post_article_stats['total_codes'] - pre_article_stats['total_codes']})"
                    )

                    # Log article completion with incremental update
                    self._log_step(
                        "incremental_article_complete",
                        {
                            "article_number": i,
                            "article_id": article["id"],
                            "candidate_codes_count": len(candidate_codes),
                            "operations_applied": len(operations),
                            "operation_types": [
                                op.operation_type.value for op in operations
                            ],
                            "pre_article_stats": pre_article_stats,
                            "post_article_stats": post_article_stats,
                            "codes_added": post_article_stats["total_codes"]
                            - pre_article_stats["total_codes"],
                            "start_time": article_start_time,
                            "end_time": datetime.now().isoformat(),
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                else:
                    print(
                        "No operations to apply - codebook unchanged for this article"
                    )

                    # Log article with no operations
                    self._log_step(
                        "incremental_article_no_operations",
                        {
                            "article_number": i,
                            "article_id": article["id"],
                            "candidate_codes_count": len(candidate_codes),
                            "reason": "no_operations_generated",
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
            else:
                print("No candidate codes generated from this article")

                # Log article with no codes
                self._log_step(
                    "incremental_article_no_codes",
                    {
                        "article_number": i,
                        "article_id": article["id"],
                        "article_title": article["title"],
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # Track article results
            final_article_stats = self.get_codebook_summary()
            article_results.append(
                {
                    "article_id": article["id"],
                    "title": article["title"],
                    "candidate_codes": len(candidate_codes),
                    "operations": len(operations) if candidate_codes else 0,
                    "codes_before": pre_article_stats["total_codes"],
                    "codes_after": final_article_stats["total_codes"],
                    "codes_added": final_article_stats["total_codes"]
                    - pre_article_stats["total_codes"],
                    "processing_time": datetime.now().isoformat(),
                }
            )

        # Log incremental analysis completion
        final_stats = self.get_codebook_summary()
        self._log_step(
            "incremental_analysis_complete",
            {
                "total_articles_processed": len(articles),
                "total_operations_applied": total_operations_applied,
                "initial_codebook_stats": self.session_log.get("initial_stats", {}),
                "final_codebook_stats": final_stats,
                "article_results": article_results,
                "approach": "incremental",
                "start_time": analysis_start_time,
                "end_time": datetime.now().isoformat(),
                "success": True,
                "timestamp": datetime.now().isoformat(),
            },
        )

        print(f"\n=== Incremental Analysis Complete ===")
        print(f"Processed {len(articles)} articles")
        print(f"Applied {total_operations_applied} total operations")
        print(f"Final codebook: {final_stats['total_codes']} codes")

        return self.current_codebook

    def save_updated_codebook(self, codebook: Codebook, output_path: str) -> None:
        """Save the updated codebook to file using the built-in method"""
        try:
            # Log save attempt
            self._log_step(
                "codebook_save_start",
                {
                    "output_path": output_path,
                    "codebook_stats": codebook.get_statistics(),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            codebook.save_to_file(output_path)
            print(f"Updated codebook saved to {output_path}")

            # Log successful save
            self._log_step(
                "codebook_save_success",
                {
                    "output_path": output_path,
                    "file_size": (
                        os.path.getsize(output_path)
                        if os.path.exists(output_path)
                        else 0
                    ),
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            error_msg = f"Error saving codebook: {e}"
            print(error_msg)

            # Log save error
            self._log_step(
                "codebook_save_error",
                {
                    "output_path": output_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Add to session error log
            self.session_log["errors"].append(
                {
                    "type": "codebook_save_error",
                    "output_path": output_path,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def get_codebook_summary(self) -> Dict[str, Any]:
        """Get a summary of the current codebook"""
        return self.current_codebook.get_statistics()

    def _log_step(self, step_type: str, data: Dict[str, Any]) -> None:
        """
        Log a step in the exploration process to both console and JSON file

        Args:
            step_type: Type of step (e.g., 'article_analysis_start', 'llm_decision', etc.)
            data: Step-specific data to log
        """
        log_entry = {
            "step_type": step_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        # Write to JSON file immediately for real-time logging
        try:
            # Read existing log file if it exists
            if os.path.exists(self.log_file):
                with open(self.log_file, "r") as f:
                    existing_log = json.load(f)
            else:
                existing_log = {"steps": []}

            # Add new step
            if "steps" not in existing_log:
                existing_log["steps"] = []
            existing_log["steps"].append(log_entry)

            # Write back to file
            with open(self.log_file, "w") as f:
                json.dump(existing_log, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to write to log file {self.log_file}: {e}")

    def _save_session_log(self) -> None:
        """
        Save the complete session log to file with summary statistics
        """
        try:
            # Calculate session summary
            end_time = datetime.now().isoformat()
            self.session_log["end_time"] = end_time
            self.session_log["summary"] = {
                "total_articles_processed": len(self.session_log["articles_processed"]),
                "total_operations_performed": len(
                    self.session_log["operations_performed"]
                ),
                "total_decisions_made": len(self.session_log["decisions_made"]),
                "total_errors": len(self.session_log["errors"]),
                "session_duration": end_time,
                "final_codebook_stats": self.get_codebook_summary(),
            }

            # Write complete session log
            session_file = f"logs/session_summary_{self.session_id}.json"
            with open(session_file, "w") as f:
                json.dump(self.session_log, f, indent=2)

            print(f"Session log saved to {session_file}")

        except Exception as e:
            print(f"Warning: Failed to save session log: {e}")

    def finalize_session(self) -> str:
        """
        Finalize the logging session and return the log file path

        Returns:
            Path to the complete session log file
        """
        self._log_step(
            "session_end",
            {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "final_stats": self.get_codebook_summary(),
            },
        )

        self._save_session_log()
        return f"logs/session_summary_{self.session_id}.json"
