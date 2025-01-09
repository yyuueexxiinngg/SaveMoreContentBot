import time, os
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, PeerIdInvalid
from pyrogram.enums import MessageMediaType
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from ethon.pyfunc import video_metadata
from ethon.telefunc import fast_upload
from telethon.tl.types import DocumentAttributeVideo
from .. import bot as Drone
from main.plugins.progress import progress_for_pyrogram
from main.plugins.helpers import screenshot

def thumbnail(sender):
    return f'{sender}.jpg' if os.path.exists(f'{sender}.jpg') else None

MEDIA_GROUP = []
FILES = []
THUMB_PATHS= []

async def get_msg(userbot, client, bot, sender, edit_id, msg_link, i, _range=-1):
    if _range and i == 0:
        MEDIA_GROUP.clear()

    edit, chat, round_message = "", "", False
    msg_link = msg_link.split("?single")[0] if "?single" in msg_link else msg_link
    msg_id = int(msg_link.split("/")[-1]) + int(i)
    height, width, duration, thumb_path = 90, 90, 0, None

    if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
        chat = str(msg_link.split("/")[-2]) if 't.me/b/' in msg_link else int('-100' + str(msg_link.split("/")[-2]))
        try:
            msg = await userbot.get_messages(chat, msg_id)
            if msg.media:
                if msg.media == MessageMediaType.WEB_PAGE:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown)
                    await edit.delete()
                    return
            if not msg.media and msg.text:
                edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                await client.send_message(sender, msg.text.markdown)
                await edit.delete()
                return

            edit = await client.edit_message_text(sender, edit_id, "Trying to Download " + str(i+1) + " !")
            file = await userbot.download_media(msg, progress=progress_for_pyrogram, progress_args=(client, "**DOWNLOADING:**\n", edit, time.time()))
            print(file)
            await edit.edit('Preparing to Upload' +  str(i+1)  + ' !')
            caption = msg.caption if msg.caption else None

            if msg.media == MessageMediaType.VIDEO_NOTE:
                round_message = True
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                thumb_path = await screenshot(file, duration, sender) or None
                await client.send_video_note(sender, file, length=height, duration=duration, thumb=thumb_path, progress=progress_for_pyrogram, progress_args=(client, '**UPLOADING:**\n', edit, time.time()))
            elif msg.media == MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                print("Video")
                data = video_metadata(file)
                print(data)
                height, width, duration = data["height"], data["width"], data["duration"]
                thumb_path = await screenshot(file, duration, sender) or None
                if thumb_path:
                    THUMB_PATHS.append(thumb_path)

                if os.path.isfile(file):
                    print(f"File Exists: {file}")
                print(_range)
                if _range > 1:
                    MEDIA_GROUP.append(
                        InputMediaVideo(file, caption=caption, supports_streaming=True, height=height, width=width,duration=duration, thumb=thumb_path)
                    )
                    FILES.append(file)
                else:
                    print("Sending Video")
                    await client.send_video(sender, file, caption=caption, supports_streaming=True, height=height, width=width, duration=duration, thumb=thumb_path, progress=progress_for_pyrogram, progress_args=(client, '**UPLOADING:**\n', edit, time.time()))
                    print("Sent Video")
            elif msg.media == MessageMediaType.PHOTO:
                # await bot.send_file(sender, file, caption=caption)
                if _range > 1:
                    MEDIA_GROUP.append(InputMediaPhoto(file, caption=caption))
                    FILES.append(file)
                else:
                    await bot.send_file(sender, file, caption=caption)
            else:
                thumb_path = thumbnail(sender)
                if thumb_path:
                    THUMB_PATHS.append(thumb_path)
                if _range > 1:
                    MEDIA_GROUP.append(InputMediaDocument(file, caption=caption, thumb=thumb_path))
                    FILES.append(file)
                else:
                    await client.send_document(sender, file, caption=caption, thumb=thumb_path, progress=progress_for_pyrogram, progress_args=(client, '**UPLOADING:**\n', edit, time.time()))

            if not _range > 1:
                os.remove(file) if os.path.isfile(file) else None
                os.remove(thumb_path) if os.path.isfile(thumb_path) else None
            await edit.delete()

            if len(MEDIA_GROUP) == 10 or i == _range - 1:
                if len(MEDIA_GROUP) > 1:
                    await client.send_media_group(sender, MEDIA_GROUP)
                else:
                    _media = MEDIA_GROUP[0]
                    if isinstance(_media, InputMediaPhoto):
                        await client.send_photo(sender, _media.media, caption=_media.caption)
                    elif isinstance(_media, InputMediaDocument):
                        await client.send_document(sender, _media.media, caption=_media.caption, thumb=_media.thumb)
                    elif isinstance(_media, InputMediaVideo):
                        await client.send_video(sender, _media.media, caption=_media.caption, thumb=_media.thumb, duration=_media.duration, width=_media.width, height=_media.height, supports_streaming=True)
                MEDIA_GROUP.clear()
                for file in FILES:
                    os.remove(file) if os.path.isfile(file) else None
                for thumb in THUMB_PATHS:
                    os.remove(thumb) if os.path.isfile(thumb) else None
                FILES.clear()

        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await client.edit_message_text(sender, edit_id, "Have you joined the channel?")
        except PeerIdInvalid:
            chat = msg_link.split("/")[-3]
            new_link = f"t.me/c/{chat}/{msg_id}" if chat.isdigit() else f"t.me/b/{chat}/{msg_id}"
            await get_msg(userbot, client, bot, sender, edit_id, new_link, i)
        except Exception as e:
            if any(err in str(e) for err in ["messages.SendMedia", "SaveBigFilePartRequest", "SendMediaRequest", "File size equals to 0 B"]):
                try:
                    UT = time.time()
                    uploader = await fast_upload(file, file, UT, bot, edit, '**UPLOADING:**')
                    attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height, round_message=round_message, supports_streaming=True)]
                    await bot.send_file(sender, uploader, caption=caption, thumb=thumb_path, attributes=attributes, force_document=False)
                    os.remove(file) if os.path.isfile(file) else None
                except Exception as e:
                    await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
                    os.remove(file) if os.path.isfile(file) else None
            else:
                await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
                os.remove(file) if os.path.isfile(file) else None
            await edit.delete()
    else:
        edit = await client.edit_message_text(sender, edit_id, "Cloning.")
        chat = msg_link.split("t.me")[1].split("/")[1]
        try:
            msg = await client.get_messages(chat, msg_id)
            if msg.empty:
                new_link = f't.me/b/{chat}/{msg_id}'
                await get_msg(userbot, client, bot, sender, edit_id, new_link, i)
            await client.copy_message(sender, chat, msg_id)
        except Exception as e:
            await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
        await edit.delete()

async def get_bulk_msg(userbot, client, sender, msg_link, i, _range):
    x = await client.send_message(sender, "Processing " + str(i+1))
    await get_msg(userbot, client, Drone, sender, x.id, msg_link, i, _range)