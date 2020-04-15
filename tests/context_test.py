from hanger.ext import commands


bot = commands.Bot('//', refresh_token="./refresh-token.txt")


@bot.event
async def on_connect():
    print('Ready!!!!')


@bot.event
async def on_message(event):
    if event.text == '//help':
        async with event.conversation.typing():
            async with event.conversation.focused():
                await event.respond('Hello!')


bot.connect()
