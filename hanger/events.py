from typing import Callable

from hangups import event


class EventHandler:
    def __init__(self, client):
        self._client = client

    def register_event(self, event_name: str, hook: Callable):
        getattr(self._client, event_name).add_observer(hook)

    def create_event(self, event_name: str) -> None:
        setattr(self._client, event_name, event.Event('hanger.{}'.format(event_name)))

    async def invoke_event(self, event_name: str, *args, **kwargs) -> None:
        await getattr(self._client, event_name).fire(*args, **kwargs)

    def get_hooks(self, event_name: str) -> Callable:
        return getattr(self._client, event_name)._observers
