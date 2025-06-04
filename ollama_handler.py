import aiohttp
import asyncio
import collections
from ollama import chat
from pydantic import BaseModel, Field
from typing import Optional, Literal

class EmojiResponse(BaseModel):
    """Schema for structured emoji response from Ollama."""
    emoji: str = Field(description="A single emoji character that reacts to the message")
    confidence: float = Field(default=1.0, description="Confidence level in the selected emoji")

class TextResponse(BaseModel):
    """Schema for structured text response from Ollama."""
    text: str = Field(description="The text response from the model")
    related_topics: Optional[list[str]] = Field(default=None, description="Related topics to the response")

class OllamaSession:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OllamaSession, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    async def initialize(self, model="qwen3:0.6b", host="http://localhost:11434"):
        if not self.initialized:
            self.model = model
            self.host = host
            self.session = aiohttp.ClientSession()
            # Store conversation context per channel
            self.conversation_context = collections.defaultdict(lambda: collections.deque(maxlen=10))
            self.last_reactions = collections.defaultdict(lambda: "🤪")  # Default emoji
            self.initialized = True
        return self
    
    async def close(self):
        if hasattr(self, 'session') and self.session:
            await self.session.close()
            self.initialized = False
    
    async def get_emoji_reaction(self, channel_id, message_content, author_name, last_reaction=None, debug=True):
        # Update last reaction if provided
        if last_reaction:
            self.last_reactions[channel_id] = last_reaction
            
        # Add message to context
        self.conversation_context[channel_id].append({
            'author': author_name,
            'content': message_content
        })
        
        # Format conversation context for the prompt
        context_messages = list(self.conversation_context[channel_id])
        context_str = "\nRecent conversation:\n" + "\n".join([
            f"{m['author']}: {m['content']}" for m in context_messages
        ])
        
        try:
            with open('reactionprompt.txt', 'r') as promptheader:
                prompt = (
                    promptheader.read() + "\n"
                    f"Do NOT use the emoji \"{self.last_reactions[channel_id]}\". \n" + 
                    f"Current message to react to: {author_name}: {message_content}\n" +
                    context_str
                )
                
                
                # Debug output
                if debug:
                    print("\n==== LLM DEBUGGING ====")
                    print(f"Channel ID: {channel_id}")
                    print(f"Last reaction: {self.last_reactions[channel_id]}")
                    print("\nCONTEXT HISTORY:")
                    for i, msg in enumerate(context_messages):
                        print(f"[{i+1}] {msg['author']}: {msg['content']}")
                    print("\nPROMPT SENT TO LLM:")
                    print("--------------------")
                    print(prompt)
                    print("--------------------\n")
                
                # Use structured output with format parameter
                response = chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    format=EmojiResponse.model_json_schema(),
                    options={"temperature": 0.2}
                )
                
                if response and hasattr(response, 'message') and hasattr(response.message, 'content'):
                    emoji_data = EmojiResponse.model_validate_json(response.message.content)
                    emoji_response = emoji_data.emoji
                    
                    # Update last reaction
                    if emoji_response:
                        self.last_reactions[channel_id] = emoji_response[0]
                    
                    if debug:
                        print("\nSTRUCTURED RESPONSE:")
                        print(f"Emoji: {emoji_response}")
                        print(f"Confidence: {emoji_data.confidence}")
                        print("--------------------\n")
                        
                    return emoji_response
                return None
        except Exception as e:
            print(f"Error in get_emoji_reaction: {e}")
            return None
        except Exception as e:
            print(f"Error in get_emoji_reaction: {e}")
            return None
        return None
    
    async def ask_ollama(self, prompt, model=None, host=None):
        model = model or self.model
        host = host or self.host
        
        try:
            # Use the chat function with structured output
            response = chat(
                model=model,
                messages=[{"role": "user", "content": prompt + " Return as JSON."}],
                format=TextResponse.model_json_schema(),
                options={"temperature": 0.2, "num_predict": 100}  # Using num_predict instead of max_tokens
            )
            
            if response and hasattr(response, 'message') and hasattr(response.message, 'content'):
                text_data = TextResponse.model_validate_json(response.message.content)
                return text_data.text
            return None
        except Exception as e:
            print(f"Error in ask_ollama: {e}")
            return None

# Global instance
_ollama_instance = None

async def get_ollama_session():
    global _ollama_instance
    if _ollama_instance is None or not _ollama_instance.initialized:
        _ollama_instance = OllamaSession()
        await _ollama_instance.initialize()
    return _ollama_instance

# Legacy function for backward compatibility
async def ask_ollama_for_emoji(message_content, last_reaction=None):
    # Extract channel_id and author_name from message_content if possible
    channel_id = 0  # Default channel ID
    author_name = "User"  # Default author name
    
    # Check if the message content contains channel context
    lines = message_content.strip().split('\n')
    for line in lines:
        if line.startswith("Current message to react to:"):
            # Try to extract author name from this line
            parts = line.split(':', 2)
            if len(parts) >= 3:
                author_name = parts[1].strip()
    
    session = await get_ollama_session()
    response = await session.get_emoji_reaction(
        channel_id=channel_id,
        message_content=message_content,
        author_name=author_name,
        last_reaction=last_reaction,
        debug=True  # Enable debugging output
    )
    return response

# Legacy function for backward compatibility
async def ask_ollama(prompt, model="llama3.2:1b", host="http://localhost:11434"):
    session = await get_ollama_session()
    return await session.ask_ollama(prompt, model, host)

