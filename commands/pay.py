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

    user = msg.author
    request_channel = msg.channel
    description = "please donate to help fund my medication"

    if amount == 0:
        await send_message(data, "Amount must not be zero you little bitch")
        return

    if amount > 0:
        await brook.request_payment(user, amount, request_channel, description)
    else:
        # Negative amount: pay the user
        #await brook.pay(user, abs(amount), request_channel)
        await send_message(data, "https://tenor.com/view/nuh-uh-beocord-no-lol-gif-24435520")
