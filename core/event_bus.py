"""Event bus for inter-component communication"""
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import asyncio
from utils.logger import logger


class EventBus:
    """Event bus for publish-subscribe pattern"""

    def __init__(self):
        """Initialize event bus"""
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._async_listeners: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event_name: str, callback: Callable, is_async: bool = False):
        """Subscribe to an event

        Args:
            event_name: Event name
            callback: Callback function
            is_async: Whether callback is async
        """
        if is_async:
            self._async_listeners[event_name].append(callback)
        else:
            self._listeners[event_name].append(callback)

        logger.debug(f"Registered listener for event: {event_name}")

    def off(self, event_name: str, callback: Callable):
        """Unsubscribe from an event

        Args:
            event_name: Event name
            callback: Callback function to remove
        """
        if callback in self._listeners[event_name]:
            self._listeners[event_name].remove(callback)

        if callback in self._async_listeners[event_name]:
            self._async_listeners[event_name].remove(callback)

        logger.debug(f"Removed listener for event: {event_name}")

    def emit(self, event_name: str, data: Any = None):
        """Emit an event synchronously

        Args:
            event_name: Event name
            data: Event data
        """
        logger.debug(f"Emitting event: {event_name}")

        # Call synchronous listeners
        for callback in self._listeners[event_name]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in event listener {callback.__name__}: {e}")

    async def emit_async(self, event_name: str, data: Any = None):
        """Emit an event asynchronously

        Args:
            event_name: Event name
            data: Event data
        """
        logger.debug(f"Emitting async event: {event_name}")

        # Call synchronous listeners
        for callback in self._listeners[event_name]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in event listener {callback.__name__}: {e}")

        # Call async listeners
        tasks = []
        for callback in self._async_listeners[event_name]:
            try:
                tasks.append(callback(data))
            except Exception as e:
                logger.error(f"Error in async event listener {callback.__name__}: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def clear(self, event_name: Optional[str] = None):
        """Clear event listeners

        Args:
            event_name: Event name to clear (None for all)
        """
        if event_name:
            self._listeners[event_name].clear()
            self._async_listeners[event_name].clear()
        else:
            self._listeners.clear()
            self._async_listeners.clear()

        logger.debug(f"Cleared listeners for event: {event_name or 'all'}")


# Global event bus instance
event_bus = EventBus()
