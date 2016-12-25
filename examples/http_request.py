# -*- coding: utf-8 -*-
import pook
import requests
from riprova import retry

# Define HTTP mocks
pook.get('server.com').times(3).reply(503)
pook.get('server.com').times(1).reply(200).json({'hello': 'world'})


# Retry evaluator function used to determine if the operated failed or not
def evaluator(response):
    if response != 200:
        return Exception('failed request')
    return False


# On retry even subcriptor
def on_retry(err, next_try):
    print('Operation error {}'.format(err))
    print('Next try in {}ms'.format(next_try))


# Register retriable operation
@retry(evaluator=evaluator, on_retry=on_retry)
def fetch(url):
    return requests.get(url)


# Run request
fetch('http://server.com')
