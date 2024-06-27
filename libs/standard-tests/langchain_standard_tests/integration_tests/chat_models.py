import base64
import json
from typing import Optional

import httpx
import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessageChunk,
    HumanMessage,
    ToolMessage,
)
from langchain_core.tools import tool

from langchain_standard_tests.unit_tests.chat_models import (
    ChatModelTests,
    my_adder_tool,
)


@tool
def magic_function(input: int) -> int:
    """Applies a magic function to an input."""
    return input + 2


def _validate_tool_call_message(message: AIMessage) -> None:
    assert isinstance(message, AIMessage)
    assert len(message.tool_calls) == 1
    tool_call = message.tool_calls[0]
    assert tool_call["name"] == "magic_function"
    assert tool_call["args"] == {"input": 3}
    assert tool_call["id"] is not None


class ChatModelIntegrationTests(ChatModelTests):
    def test_invoke(self, model: BaseChatModel) -> None:
        result = model.invoke("Hello")
        assert result is not None
        assert isinstance(result, AIMessage)
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    async def test_ainvoke(self, model: BaseChatModel) -> None:
        result = await model.ainvoke("Hello")
        assert result is not None
        assert isinstance(result, AIMessage)
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    def test_stream(self, model: BaseChatModel) -> None:
        num_tokens = 0
        for token in model.stream("Hello"):
            assert token is not None
            assert isinstance(token, AIMessageChunk)
            num_tokens += len(token.content)
        assert num_tokens > 0

    async def test_astream(self, model: BaseChatModel) -> None:
        num_tokens = 0
        async for token in model.astream("Hello"):
            assert token is not None
            assert isinstance(token, AIMessageChunk)
            num_tokens += len(token.content)
        assert num_tokens > 0

    def test_batch(self, model: BaseChatModel) -> None:
        batch_results = model.batch(["Hello", "Hey"])
        assert batch_results is not None
        assert isinstance(batch_results, list)
        assert len(batch_results) == 2
        for result in batch_results:
            assert result is not None
            assert isinstance(result, AIMessage)
            assert isinstance(result.content, str)
            assert len(result.content) > 0

    async def test_abatch(self, model: BaseChatModel) -> None:
        batch_results = await model.abatch(["Hello", "Hey"])
        assert batch_results is not None
        assert isinstance(batch_results, list)
        assert len(batch_results) == 2
        for result in batch_results:
            assert result is not None
            assert isinstance(result, AIMessage)
            assert isinstance(result.content, str)
            assert len(result.content) > 0

    def test_conversation(self, model: BaseChatModel) -> None:
        messages = [
            HumanMessage("hello"),
            AIMessage("hello"),
            HumanMessage("how are you"),
        ]
        result = model.invoke(messages)
        assert result is not None
        assert isinstance(result, AIMessage)
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    def test_usage_metadata(self, model: BaseChatModel) -> None:
        if not self.returns_usage_metadata:
            pytest.skip("Not implemented.")
        result = model.invoke("Hello")
        assert result is not None
        assert isinstance(result, AIMessage)
        assert result.usage_metadata is not None
        assert isinstance(result.usage_metadata["input_tokens"], int)
        assert isinstance(result.usage_metadata["output_tokens"], int)
        assert isinstance(result.usage_metadata["total_tokens"], int)

    def test_stop_sequence(self, model: BaseChatModel) -> None:
        result = model.invoke("hi", stop=["you"])
        assert isinstance(result, AIMessage)

        custom_model = self.chat_model_class(
            **{**self.chat_model_params, "stop": ["you"]}
        )
        result = custom_model.invoke("hi")
        assert isinstance(result, AIMessage)

    def test_tool_calling(self, model: BaseChatModel) -> None:
        if not self.has_tool_calling:
            pytest.skip("Test requires tool calling.")
        model_with_tools = model.bind_tools([magic_function])

        # Test invoke
        query = "What is the value of magic_function(3)? Use the tool."
        result = model_with_tools.invoke(query)
        assert isinstance(result, AIMessage)
        _validate_tool_call_message(result)

        # Test stream
        full: Optional[BaseMessageChunk] = None
        for chunk in model_with_tools.stream(query):
            full = chunk if full is None else full + chunk  # type: ignore
        assert isinstance(full, AIMessage)
        _validate_tool_call_message(full)

    def test_tool_message_histories_string_content(
        self,
        model: BaseChatModel,
    ) -> None:
        """
        Test that message histories are compatible with string tool contents
        (e.g. OpenAI).
        """
        if not self.has_tool_calling:
            pytest.skip("Test requires tool calling.")
        model_with_tools = model.bind_tools([my_adder_tool])
        function_name = "my_adder_tool"
        function_args = {"a": "1", "b": "2"}

        messages_string_content = [
            HumanMessage("What is 1 + 2"),
            # string content (e.g. OpenAI)
            AIMessage(
                "",
                tool_calls=[
                    {
                        "name": function_name,
                        "args": function_args,
                        "id": "abc123",
                    },
                ],
            ),
            ToolMessage(
                json.dumps({"result": 3}),
                name=function_name,
                tool_call_id="abc123",
            ),
        ]
        result_string_content = model_with_tools.invoke(messages_string_content)
        assert isinstance(result_string_content, AIMessage)

    def test_tool_message_histories_list_content(
        self,
        model: BaseChatModel,
    ) -> None:
        """
        Test that message histories are compatible with list tool contents
        (e.g. Anthropic).
        """
        if not self.has_tool_calling:
            pytest.skip("Test requires tool calling.")
        model_with_tools = model.bind_tools([my_adder_tool])
        function_name = "my_adder_tool"
        function_args = {"a": 1, "b": 2}

        messages_list_content = [
            HumanMessage("What is 1 + 2"),
            # List content (e.g., Anthropic)
            AIMessage(
                [
                    {"type": "text", "text": "some text"},
                    {
                        "type": "tool_use",
                        "id": "abc123",
                        "name": function_name,
                        "input": function_args,
                    },
                ],
                tool_calls=[
                    {
                        "name": function_name,
                        "args": function_args,
                        "id": "abc123",
                    },
                ],
            ),
            ToolMessage(
                json.dumps({"result": 3}),
                name=function_name,
                tool_call_id="abc123",
            ),
        ]
        result_list_content = model_with_tools.invoke(messages_list_content)
        assert isinstance(result_list_content, AIMessage)

    def test_structured_few_shot_examples(self, model: BaseChatModel) -> None:
        """
        Test that model can process few-shot examples with tool calls.
        """
        if not self.has_tool_calling:
            pytest.skip("Test requires tool calling.")
        model_with_tools = model.bind_tools([my_adder_tool], tool_choice="any")
        function_name = "my_adder_tool"
        function_args = {"a": 1, "b": 2}
        function_result = json.dumps({"result": 3})

        messages_string_content = [
            HumanMessage("What is 1 + 2"),
            AIMessage(
                "",
                tool_calls=[
                    {
                        "name": function_name,
                        "args": function_args,
                        "id": "abc123",
                    },
                ],
            ),
            ToolMessage(
                function_result,
                name=function_name,
                tool_call_id="abc123",
            ),
            AIMessage(function_result),
            HumanMessage("What is 3 + 4"),
        ]
        result_string_content = model_with_tools.invoke(messages_string_content)
        assert isinstance(result_string_content, AIMessage)

    def test_image_inputs(self, model: BaseChatModel) -> None:
        if not self.supports_image_inputs:
            return
        image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
        image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": "describe the weather in this image"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
            ],
        )
        model.invoke([message])
