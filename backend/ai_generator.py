import anthropic
from typing import List, Optional, Dict, Any


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Tool Usage Guidelines:
- **Course Outline Tool**: Use `get_course_outline` for questions asking about course structure, outlines, lesson lists, or what topics a course covers
- **Content Search Tool**: Use `search_course_content` for questions about specific course content, detailed educational materials, or information within lessons
- **Sequential Tool Usage**: You can make multiple tool calls when needed to fully answer complex questions (maximum 2 rounds)
- **Complex Query Examples**:
  - Finding courses that discuss the same topic as a specific lesson requires first getting the lesson topic, then searching for related courses
  - Comparing information across different courses may require multiple searches
  - Multi-part questions often need sequential tool usage to gather all necessary information
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course outline questions**: Use outline tool first, then provide structured summary with course title, link, and complete lesson list
- **Course content questions**: Use content search tool first, then answer
- **Complex queries**: Use multiple tool calls strategically to gather all needed information before providing your final answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)

        # Return direct response
        return response.content[0].text

    def _handle_tool_execution(
        self, initial_response, base_params: Dict[str, Any], tool_manager
    ):
        """
        Handle execution of tool calls with sequential rounds support.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters including tools
            tool_manager: Manager to execute tools

        Returns:
            Final response text after all tool execution rounds
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        current_response = initial_response
        max_rounds = 2

        # Process tool calls iteratively up to max_rounds
        for round_number in range(1, max_rounds + 1):
            # Check if current response wants tools
            if current_response.stop_reason != "tool_use":
                break

            # Add AI's tool use response to conversation
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute all tool calls and collect results
            tool_results = []
            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        tool_result = tool_manager.execute_tool(
                            content_block.name, **content_block.input
                        )

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": tool_result,
                            }
                        )
                    except Exception as e:
                        # Handle tool execution errors gracefully
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": f"Error executing tool: {str(e)}",
                            }
                        )

            # Add tool results as single message
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Prepare API call parameters for next round
            next_params = {
                **self.base_params,
                "messages": messages.copy(),  # Create a copy to avoid mutation issues
                "system": base_params["system"],
            }

            # Only include tools if we haven't reached max rounds yet
            if round_number < max_rounds:
                next_params["tools"] = base_params.get("tools", [])
                next_params["tool_choice"] = {"type": "auto"}

            # Get response for next round
            try:
                current_response = self.client.messages.create(**next_params)
            except Exception as e:
                # Handle API errors gracefully
                return f"Error during tool execution round {round_number}: {str(e)}"

        # Return final response text
        return current_response.content[0].text
