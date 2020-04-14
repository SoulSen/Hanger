import asyncio

from hanger.enums import TypingStatus


class Typing:
    def __init__(self, conversation):
        self._conversation = conversation

    async def __aenter__(self):
        await self._conversation.set_typing(TypingStatus.STARTED)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._conversation.set_typing(TypingStatus.STOPPED)


class Focus:
    def __init__(self, conversation):
        self._conversation = conversation
        self.loop = self._conversation._client.loop
        self.task = None

    async def do_focus(self):
        while True:
            await self._conversation.focus()
            await asyncio.sleep(5)

    async def __aenter__(self):
        await self._conversation.focus()
        self.task = asyncio.ensure_future(self.do_focus(), loop=self.loop)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.task.cancel()
