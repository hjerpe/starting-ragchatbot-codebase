"""
Comprehensive tests for AIGenerator sequential tool calling functionality.
Focus on external behavior: API calls made, tools executed, results returned.
"""
import pytest
from unittest.mock import Mock, patch, call
import os
import sys

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_generator import AIGenerator


class TestAIGeneratorSingleRound:
    """Test backward compatibility with single round tool calling"""

    @patch('anthropic.Anthropic')
    def test_simple_response_without_tools(self, mock_anthropic):
        """Test simple response without any tool usage"""
        # Setup mock
        mock_client = mock_anthropic.return_value
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a simple response."
        mock_client.messages.create.return_value = mock_response

        # Create generator
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")

        # Execute
        result = generator.generate_response("What is machine learning?")

        # Verify
        assert result == "This is a simple response."
        mock_client.messages.create.assert_called_once()

        # Verify API call parameters
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["model"] == "claude-3-sonnet-20241022"
        assert call_args[1]["temperature"] == 0
        assert call_args[1]["max_tokens"] == 800
        assert len(call_args[1]["messages"]) == 1
        assert call_args[1]["messages"][0]["role"] == "user"

    @patch('anthropic.Anthropic')
    def test_single_tool_call_round(self, mock_anthropic):
        """Test single tool call followed by final response"""
        # Setup mock client
        mock_client = mock_anthropic.return_value

        # First response: tool use
        tool_use_response = Mock()
        tool_use_response.stop_reason = "tool_use"
        tool_use_response.content = [Mock()]
        tool_use_response.content[0].type = "tool_use"
        tool_use_response.content[0].name = "search_course_content"
        tool_use_response.content[0].id = "tool_123"
        tool_use_response.content[0].input = {"query": "machine learning"}

        # Second response: final answer
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock()]
        final_response.content[0].text = "Machine learning is the study of algorithms."

        mock_client.messages.create.side_effect = [tool_use_response, final_response]

        # Setup mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Course content about ML algorithms..."

        # Setup tools
        tools = [{"name": "search_course_content", "description": "Search courses"}]

        # Create generator and execute
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")
        result = generator.generate_response(
            "What is machine learning?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Verify result
        assert result == "Machine learning is the study of algorithms."

        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", query="machine learning"
        )

        # Verify two API calls were made
        assert mock_client.messages.create.call_count == 2

        # Verify first call had tools
        first_call = mock_client.messages.create.call_args_list[0]
        assert "tools" in first_call[1]
        assert "tool_choice" in first_call[1]

        # Verify second call had conversation context with tool results
        second_call = mock_client.messages.create.call_args_list[1]
        assert len(second_call[1]["messages"]) == 3  # user, assistant, tool_results
        assert second_call[1]["messages"][1]["role"] == "assistant"
        assert second_call[1]["messages"][2]["role"] == "user"
        # Tools should still be available for potential second round
        assert "tools" in second_call[1]
        assert "tool_choice" in second_call[1]


class TestAIGeneratorSequentialRounds:
    """Test sequential tool calling with multiple rounds"""

    @patch('anthropic.Anthropic')
    def test_two_round_sequential_tool_calls(self, mock_anthropic):
        """Test two sequential rounds of tool calling"""
        # Setup mock client
        mock_client = mock_anthropic.return_value

        # Round 1: Get course outline
        round1_response = Mock()
        round1_response.stop_reason = "tool_use"
        round1_response.content = [Mock()]
        round1_response.content[0].type = "tool_use"
        round1_response.content[0].name = "get_course_outline"
        round1_response.content[0].id = "tool_round1"
        round1_response.content[0].input = {"course_title": "ML Course"}

        # Round 2: Search for similar content
        round2_response = Mock()
        round2_response.stop_reason = "tool_use"
        round2_response.content = [Mock()]
        round2_response.content[0].type = "tool_use"
        round2_response.content[0].name = "search_course_content"
        round2_response.content[0].id = "tool_round2"
        round2_response.content[0].input = {"query": "neural networks"}

        # Final response
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock()]
        final_response.content[0].text = "Found course Y that covers neural networks like lesson 4 of ML Course."

        mock_client.messages.create.side_effect = [round1_response, round2_response, final_response]

        # Setup mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "ML Course - Lesson 4: Neural Networks",  # Round 1 result
            "Course Y covers neural network fundamentals..."  # Round 2 result
        ]

        # Setup tools
        tools = [
            {"name": "get_course_outline", "description": "Get course outline"},
            {"name": "search_course_content", "description": "Search courses"}
        ]

        # Create generator and execute
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")
        result = generator.generate_response(
            "Find courses that cover the same topic as lesson 4 of ML Course",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Verify final result
        assert result == "Found course Y that covers neural networks like lesson 4 of ML Course."

        # Verify both tools were executed in sequence
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_has_calls([
            call("get_course_outline", course_title="ML Course"),
            call("search_course_content", query="neural networks")
        ])

        # Verify three API calls were made (initial + 2 rounds)
        assert mock_client.messages.create.call_count == 3

        # Verify tools were available in rounds 1 and 2, but not in final
        calls = mock_client.messages.create.call_args_list

        # Round 1: tools available
        assert "tools" in calls[0][1]
        assert calls[0][1]["tool_choice"] == {"type": "auto"}

        # Round 2: tools still available
        assert "tools" in calls[1][1]
        assert calls[1][1]["tool_choice"] == {"type": "auto"}

        # Final call: no tools
        assert "tools" not in calls[2][1]

        # Verify conversation context builds correctly
        assert len(calls[0][1]["messages"]) == 1  # user (initial call)
        assert len(calls[1][1]["messages"]) == 3  # user + assistant_round1 + tool_result_round1 (round 1 call)
        assert len(calls[2][1]["messages"]) == 5  # user + assistant_round1 + tool_result_round1 + assistant_round2 + tool_result_round2 (round 2 call)

    @patch('anthropic.Anthropic')
    def test_max_rounds_termination(self, mock_anthropic):
        """Test that system stops after max rounds (2) even if Claude wants more tools"""
        # Setup mock client - Claude keeps requesting tools
        mock_client = mock_anthropic.return_value

        # All responses request tools
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [Mock()]
        tool_response.content[0].type = "tool_use"
        tool_response.content[0].name = "search_course_content"
        tool_response.content[0].id = "tool_id"
        tool_response.content[0].input = {"query": "test"}

        # Mock client returns tool requests for all calls
        mock_client.messages.create.return_value = tool_response

        # Setup mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search result..."

        tools = [{"name": "search_course_content", "description": "Search courses"}]

        # Create generator and execute
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")
        result = generator.generate_response(
            "Test query", tools=tools, tool_manager=mock_tool_manager
        )

        # Verify system stops after exactly 2 rounds (initial + 2 rounds = 3 calls)
        assert mock_client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2

        # Result should be the last Claude response text (even though it's a tool_use response)
        # In practice, Claude should provide a final text response, but this tests the edge case
        assert result == tool_response.content[0].text  # This would be None/empty in practice


class TestAIGeneratorTerminationConditions:
    """Test various termination conditions"""

    @patch('anthropic.Anthropic')
    def test_tool_execution_error_handling(self, mock_anthropic):
        """Test that tool execution errors are handled gracefully"""
        # Setup mock client
        mock_client = mock_anthropic.return_value

        # Tool use response
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [Mock()]
        tool_response.content[0].type = "tool_use"
        tool_response.content[0].name = "search_course_content"
        tool_response.content[0].id = "tool_123"
        tool_response.content[0].input = {"query": "test"}

        # Final response after error
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock()]
        final_response.content[0].text = "I encountered an error but continued."

        mock_client.messages.create.side_effect = [tool_response, final_response]

        # Setup tool manager that raises exception
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = Exception("Tool failed!")

        tools = [{"name": "search_course_content", "description": "Search courses"}]

        # Execute
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")
        result = generator.generate_response(
            "Test query", tools=tools, tool_manager=mock_tool_manager
        )

        # Verify execution completes despite tool error
        assert result == "I encountered an error but continued."

        # Verify error was included in tool result
        second_call = mock_client.messages.create.call_args_list[1]
        tool_result_content = second_call[1]["messages"][2]["content"][0]
        assert "Error executing tool: Tool failed!" in tool_result_content["content"]

    @patch('anthropic.Anthropic')
    def test_api_error_during_rounds(self, mock_anthropic):
        """Test handling of API errors during tool rounds"""
        # Setup mock client
        mock_client = mock_anthropic.return_value

        # First call succeeds with tool use
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [Mock()]
        tool_response.content[0].type = "tool_use"
        tool_response.content[0].name = "search_course_content"
        tool_response.content[0].id = "tool_123"
        tool_response.content[0].input = {"query": "test"}

        # Second call fails
        mock_client.messages.create.side_effect = [tool_response, Exception("API Error!")]

        # Setup tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        tools = [{"name": "search_course_content", "description": "Search courses"}]

        # Execute
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")
        result = generator.generate_response(
            "Test query", tools=tools, tool_manager=mock_tool_manager
        )

        # Verify API error is handled gracefully
        assert "Error during tool execution round 1: API Error!" in result

    @patch('anthropic.Anthropic')
    def test_natural_termination_after_one_round(self, mock_anthropic):
        """Test that system terminates naturally when Claude doesn't request more tools"""
        # Setup mock client
        mock_client = mock_anthropic.return_value

        # Tool use response
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [Mock()]
        tool_response.content[0].type = "tool_use"
        tool_response.content[0].name = "search_course_content"
        tool_response.content[0].id = "tool_123"
        tool_response.content[0].input = {"query": "test"}

        # Natural end response (no more tools)
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock()]
        final_response.content[0].text = "Here's the complete answer."

        mock_client.messages.create.side_effect = [tool_response, final_response]

        # Setup tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search results..."

        tools = [{"name": "search_course_content", "description": "Search courses"}]

        # Execute
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")
        result = generator.generate_response(
            "Test query", tools=tools, tool_manager=mock_tool_manager
        )

        # Verify natural termination
        assert result == "Here's the complete answer."
        assert mock_client.messages.create.call_count == 2
        assert mock_tool_manager.execute_tool.call_count == 1

        # Verify second call still had tools available (under max rounds)
        second_call = mock_client.messages.create.call_args_list[1]
        assert "tools" in second_call[1]  # Tools were available but Claude chose not to use them


class TestAIGeneratorConversationContext:
    """Test conversation context preservation"""

    @patch('anthropic.Anthropic')
    def test_conversation_history_preserved(self, mock_anthropic):
        """Test that conversation history is preserved through sequential rounds"""
        # Setup mock client - single tool round
        mock_client = mock_anthropic.return_value

        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [Mock()]
        tool_response.content[0].type = "tool_use"
        tool_response.content[0].name = "search_course_content"
        tool_response.content[0].id = "tool_123"
        tool_response.content[0].input = {"query": "test"}

        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock()]
        final_response.content[0].text = "Final answer"

        mock_client.messages.create.side_effect = [tool_response, final_response]

        # Setup tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        tools = [{"name": "search_course_content", "description": "Search courses"}]

        # Execute with conversation history
        generator = AIGenerator("test-key", "claude-3-sonnet-20241022")
        result = generator.generate_response(
            "Current query",
            conversation_history="Previous conversation context",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Verify system prompt includes history in both calls
        calls = mock_client.messages.create.call_args_list

        # First call
        first_system = calls[0][1]["system"]
        assert "Previous conversation context" in first_system

        # Second call
        second_system = calls[1][1]["system"]
        assert "Previous conversation context" in second_system

        assert result == "Final answer"
