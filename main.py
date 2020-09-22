import discord
import asyncio
import sqlite3
from database import *
import json
from dotenv import load_dotenv
import os
import time
from track_action import *
from datetime import date
from DBBackup import upload_to_aws

print("Main.py running")
ZEET_ENVIRONMENT = os.getenv('ZEET_ENVIRONMENT')

timeLastEdited = os.path.getmtime("/data/discord-commerce.db")

local_file = "/data/discord-commerce.db"
bucket_name = "matrixdatabasebackup"
s3_file_name = str(date.today())

uploaded = upload_to_aws('local_file', 'bucket_name', 's3_file_name')

if ZEET_ENVIRONMENT == "master":
    APIKEY = os.getenv('PROD_API_KEY')
else:
    APIKEY = os.getenv('TEST_API_KEY')
    

upload_to_aws(local_file, bucket_name, s3_file_name)
print(s3_file_name + " uploaded")
directory = os.listdir("/data")
print(directory)
print(timeLastEdited)

load_dotenv()
example_withdraw = "$withdraw eth_address token_name token_count"
example_balance_self = "$balance"
example_balance = "$balance @user"
example_send = "$send AMOUNT_OF_TOKENS TOKEN_NAME @USER"
example_drop = "$drop TOKEN_NAME AMOUNT_OF_TOKENS NUM_DROPS"
example_add_item = "$add_item SHOP_NAME ITEM_NAME QUANTITY_AVAILABLE COST TOKEN_NAME, after doing so react to the message you sent with the correct emoji for that item."
example_remove_item = "$remove_item SHOP_NAME ITEM_NAME"
example_create = "$create_token TOKEN_NAME"
example_shop = "$createshop SHOP_NAME"
example_poll_create = "$create_vote QUESTION TOKEN_NAME MINUTES_TILL_END"
example_code_create = "$create_code CODE TOKEN_AMOUNT TOKEN_NAME CODE_LIMIT"
example_code_remove = "$remove_code CODE"
example_add_admin = "$add_admin USER_ID"
example_remove_admin = "$remove_admin USER_ID"
DROP_EMOJI = "💰"
ADMIN_ID = 124016824202297344
APIKEY = os.getenv('PROD_API_KEY')

client = discord.Client()
codes = {}  #redeemable codes
drops = {}  #drops are stored in memory

try:
    shop = json.loads(open("/data/shop.json", "r").read())
except:
    shop = {"message_list": []}
    json.dump(shop, open("/data/shop.json", "w+"))
try:
    admins = json.loads(open("/data/admins.json", "r").read())
    admin_list = admins['admins']
except:
    admins = {"admins": []}
    admin_list = []
    json.dump(admins, open("/data/admins.json", "w+"))


#connect
@client.event
async def on_ready():
    print('logged in as: ', client.user.name, ' - ', client.user.id)


def get_shop_contents(shop_name):
    item_list = shop[shop_name]['items']
    sorted(item_list, key=lambda k: k['item_name'])
    message_content = "**" + str(shop_name).capitalize(
    ) + " Shop**" + "\n" + "*" + "React to purchase an item*" + "\n\n"
    for item in item_list:
        message_content += (
            "**Name**: " + item['item_name'] + ", **Price**: " + str(
                item['cost']) + ", **Token Type**: " + item['token_name'] +
            ", **Stock**: " + str(
                item['stock']) + ", **Icon**: " + item['icon'] + "\n")
    return message_content

#code redemption
@client.event
async def on_message(message):
    channel = message.channel
    author = str(message.author)
    unique_id = message.author.id
    try:
        if unique_id != client.user.id:
            if message.guild is None:
                code = message.content
                if code in codes and unique_id:
                    if unique_id not in codes[code]['user_list']:
                        if codes[code]['remaining'] >= 1:
                            codes[code]['user_list'].append(unique_id)
                            codes[code]['remaining'] -= 1
                            token_name = codes[code]['token_name']
                            set_balance(
                                unique_id, token_name,
                                get_balance(unique_id, token_name) +
                                codes[code]['token_count'])
                            #
                            #
                            #
                            #
                            set_profile(unique_id, token_name, code)
                            track_code(unique_id)
                            #
                            #
                            #
                            #
                            await channel.send("Code redeemed succesfully!")
                        else:
                            await channel.send(
                                "This code is no longer available.")
                    else:
                        await channel.send(
                            "You have already redeemed this code.")

        if unique_id != client.user.id:
            if message.content.lower().startswith("$help"):
                output_text = "**Help Menu**\n\n"
                output_text += "**$withdraw** - withdraw tokens to ETH address\nExample Usage: " + \
                    example_withdraw+"\n\n"
                output_text += "**$balance** - list balances for yourself\nExample Usage: " + \
                    example_balance_self+"\n\n"
                output_text += "**$balance** @User - list balances for other users\nExample Usage: " + \
                    example_balance+"\n\n"
                output_text += "**$send** - sends tokens to other users\nExample Usage: " + \
                    example_send+"\n\n"
                output_text += "If you need more help please visit https://discord.gg/matrix" 
                await channel.send(output_text)

            elif message.content.lower().startswith("$adminhelp"):
                adminoutput_text = "**Admin Help Menu**\n\n"
                adminoutput_text += "**$drop** - creates token drops, users who react with the correct emoji will receive tokens.[ADMIN ONLY]\nExample Usage: " + example_drop + "\n\n"
                adminoutput_text += "**$add_item** - adds new item to shop.[ADMIN ONLY]\nExample Usage: " + \
                    example_add_item+"\n\n"
                adminoutput_text += "**$remove_item** - removes item from shop.[ADMIN ONLY]\nExample Usage: " + \
                    example_remove_item+"\n\n"
                adminoutput_text += "**$create_token** - creates new token.[ADMIN ONLY]\nExample Usage: " + \
                    example_create+"\n\n"
                adminoutput_text += "**$createshop** - posts new shop and invalidates previous shop.[ADMIN ONLY]\nExample Usage: " + example_shop + "\n\n"
                adminoutput_text += "**$create_code** - Makes code. [ADMIN ONLY]\nExample Usage: " + \
                  example_code_create+"\n\n"
                adminoutput_text += "**$quietdrop** - No channel message drop. [ADMIN ONLY]"

                await channel.send(adminoutput_text)
                await channel.send(directory)

            elif message.content.lower().startswith("$withdraw"):

                params = message.content.split(" ")
                if len(params) != 4:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the withdraw command should look like this.\n"
                        + example_withdraw)
                else:
                    eth_address = params[1]
                    token_name = params[2]
                    token_count = int(params[3])
                    current_balance = get_balance(unique_id, token_name)
                    if current_balance is None:
                        await channel.send("Token not found.")
                    elif current_balance < token_count:
                        await channel.send(
                            "Not enough tokens to make the withdrawal.")
                    elif token_count < 0:
                        await channel.send(
                            "You cannot withdraw less than 0 tokens.")
                    else:
                        HQ_channel = client.get_channel(754155758194524181)
                        current_balance -= token_count
                        set_balance(unique_id, token_name, current_balance)
                        #
                        #
                        #
                        #
                        set_profile(unique_id, token_name, message.guild.name)
                        track_withdraw(unique_id)
                        #
                        #
                        #
                        #
                        await channel.send("Request being processed.")
                        await HQ_channel.send(
                            "<@" + str(unique_id) + "> has withdrawn " +
                            str(token_count) + " " + token_name +
                            " tokens to " + str(eth_address))

            elif message.content.lower() == "$balance":
                user_balance = get_balances(unique_id)
                balance_text = "**<@" + str(
                    message.author.id) + ">" + "'s balance:**\n\n"
                for token_name in user_balance:
                    if (int(user_balance[token_name]) != 0):
                        balance_text += ("**" + token_name + "**: " + str(
                            user_balance[token_name]) + "\n")
                #
                #
                #
                #
                set_profile(unique_id, token_name, message.guild.name)
                track_balance(unique_id)
                #
                #
                #
                #
                await channel.send("sending balance")
                await channel.send(balance_text)

            elif message.content.lower().startswith("$balance"):
                params = message.content.split(" ")

                if len(message.mentions) != 1:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the balance command should look like this.\n"
                        + example_balance)
                else:
                    other_user = str(message.mentions[0].name +
                                     message.mentions[0].discriminator)
                    other_id = message.mentions[0].id
                    user_balance = get_balances(other_id)
                    balance_text = "**<@" + str(
                        other_id) + ">" + "'s balance:**\n\n"
                    for token_name in user_balance:
                        if (int(user_balance[token_name]) != 0):
                            balance_text += ("**" + token_name + "**: " + str(
                                user_balance[token_name]) + "\n")
                    #
                    #
                    #
                    #
                    set_profile(unique_id, token_name, message.guild.name)
                    track_balance(unique_id)
                    #
                    #
                    #
                    # 
                    await channel.send(balance_text)

            elif message.content.lower().startswith("$send"):
                params = message.content.split(" ")
                if len(params) != 4 or len(message.mentions) != 1:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the send command should look like this.\n"
                        + example_send)
                else:
                    other_user = message.mentions[0].name + \
                        message.mentions[0].discriminator
                    other_id = message.mentions[0].id
                    token_count = int(params[1])
                    token_name = params[2].lower()
                    current_balance = get_balance(unique_id, token_name)
                    otherBalance = get_balances(other_id)
                    otherBalanceSpecificToken = int(otherBalance[token_name])
                    if current_balance < token_count:
                        await channel.send("Not enough tokens.")
                    elif token_count < 0:
                        await channel.send(
                            "You cannot send less than zero tokens.")
                    elif token_count > 10000:
                        await channel.send(
                            "You cannot send more than 10000 tokens."
                        )
                    elif otherBalanceSpecificToken > 25000:
                        await channel.send(
                            "You cannot send tokens to someone with more than 25,000 tokens! They must spend first."
                        )     
                    else:
                        set_balance(unique_id, token_name,
                                    current_balance - token_count)
                        set_balance(
                            other_id, token_name,
                            get_balance(other_id, token_name) + token_count)
                        #
                        #
                        #
                        #
                        set_profile(unique_id, token_name, message.guild.name)
                        track_send(unique_id)
                        #
                        #
                        #
                        #
                        await channel.send("Tokens sent succesfully.")

            elif message.content.lower().startswith(
                    "$drop") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 4:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the drop command should look like this.\n"
                        + example_drop)
                else:
                    token_name = params[1]
                    amount_tokens = int(params[2])
                    num_drops = int(params[3])
                    if amount_tokens < 0 or num_drops < 0:
                        await channel.send("Parameters cannot be less then 0.")
                    if amount_tokens > 1000:
                        await channel.send(
                            "You can't drop more than 1000 tokens!")
                    else:
                        user_list = []
                        m = await channel.send(
                            "The first " + str(num_drops) +
                            " people to react with the below reaction, will receive "
                            + str(amount_tokens) + " " + str(token_name) +
                            " tokens")
                        token_list = get_token_list()
                        track_channel = client.get_channel(754155758194524181)
                        author = str(message.author)
                        if m.id not in drops:
                            drops[m.id] = {
                                "token_name": token_name.lower(),
                                "num_tokens": amount_tokens,
                                "remaining": num_drops,
                                "user_list": [client.user.id]
                            }
                        
                        await m.add_reaction(DROP_EMOJI)
                        await track_channel.send(author + " has created a " + token_name + " drop with " + str(num_drops) + " uses. It drops " + str(amount_tokens) + " every time.")
            
            elif message.content.lower().startswith(
                    "$quietdrop") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 4:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the drop command should look like this.\n"
                        + example_drop)
                else:
                    token_name = params[1]
                    amount_tokens = int(params[2])
                    num_drops = int(params[3])
                    if amount_tokens < 0 or num_drops < 0:
                        await channel.send("Parameters cannot be less then 0.")
                    if amount_tokens > 1000:
                        await channel.send(
                            "You can't drop more than 1000 tokens!")
                    else:

                        user_list = []
                        m = await channel.send(
                            "The first " + str(num_drops) +
                            " people to react with the below reaction, will receive "
                            + str(amount_tokens) + " " + str(token_name) +
                            " tokens")

                        def check(reaction, user):
                            return user != m.author and str(
                                reaction.emoji
                            ) == DROP_EMOJI and reaction.message.id == m.id and user.id not in user_list

                        token_list = get_token_list()
                        await m.add_reaction(DROP_EMOJI)
                        while num_drops > 0:
                            reaction, user = await client.wait_for(
                                'reaction_add', check=check)
                            user_list.append(user.id)
                            num_drops -= 1
                            set_balance(
                                user.id, token_name,
                                get_balance(user.id, token_name) +
                                amount_tokens)
                            await user.send("You have obtained " +
                                            str(amount_tokens) + " tokens!")
                            print(num_drops)

            elif message.content.lower().startswith(
                    "$add_item") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 6:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the add item command should look like this.\n"
                        + example_add_item)
                else:
                    shop_name = params[1].lower()
                    item_name = params[2].lower()
                    quantity = int(params[3])
                    cost = int(params[4])
                    token_name = params[5].lower()

                    def check(reaction, user):
                        return user == message.author and reaction.message == message

                    try:
                        reaction, user = await client.wait_for(
                            'reaction_add', timeout=60.0, check=check)
                        if shop_name == "message_list":
                            await channel.send(
                                "Reserved keyword used for shop name.")
                        else:
                            if shop_name not in shop:
                                shop[shop_name] = {
                                    "items": [],
                                    "message_id": None
                                }
                            shop[shop_name]['items'].append({
                                "item_name":
                                item_name,
                                "cost":
                                cost,
                                "stock":
                                quantity,
                                "token_name":
                                token_name,
                                "icon":
                                str(reaction)
                            })
                            json.dump(shop, open("/data/shop.json", "w+"))
                            await channel.send(
                                "Item added, please re-run the $createshop command to refresh"
                            )
                    except asyncio.TimeoutError:
                        await channel.send(
                            "Item not added succesfully, icon not specified in time."
                        )

            elif message.content.lower().startswith(
                    "$remove_item") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 3:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the remove item command should look like this.\n"
                        + example_remove_item)
                else:
                    shop_name = params[1].lower()
                    item_name = params[2].lower()
                    if shop_name not in shop:
                        await channel.send("Shop not found.")
                    else:
                        for item_num in range(len(shop[shop_name]['items'])):
                            if shop[shop_name]['items'][item_num][
                                    'item_name'].lower() == item_name.lower():
                                shop[shop_name]['items'].pop(item_num)
                        json.dump(shop, open("/data/shop.json", "w+"))
                        await channel.send(
                            "Item removed, please re-run the $createshop command to refresh"
                        )

            elif message.content.lower().startswith(
                    "$create_token") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 2:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the add item command should look like this.\n"
                        + example_create)
                else:
                    token_name = params[1]
                    add_token(token_name)
                    await channel.send("Token created succesfully.")

            elif message.content.lower().startswith(
                    "$createshop") and unique_id in admin_list:

                params = message.content.split(" ")
                if len(params) != 2:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the add item command should look like this.\n"
                        + example_shop)
                else:
                    shop_name = params[1].lower()
                    if shop_name not in shop:
                        await channel.send("Shop not found.")
                    else:
                        item_list = shop[shop_name]['items']
                        sorted(item_list, key=lambda k: k['item_name'])
                        message_content = "**" + str(shop_name).capitalize(
                        ) + " Shop**" + "\n" + "*" + "React to purchase an item*" + "\n\n"
                        for item in item_list:
                            message_content += (
                                "**Name**: " + item['item_name'] +
                                ", **Price**: " + str(item['cost']) +
                                ", **Token Type**: " + item['token_name'] +
                                ", **Icon**: " + item['icon'] + "\n")
                        new_message = await channel.send(message_content)
                        previous_id = shop[shop_name]['message_id']
                        if previous_id != "None" and previous_id in shop[
                                'message_list']:
                            shop['message_list'].pop(
                                shop['message_list'].index(previous_id))
                            old_msg = await channel.fetch_message(previous_id)
                            await old_msg.delete()
                        shop[shop_name]['message_id'] = new_message.id
                        shop['message_list'].append(new_message.id)
                        json.dump(shop, open("/data/shop.json", "w+"))

            elif message.content.lower().startswith(
                    "$create_vote") and unique_id in admin_list:
                params = message.content.split('-')
                if len(params) != 4:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the create_poll command should look like this.\n"
                        + example_poll_create)
                else:
                    question = params[1]
                    token_name = params[2].lower()
                    minutes_till_end = int(params[3])
                    affirmative = 0
                    negative = 0
                    poll = await channel.send("**Poll: " + question + "**" +
                                              "\n" + "👍: " + str(affirmative) +
                                              "\n\n" + "👎:" + str(negative))
                    await poll.add_reaction("👍")
                    await poll.add_reaction("👎")
                    start_time = time.time()
                    end_time = start_time + (minutes_till_end * 60)
                    temp_user_list = []
                    while time.time() < end_time:

                        def check(reaction, user):
                            return user != poll.author and reaction.message.id == poll.id and user.id not in temp_user_list

                        try:
                            reaction, user = await client.wait_for(
                                'reaction_add',
                                timeout=end_time - time.time(),
                                check=check)
                            temp_user_list.append(user.id)
                            balance = get_balance(user.id, token_name)
                            if (str(reaction) == "👍"):
                                affirmative += balance
                            elif (str(reaction) == "👎"):
                                negative += balance
                            await poll.edit(
                                content="**Poll: " + question + "**" + "\n" +
                                "👍: " + str(affirmative) + "\n\n" + "👎:" +
                                str(negative))
                        except asyncio.TimeoutError:
                            pass

                    if affirmative > negative:
                        await poll.edit(content="**Poll: " + question + "**" +
                                        "\nWinner is 👍 with " +
                                        str(affirmative) + " tokens")
                    elif negative > affirmative:
                        await poll.edit(
                            content="**Poll: " + question + "**" +
                            "\nWinner is  👎 with " + str(negative) + " tokens")
                    else:
                        await poll.edit(
                            content="**Poll: " + question + "**" +
                            "\nIt's a tie with " + str(affirmative) + " tokens"
                        )

            elif message.content.lower().startswith(
                    "$create_code") and unique_id in admin_list:
                params = message.content.split(" ")
                
                if len(params) != 5:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the create_code command should look like this.\n"
                        + example_code_create)
                else:
                    author = str(message.author)
                    track_channel = client.get_channel(754155758194524181)
                    code_creator = client.get_user(message.author.id)
                    code = params[1]
                    token_amount = int(params[2])
                    token_name = params[3].lower()
                    max_use = int(params[4])
                    codes[code] = {
                        "remaining": max_use,
                        "user_list": [],
                        "token_name": token_name,
                        "token_count": token_amount
                    }
                    await track_channel.send(author + " has created a " + token_name + " code with " + str(max_use) + " uses. It drops " + str(token_amount) + " every time.")

                    await channel.send("Code created.")
                
                    
          
            elif message.content.lower().startswith("$godsend") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 4 or len(message.mentions) != 1:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the send command should look like this.\n"
                        + example_send)
                else:
                    other_user = message.mentions[0].name + \
                        message.mentions[0].discriminator
                    other_id = message.mentions[0].id
                    token_count = int(params[1])
                    token_name = params[2].lower()
                    current_balance = get_balance(unique_id, token_name)
                    otherBalance = get_balances(other_id)
                    otherBalanceSpecificToken = int(otherBalance[token_name])
                    set_balance(unique_id, token_name,
                                    current_balance - token_count)
                    set_balance(other_id, token_name,
                            get_balance(other_id, token_name) + token_count)
                    await channel.send("God powers successful.")
           
            elif message.content.lower().startswith(
                    "$remove_code") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 2:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the create_code command should look like this.\n"
                        + example_code_remove)
                else:
                    code = params[1]
                    if code in codes:
                        del (codes[code])
                        await channel.send("Code removed.")
                    else:
                        await channel.send("Code not found.")

            elif message.content.lower().startswith(
                    "$add_admin") and unique_id in admin_list:
                params = message.content.split(" ")
                mentions = message.mentions
                if len(mentions) != 1:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the add_admin command should look like this.\n"
                        + example_add_admin)
                else:
                    admin_id = mentions[0].id
                    if admin_id in admin_list:
                        await channel.send("Admin already in system.")
                    else:
                        admin_list.append(int(admin_id))
                        admins['admins'] = admin_list
                        await channel.send("Admin added.")
                        json.dump(admins, open("/data/admins.json", "w+"))

            elif message.content.lower().startswith(
                    "$remove_admin") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 2:
                    await channel.send(
                        "Error, parameters missing or extra parameters found, the remove_admin command should look like this.\n"
                        + example_remove_admin)
                else:
                    admin_id = int(params[1])
                    if admin_id in admin_list:
                        admin_list.pop(admin_list.index(admin_id))
                        await channel.send("Admin removed.")
                        admins['admins'] = admin_list
                        json.dump(admins, open("/data/admins.json", "w+"))
                    else:
                        await channel.send("Admin not found in system.")

    except Exception as e:
        print("Possible error or incorrect parameter order")
        print(e)
        await channel.send(
            "An error occured, please use the $help command to see example usage of each command."
        )


@client.event
#Drop handling
async def on_raw_reaction_add(payload):
    HQ_channel = client.get_channel(754155758194524181)
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    reaction_message_id=message.id
    if (reaction_message_id in drops):
        user = await client.fetch_user(payload.user_id)
        unique_id = user.id
        emoji = str(payload.emoji)
        if drops[reaction_message_id]['remaining']>0 and user.id not in drops[reaction_message_id]['user_list'] and emoji==DROP_EMOJI:
            drops[reaction_message_id]['user_list'].append(user.id)
            token_name=drops[reaction_message_id]['token_name']
            amount_tokens=drops[reaction_message_id]['num_tokens']
            set_balance(user.id, token_name, get_balance(
            user.id, token_name)+amount_tokens)
            drops[reaction_message_id]['remaining']-=1
            #
            #
            #
            set_profile(unique_id, token_name, message.guild.name)
            track_drop(unique_id)
            #
            #
            #
            #
            await user.send("You have obtained " + str(amount_tokens) + " tokens!")
            if drops[reaction_message_id]['remaining']==0:
                del(drops[reaction_message_id])

    elif (reaction_message_id in shop["message_list"]):
        user = await client.fetch_user(payload.user_id)
        unique_id = user.id
        emoji = str(payload.emoji)
        shop_name=None
        track_buy(unique_id)
        for s in shop:
            if s != "message_list" and shop[s]['message_id'] == reaction_message_id:
                shop_name=s
                break
        if shop_name is not None:
            for item in shop[shop_name]['items']:
                if item['icon'] == emoji:
                    user_balance = get_balance(unique_id, item['token_name'])
                    if user_balance < int(item['cost']):
                        await user.send("<@"+str(user.id) + ">, you cannot afford that item.")
                    else:
                        item['stock']-=1
                        if (item['stock']==0):
                            shop[shop_name]['items'].pop(shop[shop_name]['items'].index(item))
                        json.dump(shop,open("/data/shop.json","w+"))
                        await user.send("<@"+str(user.id) + ">, purchase is being processed. Your purchase has been sent to the admins.")
                        set_balance(
                            unique_id, item['token_name'], user_balance-int(item['cost']))
                        admin_user = client.get_user(ADMIN_ID)
                        shop_message=await channel.fetch_message(shop[shop_name]['message_id'])
                        await shop_message.edit(content=get_shop_contents(shop_name))
                        await HQ_channel.send("<@"+str(user.id) + "> has purchased " + item['item_name'] + " from " + shop_name)
                    break


            
if __name__ == '__main__':
    client.run(APIKEY)