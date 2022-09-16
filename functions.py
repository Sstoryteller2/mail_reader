import imaplib
import email
from email.header import decode_header
import traceback
import base64
import re
from datetime import datetime
import config
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types
import aiohttp


def connection():
    mail_pass = config.mail_pass
    username = config.username
    imap_server = "imap.mail.ru"
    imap = imaplib.IMAP4_SSL(imap_server)
    sts, res = imap.login(username, mail_pass)
    if sts == "OK":
        return imap
    else:
        return False


def encode_att_names(str_pl):
    enode_name = re.findall("\=\?.*?\?\=", str_pl)
    if len(enode_name) == 1:
        decode_name = decode_header(enode_name[0])[0][0]
        decode_name = decode_name.decode("utf-8")
        str_pl = str_pl.replace(enode_name[0], decode_name)
    if len(enode_name) > 1:
        nm = ""
        for part in enode_name:
            decode_name = decode_header(part)[0][0]
            decode_name = decode_name.decode("utf-8")
            nm += decode_name
        str_pl = str_pl.replace(enode_name[0], nm)
        for c, i in enumerate(enode_name):
            if c > 0:
                str_pl = str_pl.replace(enode_name[c], "").replace('"', "").rstrip()
    return str_pl


def get_attachments(msg):
    attachments = list()
    for part in msg.walk():
        if (
            "name" in part["Content-Type"]
            and part.get_content_disposition() == "attachment"
        ):
            str_pl = part["Content-Type"]
            str_pl = encode_att_names(str_pl)
            attachments.append(str_pl)
    return attachments


def date_parse(msg_date):
    dt_obj = "".join(str(msg_date[:6]))
    dt_obj = dt_obj.strip("'(),")
    dt_obj = datetime.strptime(dt_obj, "%Y, %m, %d, %H, %M, %S")
    return dt_obj


async def send_message(bot_token, message, chat, rpl=None, prv=None):
    bot = Bot(token=bot_token)
    await bot.get_session()
    obj = await bot.send_message(
        chat_id=chat,
        text=message,
        parse_mode="HTML",
        reply_to_message_id=rpl,
        disable_web_page_preview=prv,
    )
    await bot._session.close()
    return obj.message_id


def get_letter_text_from_html(body):
    body = body.replace("<div><div>", "<div>").replace("</div></div>", "</div>")
    try:
        soup = BeautifulSoup(body, "html.parser")
        paragraphs = soup.find_all("div")
        text = ""
        for paragraph in paragraphs:
            text += paragraph.text + "\n"
        return text.replace("\xa0", " ")
    except (Exception) as exp:
        print("text ftom html err ", exp)
        return False


def decode_text(payload):
    if payload.get_content_subtype() == "plain":
        letter_text = (
            (base64.b64decode(payload.get_payload()).decode()).lstrip().rstrip()
        )
        letter_text = letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")
        return letter_text
    if payload.get_content_subtype() == "html":
        try:
            letter_text = (
                (base64.b64decode(payload.get_payload()).decode()).lstrip().rstrip()
            )
            letter_text = get_letter_text_from_html(letter_text)
        except:
            letter_text = get_letter_text_from_html(payload.get_payload())
        return letter_text
    else:
        return False


def get_text_from_multipart(msg):
    for part in msg.walk():
        count = 0
        if part.get_content_maintype() == "text" and count == 0:
            letter_text = decode_text(part)
            count += 1
            return letter_text


def post_construct(msg_subj, msg_from, msg_email, letter_text, attachments):
    att_txt = ""
    for atts in attachments:
        att_txt += atts.strip() + "\n"
    txt = ""
    txt += (
        "\U0001F4E8 <b>"
        + str(msg_subj)
        + "</b>"
        + "\n\n<pre>"
        + str(msg_from)
        + "\n"
        + msg_email
        + "</pre>\n\n"
        + letter_text
        + "\n\n"
        + "\U0001F4CE<i> вложения: </i>"
        + str(len(attachments))
        + "\n\n"
        + att_txt
    )
    return txt
