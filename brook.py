import json
from typing import Union
from discord import Client, TextChannel, User
from discord.enums import ChannelType
from discord.ext import commands

pending_requests = {}

def is_error_status(status_code):
    return 400 <= status_code <= 599

class Brook:
    def __init__(self, transport_channel: TextChannel, client: Client):
        self.transport_channel = transport_channel
        self.client = client

    async def on_message(self, msg):
        if msg.channel.id != self.transport_channel.id:
            return
        if msg.author.id != 1183134058415394846:
            return
        if not msg.reference or not msg.reference.message_id:
            return

        json_content = json.loads(msg.content)
        request = pending_requests.get(msg.reference.message_id)
        if request:
            if not json_content.get('body'):
                return

            if is_error_status(json_content['status']):
                del pending_requests[msg.reference.message_id]
                request['reject'](Exception(f"Status {json_content['status']}. {json_content['body']}"))
            else:
                print('request type:', request['request_type'])
                if request['request_type'] == 'payrequest':
                    if json_content['body']['type'] == 'accepted':
                        del pending_requests[msg.reference.message_id]
                        request['resolve'](json_content)
                    elif json_content['body']['type'] == 'declined':
                        del pending_requests[msg.reference.message_id]
                        request['reject'](Exception('Payment declined'))
                    else:
                        return  # ignore others
                else:
                    del pending_requests[msg.reference.message_id]
                    request['resolve'](json_content)


    async def request_payment(self, user: User, amount: int, request_channel: ChannelType, description: str):
        message = await self.transport_channel.send(f"1183134058415394846!api payrequest {user.id} {amount} {request_channel.id} {description}")
        return self._create_promise(message.id, 'payrequest')
    async def pay(self, target: Union[User, str], amount: int, receipt_channel: ChannelType):
        target_id = target if isinstance(target, str) else target.id
        message = await self.transport_channel.send(f"1183134058415394846!api pay {target_id} {amount} {receipt_channel.id}")
        return self._create_promise(message.id, 'pay')

    async def balance(self, target: Union[User, str]):
        target_id = target if isinstance(target, str) else target.id
        message = await self.transport_channel.send(f"1183134058415394846!api balance {target_id}")
        return self._create_promise(message.id, 'balance')

    def _create_promise(self, message_id, request_type):
        future = self.client.loop.create_future()
        pending_requests[message_id] = {
            'resolve': future.set_result,
            'reject': future.set_exception,
            'request_type': request_type
        }
        return future
