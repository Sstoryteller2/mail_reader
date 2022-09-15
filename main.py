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

def main():
    imap = functions.connection()
    if not imap:
        sys.exit()

    status, messages = imap.select("INBOX")  # папка входящие
    res, unseen_msg = imap.uid('search', "UNSEEN", "ALL")
    unseen_msg = unseen_msg[0].decode("utf-8").split(" ")

    if unseen_msg[0]:
        for letter in unseen_msg:
            attachments=[]
            res, msg = imap.uid('fetch', letter, '(RFC822)')            
            if res == "OK":
                #получаем всю информацию о письме
                msg = email.message_from_bytes(msg[0][1])
                msg_date = email.utils.parsedate_tz(msg["Date"])
                msg_date = functions.date_parse(msg_date)
                
                msg_from = decode_header(msg["From"])                
                try:
                    if type(msg_from[0][0]) == type("str"):
                        msg_from = str(msg_from[0][0]).strip("<>").replace("<", "")
                    else:
                        msg_from = decode_header(msg["From"])[0][0].decode()
                    msg_subj = decode_header(msg["Subject"])[0][0].decode()
                except:
                    msg_from = decode_header(msg["From"])[0][0].decode()#.strip("<>").rstrip(">")
                    msg_from = msg_from#.replace("<", "")
                    msg_subj = (msg["Subject"])
                    if msg_subj != None:
                        msg_subj = decode_header(msg["Subject"])[0][0]
                        
                msg_id = msg["Message-ID"].lstrip("<").rstrip(">")
                msg_email = msg["Return-path"].lstrip("<").rstrip(">")
                
                payload = msg.get_payload()
                
                if msg.is_multipart():                    
                    letter_text=functions.get_text_from_multipart(msg)
                    attachments = functions.get_attachments(payload)                    
                else:                    
                    letter=base64.b64decode(payload).decode()
                    letter_text=functions.get_letter_text(letter)
                post_text = functions.post_construct(
                        msg_subj, msg_from, msg_email, letter_text, attachments
                        )                
                if len(post_text) > 4000:
                    post_text = post_text[:4000]
                    
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    functions.send_message(config.bot_key, post_text, config.chat_id)
                )
        imap.logout()
    else:
        imap.logout()
        sys.exit()


if __name__ == "__main__":
    try:
        main()
    except (Exception) as exp:        
        text=str("ошибка: " + str(exp))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
                functions.send_message(config.bot_key, text, config.chat_id)
                )
