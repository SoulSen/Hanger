import inspect

from hanger import Client
from hanger.conversation_event import ChatMessageEvent


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

            func = self._commands.get(arguments.pop(0))

            if not func:
                return
            params = inspect.signature(func).parameters

            if len(params) - 1 == len(arguments):
                for index, param in enumerate(params.values()):
                    if param.kind == inspect.Parameter.KEYWORD_ONLY:
                        break
                else:
                    index = len(params.values()) - 1

                if index == len(params.values()) - 1:
                    await func(*arguments)
                else:
                    await func(*arguments[:index], ''.join(arguments[index:]))

    def add_command(self, func, aliases=[]):
        self._commands[func.__name__] = func

        for alias in aliases:
            self._commands[alias] = func

    def command(self, aliases=[]):
        def decorator(func):
            self.add_command(func, aliases)
            return func

        return decorator
