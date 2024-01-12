#Tg:MaheshChauhan/DroneBots
#Github.com/Vasusen-code

"""
Plugin for both public & private channels!
"""

import time, os, asyncio
import random  # Import the random module

from .. import bot as Drone
from .. import userbot, Bot, AUTH
from .. import FORCESUB as fs
from main.plugins.pyroplug import get_bulk_msg
from main.plugins.helpers import get_link, screenshot

from telethon import events, Button, errors
from telethon.tl.types import DocumentAttributeVideo

from pyrogram import Client 
from pyrogram.errors import FloodWait

from ethon.pyfunc import video_metadata
from ethon.telefunc import force_sub

ft = f"To use this bot you've to join @{fs}."

batch = []

@Drone.on(events.NewMessage(incoming=True, from_users=AUTH, pattern='/cancel'))
async def cancel(event):
    if not event.sender_id in batch:
        return await event.reply("No batch active.")
    batch.clear()
    await event.reply("Done.")
    
@Drone.on(events.NewMessage(incoming=True, from_users=AUTH, pattern='/batch'))
async def _batch(event):
    if not event.is_private:
        return
    s, r = await force_sub(event.client, fs, event.sender_id, ft) 
    if s == True:
        await event.reply(r)
        return       
    if event.sender_id in batch:
        return await event.reply("You've already started one batch, wait for it to complete you dumbfuck owner!")
    async with Drone.conversation(event.chat_id) as conv: 
        if s != True:
            await conv.send_message("Send me the message link you want to start saving from, as a reply to this message.", buttons=Button.force_reply())
            try:
                link = await conv.get_reply()
                try:
                    _link = get_link(link.text)
                except Exception:
                    await conv.send_message("No link found.")
                    return conv.cancel()
            except Exception as e:
                print(e)
                await conv.send_message("Cannot wait more longer for your response!")
                return conv.cancel()
            await conv.send_message("Send me the number of files/range you want to save from the given message, as a reply to this message.", buttons=Button.force_reply())
            try:
                _range = await conv.get_reply()
            except Exception as e:
                print(e)
                await conv.send_message("Cannot wait more longer for your response!")
                return conv.cancel()
            try:
                value = int(_range.text)
                if value > 10000:
                    await conv.send_message("You can only get upto 100 files in a single batch.")
                    return conv.cancel()
            except ValueError:
                await conv.send_message("Range must be an integer!")
                return conv.cancel()
            batch.append(event.sender_id)
            await run_batch(userbot, Bot, event.sender_id, _link, value) 
            conv.cancel()
            batch.clear()

async def run_batch(userbot, client, sender, link, _range):
    for i in range(_range):
        timer = 60
        if i < 25:
            timer = random.uniform(2, 10)  # Random delay between 2 and 15 seconds
        if i < 100 and i > 25:
            timer = random.uniform(5, 15)  # Random delay between 10 and 30 seconds
        if i < 200 and i > 100:
            timer = random.uniform(25, 35) # Random delay between 30 and 60 seconds
        if i < 300 and i > 200:
            timer = random.uniform(10, 20)
        if i < 400 and i > 300:
            timer = random.uniform(30, 45)
        if i < 500 and i > 400:
            timer = random.uniform(22, 28)
        if i < 600 and i > 500:
            timer = random.uniform(2, 10)
        if i < 700 and i > 600:
            timer = random.uniform(25, 40)
        if i < 800 and i > 700:
            timer = random.uniform(15, 20)
        if i < 900 and i > 800:
            timer = random.uniform(45, 60)
        if i < 1000 and i > 900:
            timer = random.uniform(5, 12)
        if i > 1000:
            timer = random.uniform(2, 60)
        if not 't.me/c/' in link:
            if i < 25:
                timer = 2
            else:
                timer = 3
        try: 
            if not sender in batch:
                await client.send_message(sender, "Batch completed.")
                break
        except Exception as e:
            print(e)
            await client.send_message(sender, "Batch completed.")
            break
        try:
            await get_bulk_msg(userbot, client, sender, link, i) 
        except FloodWait as fw:
            if int(fw.value) > 14400:
                await client.send_message(sender, "Cancelling batch since you have floodwait more than 5 minutes.")
                break
            await asyncio.sleep(fw.value + random.uniform(5, 60))  # Random delay after FloodWait
            await get_bulk_msg(userbot, client, sender, link, i)
        protection = await client.send_message(sender, f"Sleeping for `{timer:.2f}` seconds to avoid Floodwaits and Protect account!")
        await asyncio.sleep(timer)
        await protection.delete()
        
            
