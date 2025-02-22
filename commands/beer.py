from ..bot_helper import send_message

async def beer(data):
    if not hasattr(beer, 'beercount'):
        beer.beercount = 99

    beer.beercount
    if beer.beercount == 0:
        await send_message(data, 'No more bottles of beer on the wall, no more bottles of beer. Go to the store and buy some more, 99 bottles of beer on the wall!')
        beer.beercount = 100 # gets subtracted to 99
    elif beer.beercount == 1:
        await send_message(data, '1 bottle of beer on the wall, 1 bottle of beer! Take one down and pass it around, no more bottles of beer on the wall!')
    else:
        await send_message(data, f'{beer.beercount} bottles of beer on the wall, {beer.beercount} bottles of beer! Take one down and pass it around, {beer.beercount-1} bottles of beer on the wall!')
    beer.beercount -= 1
