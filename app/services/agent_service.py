import logging
import os
import time
from typing import Any, Dict

from pydantic import ValidationError

from app.config import settings
from app.constants import AgentConstants
from app.core.interfaces import LLMInterface, VectorStoreInterface
from app.services.llm_service import LLMService
from app.services.tool_service import ToolService
from app.vectorstore import get_retriever
from app.models import (
    ToolSelection,
    RAGResponse,
    ToolExecutionResult,
    GeneralResponse,
    ConversationAnalysis,
    ConversationSummary,
)
from app.logging_config import get_logger, log_error, log_performance

logger = get_logger("app.agent")


class AgentService:
    """High-level agent orchestration. Single responsibility: orchestrate chains and tools.

    This class accepts optional injectable dependencies to support DI and testing.
    If dependencies are not provided, it falls back to the existing concrete
    implementations for backward compatibility.
    """

    def __init__(
        self,
        mode: str = AgentConstants.MODE_CHAT,
        llm: LLMInterface | None = None,
        tool_service: ToolService | None = None,
        vectorstore: VectorStoreInterface | None = None,
    ):
        self.mode = mode
        # Use provided LLM adapter or fallback to existing implementation
        self.llm: LLMInterface = llm if llm is not None else LLMService()
        # ToolService currently manages tool instances; accept injected or create
        self.tool_service = tool_service if tool_service is not None else ToolService()
        # Vectorstore adapter (retriever) used in RAG mode
        self.vectorstore = vectorstore

    async def answer_with_history(
        self, question: str, conversation_history: list
    ) -> str:
        """Answer with conversation history for memory"""
        start_time = time.time()

        logger.info(
            "Processing question with history",
            extra={
                'mode': self.mode,
                'question_length': len(question),
                'history_count': (
                    len(conversation_history) if conversation_history else 0
                ),
            },
        )

        # Build conversation context
        conversation_messages = []

        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-8:]:  # Last 8 messages for better context
                if msg.role == 'user':
                    conversation_messages.append(f"Human: {msg.content}")
                elif msg.role == 'assistant':
                    conversation_messages.append(f"Assistant: {msg.content}")

        # Add current question
        conversation_messages.append(f"Human: {question}")

        # Create full conversation string
        full_conversation = "\n".join(conversation_messages)

        # RAG mode: retrieve -> format -> LLM with conversation context using structured responses
        from app.constants import AgentConstants

        if self.mode == AgentConstants.MODE_RAG:
            try:
                # Prefer an injected vectorstore; fallback to the module-level retriever
                retriever = self.vectorstore or get_retriever()
                # Use invoke method for newer LangChain versions
                docs = retriever.invoke(question) if retriever else []
                context = "\n\n".join([d.page_content for d in docs[:4]])
                sources = (
                    [f"Document {i+1}" for i in range(len(docs[:4]))] if docs else []
                )

                if context:
                    rag_prompt = f"""<system>
You are an AI assistant with access to relevant documents and conversation history.
</system>

<documents>
{context}
</documents>

<conversation_history>
{full_conversation}
</conversation_history>

<instruction>
Please provide a comprehensive answer using the relevant documents and conversation context.
</instruction>"""

                    # Use structured RAG response only
                    rag_response = await self.llm.generate_structured(
                        rag_prompt, RAGResponse
                    )

                    if rag_response:
                        # Include source information if available
                        response = rag_response.answer
                        if sources and rag_response.sources_used:
                            response += f"\n\n*Sources: {', '.join(sources)}*"

                        logger.info(
                            "RAG response generated successfully",
                            extra={
                                'sources_count': len(sources),
                                'context_relevance': rag_response.context_relevance,
                                'response_length': len(response),
                            },
                        )
                        return response
                    else:
                        logger.error("Structured RAG response failed")
                        raise Exception("Failed to generate structured RAG response")
                else:
                    # No context found, use general response
                    logger.warning(
                        "No context retrieved for RAG mode, using general response"
                    )
                    return await self._generate_general_response(
                        question, conversation_history
                    )

            except Exception as e:
                # Log retrieval failure and re-raise for proper error handling
                logger.error(
                    "RAG retrieval failed",
                    extra={
                        'error': str(e),
                        'mode': self.mode,
                        'question_length': len(question),
                    },
                )
                raise e
        elif self.mode == AgentConstants.MODE_TOOLS:
            # Basic tools mode with multiple tool support and conversation context
            return await self._handle_tools_mode_with_history(
                question, conversation_history
            )
        elif self.mode == AgentConstants.MODE_ENHANCED_TOOLS:
            # Enhanced tools mode uses heavy model with advanced tool capabilities
            return await self._handle_enhanced_tools_mode_with_history(
                question, conversation_history
            )
        elif self.mode == AgentConstants.MODE_EXPRESSIVE:
            # Expressive mode uses heavy model with conversation history and structured responses
            heavy = LLMService(model=None)
            heavy.model = os.getenv("GEMINI_HEAVY_MODEL", settings.GEMINI_HEAVY_MODEL)

            heavy_prompt = f"""<system>
You are a sophisticated AI assistant engaging in a conversation. Provide expressive, detailed, and comprehensive responses.
</system>

<conversation>
{full_conversation}
</conversation>

<instruction>
Please provide a thoughtful, expressive, and comprehensive response as the Assistant.
</instruction>"""

            # Use structured response only
            heavy_response = await heavy.generate_structured(
                heavy_prompt, GeneralResponse
            )

            processing_time = (time.time() - start_time) * 1000

            if heavy_response:
                logger.info(
                    "Expressive mode response generated successfully",
                    extra={
                        'processing_time_ms': processing_time,
                        'response_length': len(heavy_response.response),
                        'structured': True,
                    },
                )
                log_performance(
                    "expressive_mode_response", processing_time, {'structured': True}
                )
                return heavy_response.response
            else:
                logger.error("Expressive mode structured response failed")
                raise Exception(
                    "Failed to generate expressive mode structured response"
                )
        else:
            # Default chat mode uses standard model with conversation history
            chat_prompt = f"""<system>
You are Agent 007, a helpful AI assistant engaging in a conversation.
</system>

<conversation>
{full_conversation}
</conversation>

<instruction>
Please provide a helpful and conversational response as the Assistant.
</instruction>"""

            # Use structured response for consistency
            heavy_response = await self.llm.generate_structured(
                chat_prompt, GeneralResponse
            )

            processing_time = (time.time() - start_time) * 1000

            if heavy_response:
                logger.info(
                    "Heavy mode response generated successfully",
                    extra={
                        'processing_time_ms': processing_time,
                        'response_length': len(heavy_response.response),
                        'structured': True,
                    },
                )
                log_performance(
                    "heavy_mode_response", processing_time, {'structured': True}
                )
                return heavy_response.response
            else:
                logger.error("Heavy mode structured response failed")
                raise Exception("Failed to generate heavy mode structured response")

    async def _handle_tools_mode_with_history(
        self, question: str, conversation_history: list
    ) -> str:
        """Handle tool-based questions with conversation history context"""

        # Get available tools
        available_tools = self.tool_service.get_available_tools()

        # Build conversation context for tool selection
        conversation_context = ""
        if conversation_history:
            context_messages = []
            for msg in conversation_history[-4:]:  # Last 4 messages for tool context
                role = "Human" if msg.role == 'user' else "Assistant"
                context_messages.append(f"{role}: {msg.content}")
            if context_messages:
                conversation_context = (
                    f"\n\nConversation context:\n{chr(10).join(context_messages)}\n"
                )

        # Create tool selection prompt - let PydanticOutputParser handle format instructions
        tool_selection_prompt = f"""<system>
You are an AI agent that can use various tools to help users. Analyze the user's question and determine which tool to use and what parameters to extract.
</system>

<available_tools>
{self._format_tools_for_prompt(available_tools)}
</available_tools>{conversation_context}

<user_question>
{question}
</user_question>

<instruction>
Select the most appropriate tool and extract the necessary parameters. If no specific tool is needed for a general knowledge question, use "llm_only" as the tool name.
</instruction>"""

        try:
            # Get structured tool selection from LLM using enhanced Pydantic model
            tool_decision = await self.llm.generate_structured(
                tool_selection_prompt, ToolSelection
            )

            if tool_decision is None:
                logger.error("Structured tool selection failed")
                raise Exception("Failed to generate structured tool selection")

            selected_tool = tool_decision.selected_tool
            parameters = tool_decision.parameters
            reasoning = tool_decision.reasoning

            # Execute the selected tool
            if selected_tool == "llm_only" or selected_tool not in available_tools:
                return await self._generate_general_response(
                    question, conversation_history
                )

            # Execute the tool and create structured result
            start_time = time.time()
            try:
                result = self.tool_service.execute_tool(selected_tool, **parameters)
                execution_time = time.time() - start_time

                # Create structured tool execution result
                tool_result = ToolExecutionResult(
                    tool_name=selected_tool,
                    success=True,
                    result=str(result),
                    parameters_used=parameters,
                    execution_time=execution_time,
                )

                # Generate structured response about the tool execution
                response_prompt = f"""<system>
You are Agent 007, a helpful AI assistant that has just used a tool to gather information for the user.
</system>

<user_question>
{question}
</user_question>

<tool_execution>
<tool_name>{selected_tool}</tool_name>
<parameters>{parameters}</parameters>
<result>{result}</result>
</tool_execution>

<instruction>
Provide a helpful response to the user incorporating the tool results. Be natural and conversational.
</instruction>"""

                final_response = await self.llm.generate_structured(
                    response_prompt, GeneralResponse
                )

                if final_response:
                    logger.info(
                        "Tool execution response generated",
                        extra={
                            'tool_name': selected_tool,
                            'execution_time': execution_time,
                            'success': True,
                        },
                    )
                    return final_response.response
                else:
                    logger.error(
                        "Failed to generate structured tool execution response"
                    )
                    raise Exception(
                        "Failed to generate structured tool execution response"
                    )

            except Exception as tool_error:
                logger.error(f"Tool execution failed: {tool_error}")
                # Create failed tool result
                tool_result = ToolExecutionResult(
                    tool_name=selected_tool,
                    success=False,
                    result=f"Tool execution failed: {str(tool_error)}",
                    parameters_used=parameters,
                    execution_time=time.time() - start_time,
                )
                return f"I tried to use the {selected_tool} tool to help you, but encountered an issue. Let me provide a general response instead."

        except ValidationError as e:
            logger.error(
                "Pydantic validation error in tool selection",
                extra={
                    'error': str(e),
                    'question': question[:100],  # First 100 chars for context
                    'available_tools': list(available_tools.keys()),
                },
            )
            raise e
        except Exception as e:
            logger.error(
                "Unexpected error in LLM tool selection",
                extra={
                    'error': str(e),
                    'question': question[:100],
                    'available_tools': list(available_tools.keys()),
                },
            )
            raise e

    async def _handle_enhanced_tools_mode_with_history(
        self, question: str, conversation_history: list
    ) -> str:
        """Handle enhanced tool-based questions with heavy model and advanced capabilities"""

        # Use heavy model for enhanced tools mode
        heavy_llm = LLMService(model=None)
        heavy_llm.model = os.getenv("GEMINI_HEAVY_MODEL", settings.GEMINI_HEAVY_MODEL)

        # Get available tools
        available_tools = self.tool_service.get_available_tools()

        # Build enhanced conversation context for tool selection
        conversation_context = ""
        if conversation_history:
            context_messages = []
            for msg in conversation_history[-6:]:  # More context for enhanced mode
                role = "Human" if msg.role == 'user' else "Assistant"
                context_messages.append(f"{role}: {msg.content}")
            if context_messages:
                conversation_context = (
                    f"\n\nConversation context:\n{chr(10).join(context_messages)}\n"
                )

        # Create enhanced tool selection prompt with XML format
        enhanced_tool_selection_prompt = f"""<system>
You are Agent 007, an advanced AI agent with sophisticated tool usage capabilities. You have access to multiple tools and can chain them together for complex tasks. Analyze the user's question deeply and determine the optimal tool strategy.
</system>

<available_tools>
{self._format_tools_for_prompt(available_tools)}
</available_tools>{conversation_context}

<user_question>
{question}
</user_question>

<instruction>
Select the most appropriate tool and extract the necessary parameters. Consider multi-step approaches if needed. If no specific tool is required for a general knowledge question, use "llm_only" as the tool name. Provide detailed reasoning for your tool selection.
</instruction>"""

        try:
            # Get structured tool selection from heavy LLM using enhanced Pydantic model
            tool_decision = await heavy_llm.generate_structured(
                enhanced_tool_selection_prompt, ToolSelection
            )

            if tool_decision is None:
                logger.error("Enhanced tool selection failed")
                raise Exception("Failed to generate enhanced tool selection")

            selected_tool = tool_decision.selected_tool
            parameters = tool_decision.parameters
            reasoning = tool_decision.reasoning

            logger.info(
                "Enhanced tool selection completed",
                extra={
                    'selected_tool': selected_tool,
                    'reasoning': reasoning[:100] if reasoning else None,
                    'parameters': parameters,
                },
            )

            # Execute the selected tool
            if selected_tool == "llm_only" or selected_tool not in available_tools:
                # Use heavy model for general response in enhanced mode
                return await self._generate_enhanced_general_response(
                    question, conversation_history, heavy_llm
                )

            # Execute the tool and create structured result
            start_time = time.time()
            try:
                result = self.tool_service.execute_tool(selected_tool, **parameters)
                execution_time = time.time() - start_time

                # Create structured tool execution result
                tool_result = ToolExecutionResult(
                    tool_name=selected_tool,
                    success=True,
                    result=str(result),
                    parameters_used=parameters,
                    execution_time=execution_time,
                )

                # Generate enhanced structured response about the tool execution using XML
                enhanced_response_prompt = f"""<system>
You are Agent 007, an advanced AI assistant that has just used a sophisticated tool to gather information. Provide comprehensive, analytical, and detailed responses.
</system>

<user_question>
{question}
</user_question>

<tool_execution>
<tool_name>{selected_tool}</tool_name>
<parameters>{parameters}</parameters>
<result>{result}</result>
<reasoning>{reasoning}</reasoning>
</tool_execution>

<conversation_context>{conversation_context}</conversation_context>

<instruction>
Provide a comprehensive, insightful response incorporating the tool results. Include analysis, context, and actionable insights. Be thorough yet conversational.
</instruction>"""

                final_response = await heavy_llm.generate_structured(
                    enhanced_response_prompt, GeneralResponse
                )

                if final_response:
                    logger.info(
                        "Enhanced tool execution response generated",
                        extra={
                            'tool_name': selected_tool,
                            'execution_time': execution_time,
                            'success': True,
                            'response_length': len(final_response.response),
                        },
                    )
                    return final_response.response
                else:
                    logger.error("Failed to generate enhanced tool execution response")
                    raise Exception(
                        "Failed to generate enhanced tool execution response"
                    )

            except Exception as tool_error:
                logger.error(f"Enhanced tool execution failed: {tool_error}")
                # Create failed tool result
                tool_result = ToolExecutionResult(
                    tool_name=selected_tool,
                    success=False,
                    result=f"Tool execution failed: {str(tool_error)}",
                    parameters_used=parameters,
                    execution_time=time.time() - start_time,
                )
                return f"I attempted to use the {selected_tool} tool with advanced capabilities, but encountered an issue. Let me provide a comprehensive response using my knowledge instead."

        except ValidationError as e:
            logger.error(
                "Pydantic validation error in enhanced tool selection",
                extra={
                    'error': str(e),
                    'question': question[:100],
                    'available_tools': list(available_tools.keys()),
                },
            )
            raise e
        except Exception as e:
            logger.error(
                "Unexpected error in enhanced tool selection",
                extra={
                    'error': str(e),
                    'question': question[:100],
                    'available_tools': list(available_tools.keys()),
                },
            )
            raise e

    async def _generate_enhanced_general_response(
        self, question: str, conversation_history: list, heavy_llm: LLMService
    ) -> str:
        """Generate an enhanced general response using heavy model and conversation context"""
        # Build conversation context
        conversation_messages = []
        if conversation_history:
            for msg in conversation_history[-10:]:  # More context for enhanced mode
                if msg.role == 'user':
                    conversation_messages.append(f"Human: {msg.content}")
                elif msg.role == 'assistant':
                    conversation_messages.append(f"Assistant: {msg.content}")

        conversation_messages.append(f"Human: {question}")
        full_conversation = "\n".join(conversation_messages)

        enhanced_general_prompt = f"""<system>
You are Agent 007, an advanced AI assistant with enhanced capabilities. Provide comprehensive, analytical, and insightful responses that go beyond surface-level answers.
</system>

<conversation>
{full_conversation}
</conversation>

<instruction>
Provide a thorough, analytical response considering multiple perspectives. Include relevant context, implications, and actionable insights where appropriate. Be comprehensive yet engaging.
</instruction>"""

        # Use heavy model for enhanced response
        enhanced_response = await heavy_llm.generate_structured(
            enhanced_general_prompt, GeneralResponse
        )

        if enhanced_response:
            logger.info(
                "Enhanced general response generated successfully",
                extra={
                    'response_length': len(enhanced_response.response),
                    'structured': True,
                    'model': 'heavy',
                },
            )
            return enhanced_response.response
        else:
            logger.error("Failed to generate enhanced general response")
            raise Exception("Failed to generate enhanced general response")

    async def _generate_general_response(
        self, question: str, conversation_history: list
    ) -> str:
        """Generate a general structured response using conversation context"""
        # Build conversation context
        conversation_messages = []
        if conversation_history:
            for msg in conversation_history[-8:]:
                if msg.role == 'user':
                    conversation_messages.append(f"Human: {msg.content}")
                elif msg.role == 'assistant':
                    conversation_messages.append(f"Assistant: {msg.content}")

        conversation_messages.append(f"Human: {question}")
        full_conversation = "\n".join(conversation_messages)

        general_prompt = f"""<system>
You are Agent 007, an intelligent AI assistant engaging in a conversation.
</system>

<conversation>
{full_conversation}
</conversation>

<instruction>
Please provide a helpful and engaging response as the Assistant, considering the conversation context.
</instruction>"""

        # Use structured response only
        general_response = await self.llm.generate_structured(
            general_prompt, GeneralResponse
        )

        if general_response:
            logger.info(
                "General response generated successfully",
                extra={
                    'response_length': len(general_response.response),
                    'structured': True,
                },
            )
            return general_response.response
        else:
            logger.error("Failed to generate structured general response")
            raise Exception("Failed to generate structured general response")

    async def _analyze_conversation(
        self, conversation_history: list
    ) -> ConversationAnalysis:
        """Analyze conversation context for better responses"""
        if not conversation_history:
            return ConversationAnalysis(
                main_topic="New conversation",
                user_intent="Starting a conversation",
                context_summary="No previous context",
                relevant_history=[],
            )

        # Build conversation for analysis
        conversation_text = "\n".join(
            [
                f"{'Human' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in conversation_history[-10:]  # Last 10 messages
            ]
        )

        analysis_prompt = f"""<system>
You are an AI assistant specialized in analyzing conversations to understand context and user intent.
</system>

<conversation>
{conversation_text}
</conversation>

<instruction>
Provide a structured analysis of the conversation, including main topic, user intent, context summary, and relevant history.
</instruction>"""

        analysis = await self.llm.generate_structured(
            analysis_prompt, ConversationAnalysis
        )

        if analysis:
            logger.info(
                "Conversation analysis completed",
                extra={
                    'main_topic': analysis.main_topic,
                    'user_intent': analysis.user_intent,
                    'history_items': len(analysis.relevant_history),
                },
            )
            return analysis
        else:
            logger.error("Failed to generate structured conversation analysis")
            raise Exception("Failed to generate structured conversation analysis")

    async def generate_conversation_summary(
        self, conversation_history: list, current_message: str = ""
    ) -> ConversationSummary:
        """Generate a summary and title for a conversation"""
        if not conversation_history and not current_message:
            return ConversationSummary(
                title="New Chat",
                summary="Empty conversation",
                key_topics=[],
                conversation_type="casual_chat",
            )

        # Build conversation text including current message
        conversation_messages = []

        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            role = "Human" if msg.role == 'user' else "Assistant"
            conversation_messages.append(f"{role}: {msg.content}")

        # Add current message if provided
        if current_message:
            conversation_messages.append(f"Human: {current_message}")

        conversation_text = "\n".join(conversation_messages)

        summary_prompt = f"""<system>
You are an AI assistant specialized in creating conversation summaries and titles.
</system>

<conversation>
{conversation_text}
</conversation>

<instruction>
Generate a title that captures the main topic in 2-4 words (like "Weather Inquiry", "Python Help", "Travel Planning").
Provide a brief summary and identify key topics discussed.
</instruction>"""

        summary = await self.llm.generate_structured(
            summary_prompt, ConversationSummary
        )

        if summary:
            logger.info(
                "Conversation summary generated",
                extra={
                    'title': summary.title,
                    'conversation_type': summary.conversation_type,
                    'topic_count': len(summary.key_topics),
                },
            )
            return summary
        else:
            logger.error("Failed to generate structured conversation summary")
            # Return a basic summary based on first message
            first_user_msg = current_message or (
                next(
                    (msg.content for msg in conversation_history if msg.role == 'user'),
                    "",
                )
            )
            title = (
                first_user_msg[:30] + "..."
                if len(first_user_msg) > 30
                else first_user_msg or "New Chat"
            )

            return ConversationSummary(
                title=title,
                summary=f"Conversation about: {title}",
                key_topics=[title.split()[0]] if title.split() else [],
                conversation_type="question_answer",
            )

    # Note: previous heuristic location extraction has been removed to keep
    # tool selection strictly LLM-driven.

    # Note: deprecated URL and GitHub repo extractors removed with heuristics.

    def _format_tools_for_prompt(self, tools: dict) -> str:
        """Format available tools for LLM prompt"""
        formatted_tools = []

        # Tool descriptions with expected parameters
        tool_params = {
            "web_search": {"query": "search query string"},
            "weather": {"location": "city, country or location name"},
            "github_issues": {
                "repo": "owner/repository format",
                "state": "open/closed (optional)",
                "limit": "number of issues (optional)",
            },
            "http_tool": {
                "url": "HTTP URL",
                "method": "GET/POST/etc (optional)",
                "json": "JSON data (optional)",
            },
            "vector_query": {
                "query": "search query for knowledge base",
                "k": "number of results (optional)",
            },
        }

        for tool_name, description in tools.items():
            params = tool_params.get(tool_name, {})
            param_str = ", ".join([f"{k}: {v}" for k, v in params.items()])
            formatted_tools.append(f"- {tool_name}: {description}")
            if param_str:
                formatted_tools.append(f"  Parameters: {param_str}")

        logger.info(
            "Tools formatted for prompt",
            extra={'tool_count': len(tools), 'available_tools': list(tools.keys())},
        )
        return "\n".join(formatted_tools)
