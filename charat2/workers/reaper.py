#!/usr/bin/python

import time

from redis import StrictRedis
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.chat import disconnect, send_message, send_userlist
from charat2.model import sm, Message, ChatUser, User
from charat2.model.connections import redis_pool

db = sm()
redis = StrictRedis(connection_pool=redis_pool)

if __name__ == "__main__":
    while True:
        current_time = int(time.time())
        for dead in redis.zrangebyscore("chats_alive", 0, current_time):
            chat_id, user_id = dead.split('/')
            disconnected = disconnect(redis, chat_id, user_id)
            # Only send a timeout message if they were already online.
            if not disconnected:
                continue
            try:
                dead_chat_user = db.query(User, ChatUser).filter(and_(
                    g.user.id,
                    ChatUser.chat_id==chat_id,
                )).options(joinedload(ChatUser.chat)).one()
            except NoResultFound:
                pass
            if dead_chat_user.group == "silent":
                send_userlist(db, redis, dead_chat_user.chat)
            else:
                send_message(db, redis, Message(
                    chat_id=chat_id,
                    user_id=dead_chat_user.user_id,
                    type="timeout",
                    name=dead_chat_user.name,
                    # omg i've been waiting so long to get rid of that FUCKING
                    # SEMI COLON
                    text="[color=#%s]%s[/color] [[color=#%s]%s[/color]] lost connection." % (
                        dead_chat_user.color, dead_chat_user.name,
                    ),
                ))
            print current_time, "Reaping ", dead
        db.commit()
        time.sleep(1)

