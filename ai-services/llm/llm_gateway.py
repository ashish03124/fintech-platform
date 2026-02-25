# ai-services/llm/llm_gateway.py
from typing import Dict, Any, List, Optional, AsyncGenerator
import openai
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMGateway:
    def __init__(self):
        self.openai_client = None
        self.models = {
            "gpt-4": {
                "provider": "openai",
                "max_tokens": 8192,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06
            },
            "gpt-4-turbo": {
                "provider": "openai",
                "max_tokens": 4096,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03
            },
            "gpt-3.5-turbo": {
                "provider": "openai",
                "max_tokens": 4096,
                "cost_per_1k_input": 0.0015,
                "cost_per_1k_output": 0.002
            },
            "claude-2": {
                "provider": "anthropic",
                "max_tokens": 100000,
                "cost_per_1k_input": 0.01102,
                "cost_per_1k_output": 0.03268
            }
        }
        
    def initialize(self, openai_api_key: str, anthropic_api_key: str = None):
        """Initialize LLM clients"""
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        
        if anthropic_api_key:
            self.anthropic_client = ChatAnthropic(
                anthropic_api_key=anthropic_api_key,
                model="claude-2"
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.1,
        max_tokens: int = 1000,
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None] or str:
        """Generate response from LLM"""
        try:
            if model not in self.models:
                model = "gpt-4"
            
            provider = self.models[model]["provider"]
            
            if provider == "openai":
                return await self._generate_openai(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    system_prompt=system_prompt
                )
            elif provider == "anthropic":
                return await self._generate_anthropic(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    system_prompt=system_prompt
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    async def _generate_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        system_prompt: Optional[str]
    ):
        """Generate using OpenAI"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        if stream:
            return self._stream_openai_response(messages, model, temperature, max_tokens)
        else:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            return response.choices[0].message.content
    
    async def _stream_openai_response(self, messages: List[Dict], model: str, 
                                    temperature: float, max_tokens: int):
        """Stream OpenAI response"""
        try:
            stream = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    async def _generate_anthropic(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        system_prompt: Optional[str]
    ):
        """Generate using Anthropic Claude"""
        if not hasattr(self, 'anthropic_client'):
            raise ValueError("Anthropic client not initialized")
        
        messages = [HumanMessage(content=prompt)]
        
        if system_prompt:
            # Claude doesn't have explicit system messages in same way
            prompt = f"{system_prompt}\n\n{prompt}"
        
        if stream:
            callback = AsyncIteratorCallbackHandler()
            
            # This would need proper async handling for streaming
            # Simplified version
            response = await self.anthropic_client.agenerate([messages])
            return response.generations[0][0].text
        else:
            response = await self.anthropic_client.agenerate([messages])
            return response.generations[0][0].text
    
    async def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for API call"""
        if model not in self.models:
            model = "gpt-4"
        
        model_info = self.models[model]
        input_cost = (input_tokens / 1000) * model_info["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * model_info["cost_per_1k_output"]
        
        return round(input_cost + output_cost, 6)
    
    async def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except:
            # Fallback: approximate token count (1 token ≈ 4 characters)
            return len(text) // 4
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models"""
        return [
            {
                "name": model,
                "provider": info["provider"],
                "max_tokens": info["max_tokens"],
                "description": f"{model.upper()} from {info['provider'].title()}"
            }
            for model, info in self.models.items()
        ]