from bot_helper import *

async def calculate_market_probability_change(data, market, amount):
    msg = data['msg']
    current_liquidity = market['liquidity']
    current_probability = market['probability']
    
    new_probability = (current_liquidity * current_probability + amount) / (current_liquidity + abs(amount))
    new_probability = max(0.0, min(1.0, new_probability))
    
    return new_probability

async def market_resolve(data):
    msg = data['msg']
    brook = data['brook']

    prompts = [
        "What is the market name?",
        "What are you resolving it to? (y/n)",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    market_name, resolution_str = responses
    resolution = 'y' in resolution_str.lower()

    market = execute_query("SELECT * FROM markets WHERE name = ?", (market_name,), fetchone=True)
    
    if not market:
        await send_message(data, "Market not found.")
        return
    
    if str(msg.author.id) != market['creator']:
        await send_message(data, "You cannot resolve markets you do not own!")
        return
    
    execute_query("UPDATE markets SET resolved = 1, resolution = ? WHERE name = ?", (resolution, market_name))

    liquidity_remaining = market['liquidity']
    
    user_shares = execute_query("SELECT user_id, shares FROM user_shares WHERE market_name = ?", (market_name,))
    for user_id, shares in user_shares:
        payout = abs(shares) if (resolution and shares > 0) or (not resolution and shares < 0) else 0
        if payout > 0:
            if payout > liquidity_remaining:
                await send_message(data, f"Not enough liquidity remaining to pay user {user_id}!")
                continue
            await brook.pay(user_id, payout, msg.channel)
            liquidity_remaining -= payout

    if liquidity_remaining > 0:
        await brook.pay(market['creator'], liquidity_remaining, msg.channel)

async def market_buy(data):
    msg = data['msg']
    brook = data['brook']

    prompts = [
        "What is the market name?",
        "How many shares do you want to buy?",
    ]
    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    try:
        responses[1] = int(responses[1])
    except ValueError:
        await send_message(data, "Amount must be an integer.")
        return
    
    market_name, amount = responses
    market = execute_query("SELECT * FROM markets WHERE name = ?", (market_name,), fetchone=True)
    
    if not market:
        await send_message(data, "Market not found.")
        return
    
    if market['resolved']:
        await send_message(data, "Market is already resolved.")
        return
    
    if amount > 0:
        price = market['probability'] * amount
    else:
        price = (1 - market['probability']) * abs(amount)

    future = await brook.request_payment(msg.author, price, msg.channel, "Market shares for market '" + market_name + "'")
    try:
        await future
    except Exception as e:
        await send_message(data, "Payment request denied. Purchase cancelled.")
        return
    
    user_id = str(msg.author.id)

    existing_shares = execute_query("SELECT shares FROM user_shares WHERE market_name = ? AND user_id = ?", (market_name, user_id), fetchone=True)
    if existing_shares:
        new_shares = existing_shares['shares'] + amount
        execute_query("UPDATE user_shares SET shares = ? WHERE market_name = ? AND user_id = ?", (new_shares, market_name, user_id))
    else:
        execute_query("INSERT INTO user_shares (market_name, user_id, shares) VALUES (?, ?, ?)", (market_name, user_id, amount))
    
    new_probability = await calculate_market_probability_change(data, market, amount)

    execute_query("UPDATE markets SET liquidity = liquidity + ?, probability = ? WHERE name = ?", (price, new_probability, market_name))

    await send_message(data, f"Purchase made. New probability: {new_probability * 100}%")

async def new_market(data):
    msg = data['msg']
    brook = data['brook']

    await send_message(data, "WARNING: super buggy and infinite money exploits abound. Ye've been warned!")

    prompts = [
        "What is the market name/resolution criteria?",
        "What is the starting liquidity?",
        "What is the initialized probability?",
    ]
    responses = await get_user_input(data, prompts)
    if not responses:
        return
    
    try:
        responses[1] = int(responses[1])
        probability_str = responses[2]
        if probability_str.endswith('%'):
            probability_str = probability_str[:-1]
        responses[2] = float(probability_str)
    except ValueError:
        await send_message(data, "Liquidity must be an integer and probability must be a number.")
        return
    
    market_name, starting_liquidity, initialized_probability = responses

    if initialized_probability >= 1:
        initialized_probability = initialized_probability / 100

    future = await brook.request_payment(msg.author, starting_liquidity, msg.channel, "Market liquidity for market '" + market_name + "'")
    try:
        await future
    except Exception as e:
        await send_message(data, "Payment request denied. Market creation cancelled.")
        return

    market = {
        "name": market_name,
        "starting_liquidity": starting_liquidity,
        "initialized_probability": initialized_probability,
        "liquidity": starting_liquidity,
        "probability": initialized_probability,
        "creator": str(msg.author.id),
        "resolved": False,
        "resolution": None,
    }

    existing_market = execute_query("SELECT name FROM markets WHERE name = ?", (market_name,))
    if existing_market:
        await send_message(data, "Market name already exists.")
        return
    
    execute_query("INSERT INTO markets (name, starting_liquidity, initialized_probability, liquidity, probability, creator, resolved, resolution) VALUES (?, ?, ?, ?, ?, ?, 0, NULL)", 
                  (market_name, starting_liquidity, initialized_probability, starting_liquidity, initialized_probability, str(msg.author.id)))

    await send_message(data, "New market created: " + market_name)

async def view_markets(data):
    msg = data['msg']
    markets = execute_query("SELECT name, probability FROM markets")
    
    response = 'Markets: '
    for market in markets:
        response += f'\n{market["name"]}: {market["probability"] * 100}%'
    await send_message(data, response)
