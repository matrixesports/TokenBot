import discord
import asyncio
import sqlite3
from database import *
import json
from dotenv import load_dotenv
import os



load_dotenv()
admin_list = [124016824202297344], 485386050512879617,  
480679155609108501, 
667098393251938364, 
450768015496183830, 
431989145842483200, 
351957872646684672,  
557388612971397130, 
639132617907896340]
example_withdraw = "$withdraw eth_address token_name token_count"
example_balance_self = "$balance"
example_balance = "$balance @user"
example_send = "$send AMOUNT_OF_TOKENS TOKEN_NAME @USER"
example_drop = "$drop TOKEN_NAME AMOUNT_OF_TOKENS NUM_DROPS"
example_add_item = "$add_item SHOP_NAME ITEM_NAME COST TOKEN_NAME, after doing so react to the message you sent with the correct emoji for that item."
example_remove_item = "$remove_item SHOP_NAME ITEM_NAME"
example_create = "$create_token TOKEN_NAME"
example_shop = "$createshop SHOP_NAME"
DROP_EMOJI = "💰"
ADMIN_ID = 124016824202297344
APIKEY = os.getenv('API_KEY')

client = discord.Client()



try:
    shop = json.loads(open("shop.json", "r").read())
except:
    shop = {"message_list": []}
    json.dump(shop, open("shop.json", "w+"))


@client.event
async def on_ready():
    print('logged in as: ', client.user.name, ' - ', client.user.id)


@client.event
async def on_message(message):
    channel = message.channel
    author = str(message.author)
    unique_id = message.author.id
    try:
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
                output_text += "For additional help, join discord.gg/matrix \n\n"     
                
                #output_text += "**$drop** - creates token drops, users who react with the correct emoji will receive tokens.[ADMIN ONLY]\nExample Usage: " + example_drop+"\n\n"
                #output_text += "**$add_item** - adds new item to shop.[ADMIN ONLY]\nExample Usage: " + \
                    #example_add_item+"\n\n"
                #output_text += "**$remove_item** - removes item from shop.[ADMIN ONLY]\nExample Usage: " + \
                    #example_remove_item+"\n\n"
                #output_text += "**$create_token** - creates new token.[ADMIN ONLY]\nExample Usage: " + \
                    #example_create+"\n\n"
                #output_text += "**$createshop** - posts new shop and invalidates previous shop.[ADMIN ONLY]\nExample Usage: " + example_shop+"\n\n"
                
                await channel.send(output_text)

            elif message.content.lower().startswith("$withdraw"):
              
                params = message.content.split(" ")
                if len(params) != 4:
                    await channel.send("Error, parameters missing or extra parameters found, the withdraw command should look like this.\n" + example_withdraw)
                else:
                    eth_address = params[1]
                    token_name = params[2]
                    token_count = int(params[3])
                    current_balance = get_balance(unique_id, token_name)
                    if current_balance is None:
                        await channel.send("Token not found.")
                    elif current_balance < token_count:
                        await channel.send("Not enough tokens to make the withdrawal.")
                    elif token_count < 0:
                        await channel.send("You cannot withdraw less than 0 tokens.")
                    else:
                        HQ_channel = client.get_channel(732435051224236043)
                        current_balance -= token_count
                        set_balance(unique_id, token_name, current_balance)
                        await channel.send("Request being processed.")
                        admin_user = client.get_user(ADMIN_ID)
                        await HQ_channel.send("<@"+str(unique_id) + "> has withdrawn " + str(token_count) + " " + token_name + " tokens to " + str(eth_address))

            elif message.content.lower() == "$balance":
                user_balance = get_balances(unique_id)
                balance_text = "**<@"+str(message.author.id) + ">" +"'s balance:**\n\n"
                for token_name in user_balance:
                    if (int(user_balance[token_name]) != 0):
                        balance_text += ("**"+token_name+"**: " +
                                         str(user_balance[token_name])+"\n")
                await channel.send(balance_text)

            elif message.content.lower().startswith("$balance"):
                params = message.content.split(" ")

                if len(message.mentions) != 1:
                    await channel.send("Error, parameters missing or extra parameters found, the balance command should look like this.\n" + example_balance)
                else:
                    other_user = str(
                        message.mentions[0].name+message.mentions[0].discriminator)
                    other_id = message.mentions[0].id
                    user_balance = get_balances(other_id)
                    balance_text = "**<@"+str(other_id) + ">"+"'s balance:**\n\n"
                    for token_name in user_balance:
                        if (int(user_balance[token_name]) != 0):
                            balance_text += ("**"+token_name+"**: " +
                                             str(user_balance[token_name])+"\n")
                    await channel.send(balance_text)

            elif message.content.lower().startswith("$send"):
                params = message.content.split(" ")
                if len(params) != 4 or len(message.mentions) != 1:
                    await channel.send("Error, parameters missing or extra parameters found, the send command should look like this.\n" + example_send)
                else:
                    other_user = message.mentions[0].name + \
                        message.mentions[0].discriminator
                    other_id = message.mentions[0].id
                    token_count = int(params[1])
                    token_name = params[2]
                    current_balance = get_balance(unique_id, token_name)
                    if current_balance < token_count:
                        await channel.send("Not enough tokens.")
                    elif token_count < 0:
                        await channel.send("You cannot send less than zero tokens.")
                    else:
                        set_balance(unique_id, token_name,
                                    current_balance-token_count)
                        set_balance(other_id, token_name, get_balance(
                            other_id, token_name)+token_count)
                        await channel.send("Tokens sent succesfully.")

            elif message.content.lower().startswith("$drop") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 4:
                    await channel.send("Error, parameters missing or extra parameters found, the drop command should look like this.\n" + example_drop)
                else:
                    token_name = params[1]
                    amount_tokens = int(params[2])
                    num_drops = int(params[3])
                    if amount_tokens < 0 or num_drops < 0:
                        await channel.send("Parameters cannot be less then 0.")
                    else:

                        user_list = []
                        m = await channel.send("The first " + str(num_drops) + " people to react with the below reaction, will receive " + str(amount_tokens) + " " + str(token_name) + " tokens")

                        def check(reaction, user):
                            return user != m.author and str(reaction.emoji) == DROP_EMOJI and reaction.message.id == m.id and user.id not in user_list
                        token_list = get_token_list()
                        await m.add_reaction(DROP_EMOJI)
                        while num_drops > 0:
                            reaction, user = await client.wait_for('reaction_add', check=check)
                            user_list.append(user.id)
                            num_drops -= 1
                            set_balance(user.id, token_name, get_balance(
                                user.id, token_name)+amount_tokens)
                            await channel.send("<@"+str(user.id) + "> " +  "has obtained " + str(amount_tokens) + " tokens! There are " + str(num_drops) + " remaining!")    
                            print(num_drops)

            elif message.content.lower().startswith("$add_item") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 5:
                    await channel.send("Error, parameters missing or extra parameters found, the add item command should look like this.\n" + example_add_item)
                else:
                    shop_name = params[1].lower()
                    item_name = params[2].lower()
                    cost = int(params[3])
                    token_name = params[4].lower()

                    def check(reaction, user):
                        return user == message.author and reaction.message == message
                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                        if shop_name == "message_list":
                            await channel.send("Reserved keyword used for shop name.")
                        else:
                            if shop_name not in shop:
                                shop[shop_name] = {
                                    "items": [], "message_id": None}
                            shop[shop_name]['items'].append(
                                {"item_name": item_name, "cost": cost, "token_name": token_name, "icon": str(reaction)})
                            json.dump(shop, open("shop.json", "w+"))
                            await channel.send("Item added, please re-run the $createshop command to refresh")
                    except asyncio.TimeoutError:
                        await channel.send("Item not added succesfully, icon not specified in time.")

            elif message.content.lower().startswith("$remove_item") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 3: 
                    await channel.send("Error, parameters missing or extra parameters found, the remove item command should look like this.\n" + example_remove_item)
                else:
                    shop_name = params[1].lower()
                    item_name = params[2].lower()
                    if shop_name not in shop:
                        await channel.send("Shop not found.")
                    else:
                        for item_num in range(len(shop['items'])):
                            if shop[shop_name]['items'][item_num]['item_name'].lower() == item_name.lower():
                                shop[shop_name]['items'].pop(item_num)
                        json.dump(shop, open("shop.json", "w+"))
                        await channel.send("Item removed, please re-run the $createshop command to refresh")

            elif message.content.lower().startswith("$create_token") and unique_id in admin_list:
                params = message.content.split(" ")
                if len(params) != 2:
                    await channel.send("Error, parameters missing or extra parameters found, the add item command should look like this.\n" + example_create)
                else:
                    token_name = params[1]
                    add_token(token_name)
                    await channel.send("Token created succesfully.")

            elif message.content.lower().startswith("$createshop") and unique_id in admin_list:

                params = message.content.split(" ")
                if len(params) != 2:
                    await channel.send("Error, parameters missing or extra parameters found, the add item command should look like this.\n" + example_shop)
                else:
                    shop_name = params[1].lower()
                    if shop_name not in shop:
                        await channel.send("Shop not found.")
                    else:
                        item_list = shop[shop_name]['items']
                        sorted(item_list, key=lambda k: k['item_name'])
                        message_content = "**"+str(shop_name).capitalize(
                        ) + " Shop**" + "\n" + "*"+"React to purchase an item*" +"\n\n"
                        for item in item_list:
                            message_content += ("**Name**: " + item['item_name'] + ", **Price**: " + str(
                                item['cost']) + ", **Token Type**: " + item['token_name']+", **Icon**: " + item['icon'] + "\n")
                        new_message = await channel.send(message_content)
                        previous_id = shop[shop_name]['message_id']
                        if previous_id !="None" and previous_id in shop['message_list']:
                            shop['message_list'].pop(
                                shop['message_list'].index(previous_id))
                            old_msg=await channel.fetch_message(previous_id)
                            await old_msg.delete()
                        shop[shop_name]['message_id'] = new_message.id
                        shop['message_list'].append(new_message.id)
                        json.dump(shop, open("shop.json", "w+")) 


    except Exception as e:
        print("Possible error or incorrect parameter order")
        print(e)
        await channel.send("An error occured, please use the $help command to see example usage of each command.")


@client.event
async def on_raw_reaction_add(payload):
    HQ_channel = client.get_channel(732435051224236043)
    channel=client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    reaction_message_id=message.id
    if (reaction_message_id in shop["message_list"]):
        user = await client.fetch_user(payload.user_id)
        unique_id = user.id
        emoji = str(payload.emoji)
        shop_name=None
        for s in shop:
            if s != "message_list" and shop[s]['message_id'] == reaction_message_id:
                shop_name=s
                break
        if shop_name is not None:
            for item in shop[shop_name]['items']:
                if item['icon'] == emoji:
                    user_balance = get_balance(unique_id, item['token_name'])
                    if user_balance < int(item['cost']):
                        await channel.send("<@"+str(user.id) + ">, you cannot afford that item.")
                    else:
                        await channel.send("<@"+str(user.id) + ">, purchase is being processed. Your purchase has been sent to the admins.")
                        set_balance(
                            unique_id, item['token_name'], user_balance-int(item['cost']))
                        admin_user = client.get_user(ADMIN_ID)
                        await HQ_channel.send("<@"+str(user.id) + "> has purchased " + item['item_name'] + " from " + shop_name)
                    break

if __name__ == '__main__':
    client.run(APIKEY)
