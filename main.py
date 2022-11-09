#!/usr/bin/env python3
# coding: utf-8

import functions
import config
import email
from email.header import decode_header
import base64
import sys
import time
import asyncio
import traceback

ENCODING=config.encoding

def main():
    imap = functions.connection()
    if not imap:
        sys.exit()

    status, messages = imap.select("INBOX")  # папка входящие
    res, unseen_msg = imap.uid("search", "UNSEEN", "ALL")
    unseen_msg = unseen_msg[0].decode(ENCODING).split(" ")

    if unseen_msg[0]:
        for letter in unseen_msg:
            attachments = []
            res, msg = imap.uid("fetch", letter, "(RFC822)")
            if res == "OK":
                msg = email.message_from_bytes(msg[0][1])

                msg_date = functions.date_parse(email.utils.parsedate_tz(msg["Date"]))
                msg_from = functions.from_subj_decode(msg["From"])
                msg_subj = functions.from_subj_decode(msg["Subject"])
                msg_id = msg["Message-ID"].lstrip("<").rstrip(">")
                msg_email = msg["Return-path"].lstrip("<").rstrip(">")
                if not msg_email:
                    msg_email = (
                        decode_header(msg["From"])[1][0]
                        .decode(ENCODING)
                        .replace("<", "")
                        .replace(">", "")
                        .replace(" ", "")
                    )

                letter_text = functions.get_letter_text(msg)
                attachments = functions.get_attachments(msg)

                post_text = functions.post_construct(
                    msg_subj, msg_from, msg_email, letter_text, attachments
                )
                if len(post_text) > 4000:
                    post_text = post_text[:4000]

                loop = asyncio.get_event_loop()
                reply_id = loop.run_until_complete(
                    functions.send_message(config.bot_key, post_text, config.chat_id)
                )
                if config.send_attach:
                    functions.send_attach(msg, msg_subj, reply_id)
        imap.logout()
    else:
        imap.logout()
        sys.exit()


if __name__ == "__main__":
    try:
        main()
    except (Exception) as exp:
        text = str("ошибка: " + str(exp))
        print(traceback.format_exc())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            functions.send_message(config.bot_key, text, config.chat_id)
        )
