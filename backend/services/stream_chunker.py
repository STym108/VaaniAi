import re
from typing import AsyncGenerator

class StreamChunker:
    """
    Buffers streaming token chunks and yields complete sentence strings 
    as soon as sentence boundary punctuation (. ? ! । \n) is encountered.
    """
    def __init__(self):
        # Regex matching sentence ending punctuation including Hindi Purna Viram (।)
        self.boundary_pattern = re.compile(r"([.!?।\n]+)(\s+|$)")

    async def chunk_stream(self, token_generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        buffer = ""
        
        async for token in token_generator:
            buffer += token
            
            # Check for sentence boundaries
            while True:
                match = self.boundary_pattern.search(buffer)
                if match:
                    end_pos = match.end()
                    sentence = buffer[:end_pos].strip()
                    buffer = buffer[end_pos:]
                    
                    if sentence:
                        yield sentence
                else:
                    break
        
        # Yield any remaining text after stream finishes
        if buffer.strip():
            yield buffer.strip()

# Singleton Instance
stream_chunker = StreamChunker()
