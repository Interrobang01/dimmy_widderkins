async def pay(data):
    msg = data['msg']
    brook = data['brook']
    args = msg.content.split()
    if len(args) < 2:
        await msg.channel.send("Please specify an amount: !pay <amount>")
        return
        
    try:
        amount = int(args[1])
        if amount <= 0:
            await msg.channel.send("Amount must be positive")
            return
    except ValueError:
        await msg.channel.send("Please provide a valid number for the amount")
        return

    user = msg.author
    request_channel = msg.channel
    description = "please donate to help fund my medication"
    
    await brook.request_payment(user, amount, request_channel, description)
