async def pay_command(data):
    msg = data['msg']
    brook = data['brook']

    user = msg.author
    amount = 100  # Example amount
    request_channel = msg.channel
    description = "please donate to help fund my medication"
    
    await brook.request_payment(user, amount, request_channel, description)
