from typing import Callable, Any
import asyncio
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = []
        self.queue = asyncio.Queue()
        self.processing = False

    async def add_request(self, func: Callable, *args, **kwargs) -> Any:
        # Add to queue
        task = (func, args, kwargs)
        await self.queue.put(task)
        
        # Start processing if not already running
        if not self.processing:
            self.processing = True
            asyncio.create_task(self._process_queue())
            
        # Wait for result
        return await self.queue.get()

    async def _process_queue(self):
        while True:
            try:
                # Clean old requests
                current_time = time.time()
                self.requests = [t for t in self.requests if current_time - t < self.time_window]
                
                # Check if we can process more requests
                if len(self.requests) >= self.max_requests:
                    # Wait until we can process more
                    sleep_time = self.requests[0] + self.time_window - current_time
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    continue
                
                # Get next task
                if self.queue.empty():
                    self.processing = False
                    break
                    
                func, args, kwargs = await self.queue.get()
                
                # Execute task
                self.requests.append(time.time())
                result = await func(*args, **kwargs)
                
                # Return result
                await self.queue.put(result)
                
            except Exception as e:
                logger.error(f"Error processing queue: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on error

# Create rate limiters
jina_limiter = RateLimiter(max_requests=20, time_window=60)  # 20 requests per minute
search_limiter = RateLimiter(max_requests=20, time_window=60)  # 20 requests per minute 