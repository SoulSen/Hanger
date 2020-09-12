from hanger.ext import commands


bot = commands.Bot('//', refresh_token="./refresh-token.txt")


@bot.event
async def on_ready():
    print('Ready!!!!')

    for convo in bot._cache.get_all_conversations():
        print(convo.name)
        for participant in convo._participants.values():
            print(participant.display_name)
        print('========')


@bot.event
async def on_hangout(event):
    conv_id = event.conversation.id
    print(f"https://plus.google.com/hangouts/_/CONVERSATION/#{conv_id}")


bot.connect()
