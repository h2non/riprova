# -*- coding: utf-8 -*-
# flake8: noqa
"""
Note: only Python 3.5+ compatible.
"""
import pook
import paco
import aiohttp
from riprova import retry

# Define HTTP mocks to simulate failed scenarios
pook.get('server.com').times(4).reply(503)
pook.get('server.com').times(1).reply(200).json({'hello': 'world'})


# Retry evaluator function used to determine if the operated failed or not
async def evaluator(status):
    if status != 200:
        return Exception('failed request with status {}'.format(status))
    return False


# On retry even subcriptor
async def on_retry(err, next_try):
    print('Operation error: {}'.format(err))
    print('Next try in {}ms'.format(next_try))


# Register retriable operation with custom evaluator
@retry(evaluator=evaluator, on_retry=on_retry)
async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return response.status


# Run request
status = paco.run(fetch('http://server.com'))
print('Response status:', status)
