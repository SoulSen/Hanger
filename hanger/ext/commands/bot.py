from hanger import Client
from hanger.conversation_event import ChatMessageEvent
from hanger.ext.commands.context import Context


class Bot(Client):
    def __init__(self, prefix, **options):
        super().__init__(**options)

        self.prefix = prefix
        self._commands = {}

    async def on_message(self, event: ChatMessageEvent) -> None:
        command = event.text

        if command.startswith(self.prefix):
            command = command.replace(self.prefix, '')
            arguments = command.split(' ')

            if arguments[0] in self._commands:
                command = arguments.pop(0)
                command_func = self._commands[command]
                ctx = Context(self, event, command)

                await command_func(ctx, *arguments)

    def add_command(self, func, aliases=[]):
        self._commands[func.__name__] = func

        for alias in aliases:
            self._commands[alias] = func

    def command(self, aliases=[]):
        def decorator(func):
            self.add_command(func, aliases)
            return func

        return decorator

    async def connect(self):
        await self._hangups_client.connect()