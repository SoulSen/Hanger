class Context:
    def __init__(self, bot, event, command):
        self.author = event.user
        self.conversation = event.conversation
        self.bot = bot
        self.attachments = event.attachments
        self.timestamp = event.timestamp
        self.command = command

        self._event = event

    async def respond(self, text='', location=None, image=None, me=False):
        await self._event.respond(text, location, image, me)
