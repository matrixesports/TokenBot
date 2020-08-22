from mixpanel import Mixpanel
import discord
from database import *

mp = Mixpanel('6e8340ea62ff79b774da5fdbdcad0b2d')

#Tracks an event, 'makes Transaction'
def set_profile(unique_id, token_name, client):
    mp.people_set(unique_id, {
        'balance' : get_balance(unique_id, token_name),
        'server' : client.get_guild(discord.Guild.id)
    })

def track_code(unique_id):
    mp.track(unique_id, 'code')

def track_withdraw(unique_id):
    mp.track(unique_id, 'withdraw')

def track_send(unique_id):
    mp.track(unique_id, 'send')

def track_drop(unique_id):
    mp.track(unique_id, 'drop')
