import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Coroutine]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable[..., Coroutine]) -> None:
        self._handlers[event].append(handler)

    async def publish(self, event: str, payload: Any = None) -> None:
        handlers = self._handlers.get(event, [])
        if handlers:
            await asyncio.gather(*[h(payload) for h in handlers], return_exceptions=True)


bus = EventBus()
