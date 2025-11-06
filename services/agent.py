import os
import json
from typing import List, Dict, Optional, Any, Union
from openai import OpenAI
from dotenv import load_dotenv
from classes import Code

# Load environment variables
load_dotenv()


class Agent:
    """Generic OpenAI agent with context management and message handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize the OpenAI agent.

        Args:
            api_key: OpenAI API key. If None, will try to get from OPENAI_API_KEY environment variable
            model: The model to use (default: gpt-4)
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Context management
        self.system_context: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []

    def set_context(self, context: str) -> None:
        """
        Set the system context for the agent.

        Args:
            context: The system context/instructions for the agent
        """
        self.system_context = context
        # Clear conversation history when context changes
        self.conversation_history = []

    def add_to_history(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: The role of the message sender ('user', 'assistant', or 'system')
            content: The content of the message
        """
        self.conversation_history.append({"role": role, "content": content})

    def clear_history(self) -> None:
        """Clear the conversation history while keeping the system context."""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.conversation_history.copy()

    def send_message_structured(
        self, message: str, schema: Dict[str, Any], add_to_history: bool = True
    ) -> Union[Dict[str, Any], str]:
        """
        Send a message with OpenAI's structured outputs (GPT-4 only).
        This is the most reliable way to get JSON responses.

        Args:
            message: The message to send
            schema: JSON schema defining the required structure
            add_to_history: Whether to add this message to conversation history

        Returns:
            Structured response as dictionary, or error string
        """
        try:
            # Check if model supports structured outputs
            if not self.model.startswith("gpt-4"):
                return "Error: Structured outputs require GPT-4 or newer models"

            # Build the messages array
            messages = []

            # Add system context if set
            if self.system_context:
                messages.append({"role": "system", "content": self.system_context})

            # Add conversation history
            messages.extend(self.conversation_history)

            # Add current message
            messages.append({"role": "user", "content": message})

            # Make the API call with structured output
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "response_schema", "schema": schema},
                },
            )

            # Extract and parse the response
            assistant_message = response.choices[0].message.content
            json_response = json.loads(assistant_message)

            # Add to history if requested
            if add_to_history:
                self.add_to_history("user", message)
                self.add_to_history("assistant", assistant_message)

            return json_response

        except Exception as e:
            return f"Error: {str(e)}"

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the current agent configuration.

        Returns:
            Dictionary containing agent configuration and status
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "has_context": self.system_context is not None,
            "context_preview": (
                self.system_context[:100] + "..."
                if self.system_context and len(self.system_context) > 100
                else self.system_context
            ),
            "conversation_length": len(self.conversation_history),
            "api_key_set": bool(self.api_key),
        }
    
    def add_embedding(self, code: Code) -> Code:
        # add embedding for code
        pass
