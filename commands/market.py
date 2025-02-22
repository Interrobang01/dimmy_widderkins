from bot_helper import *

async def _calculate_market_probability_change(data, market, amount):
    msg = data['msg']
    current_liquidity = market['liquidity']
    current_probability = market['probability']
    
    # Calculate new probability with the same formula but clamp between 0 and 1
    new_probability = (current_liquidity * current_probability + amount) / (current_liquidity + abs(amount))
    
    # Clamp probability between 0 and 1
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

    # Get market
    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    if market_name not in markets:
        await send_message(data, "Market not found.")
        return
    
    market = markets[market_name]
    if str(msg.author.id) != market['creator']:
        await send_message(data, "You cannot resolve markets you do not own!")
        return
    
    market['resolved'] = True
    market['resolution'] = resolution

    liquidity_remaining = market['liquidity']
    
    # Pay shareholders
    for user_id, shares in market['user_shares'].items():
        payout = abs(shares) if (resolution and shares > 0) or (not resolution and shares < 0) else 0
        if payout > 0:
            if payout > liquidity_remaining:
                await send_message(data, f"Not enough liquidity remaining to pay user {user_id}!")
                continue
            await brook.pay(user_id, payout, msg.channel)
            liquidity_remaining -= payout

    # Pay remaining liquidity to market creator
    if liquidity_remaining > 0:
        await brook.pay(market['creator'], liquidity_remaining, msg.channel)

    write_json(markets, 'markets.json')

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
    
    # Ensure amount is an integer
    try:
        responses[1] = int(responses[1])
    except ValueError:
        await send_message(data, "Amount must be an integer.")
        return
    
    market_name, amount = responses
    # Get market
    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    if market_name not in markets:
        await send_message(data, "Market not found.")
        return
    
    market = markets[market_name]
    if market['resolved']:
        await send_message(data, "Market is already resolved.")
        return
    
    # Calculate price
    if amount > 0:
        price = market['probability'] * amount
    else:
        price = (1 - market['probability']) * abs(amount)

    # Request money
    future = await brook.request_payment(msg.author, price, msg.channel, "Market shares for market '" + market_name + "'")
    try:
        await future
    except Exception as e:
        await send_message(data, "Payment request denied. Purchase cancelled.")
        return
    
    user_id = str(msg.author.id)

    # Update user_shares
    if user_id not in market['user_shares']:
        market['user_shares'][user_id] = amount
    else:
        market['user_shares'][user_id] += amount
    
    # Calculate new probability
    new_probability = await _calculate_market_probability_change(data, market, amount)

    # Update market
    market['liquidity'] += price
    market['probability'] = new_probability
    write_json(markets, 'markets.json')

    await send_message(data, f"Purchace made. New probability: {new_probability * 100}%")


# 1a. Asks the following prompts:
#     "What is the market name?",
#     "What is the starting liquidity?",
#     "What is the initialized probability?",
# 1b. Requests payment from the user equal to the starting liqudity, cancelling if payment is rejected
# 1c. Reserves that money for the market
# 1d. Creates a market message
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
    
    # Ensure liquidity/probability is a integer/number
    try:
        responses[1] = int(responses[1])
        probability_str = responses[2]
        if probability_str.endswith('%'):
            probability_str = probability_str[:-2]
        responses[2] = float(probability_str)
    except ValueError:
        await send_message(data, "Liquidity must be an integer and probability must be a number.")
        return
    
    market_name, starting_liquidity, initialized_probability = responses

    # Convert to fraction
    if initialized_probability >= 1:
        initialized_probability = initialized_probability / 100

    # Request payment from the user equal to the starting liquidity
    future = await brook.request_payment(msg.author, starting_liquidity, msg.channel, "Market liquidity for market '" + market_name + "'")

    # Cancel if request is denied
    try:
        await future
    except Exception as e:
        await send_message(data, "Payment request denied. Market creation cancelled.")
        return



    # Send a market message with the market name, starting liquidity, and initialized probability
    # The message has a "Buy" button that allows users to buy shares in the market
    # The message has a "Resolve" button that allows the market creator to resolve the market
    market = {
        "name": market_name,
        "starting_liquidity": starting_liquidity,
        "initialized_probability": initialized_probability,
        "liquidity": starting_liquidity,
        "probability": initialized_probability,
        "user_shares": {},
        "creator": str(msg.author.id),
        "resolved": False,
        "resolution": None,
    }

    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    # Check duplicate market names
    if market_name in markets:
        await send_message(data, "Market name already exists.")
        return
    
    markets[market_name] = market
    write_json(markets, 'markets.json')

    await send_message(data, "New market created: " + market_name)

async def view_markets(data):
    msg = data['msg']
    # Get markets
    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    response = 'Markets: '
    for market in markets:
        response += f'\n{market}: {markets[market]["probability"] * 100}%'
    await send_message(data, response)

# Function aliases without underscores, using prefixes, and using close synonyms
marketview = view_markets
marketbuy = market_buy
marketresolve = market_resolve
marketnew = new_market
newmarket = new_market
viewmarket = view_markets
viewmarkets = view_markets
buy = market_buy
resolve = market_resolve
markets = view_markets
market = view_markets



