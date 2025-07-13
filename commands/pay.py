from bot_helper import send_message

async def pay(data):
    msg = data['msg']
    brook = data['brook']
    args = msg.content.split()
    if len(args) < 2:
        await send_message(data, "Please specify an amount: !pay <amount>")
        return
        
    try:
        amount = int(args[1])
    except ValueError:
        await send_message(data, "Please provide a valid number for the amount")
        return

    user_id = msg.author.id
    request_channel_id = msg.channel.id
    description = "please donate to help fund my medication"
    print(f"Paying {user_id} {amount} in channel {request_channel_id} with description '{description}'")

    if amount == 0:
        await send_message(data, "Amount must not be zero you little bitch")
        return

    if amount > 0:
        brook.request_payment(str(user_id), amount, str(request_channel_id), description)
    else:
        # Negative amount: pay the user
        #await brook.pay(user, abs(amount), request_channel)
        await send_message(data, "https://tenor.com/view/nuh-uh-beocord-no-lol-gif-24435520")
