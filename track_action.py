from mixpanel import Mixpanel
from database import *
import discord

mp = Mixpanel('6e8340ea62ff79b774da5fdbdcad0b2d')

#Tracks an event, 'makes Transaction'
def set_profile(unique_id, token_name, server_name):
    mp.people_set(unique_id, {
        'balance' : get_balance(unique_id, token_name),
        'server' : server_name
    })

def track_code(unique_id, token_name, code):
    mp.track(unique_id, 'code', {
        'token' : token_name,
        'code': code
    })


def track_withdraw(unique_id):
    mp.track(unique_id, 'withdraw')

def track_send(unique_id):
    mp.track(unique_id, 'send')

def track_drop(unique_id):
    mp.track(unique_id, 'drop')

def track_balance(unique_id):
    mp.track(unique_id, 'balance')

def track_buy(unique_id):
    mp.track(unique_id, 'buy')