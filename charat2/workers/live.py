#!/usr/bin/python

import json
import os
import re
import signal
import time

from datetime import datetime
from redis import StrictRedis
from sqlalchemy import and_, func
from sqlalchemy.orm.exc import NoResultFound
from tornado.gen import engine, Task
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler
from tornadoredis import Client
from uuid import uuid4

from charat2.helpers.chat import (
    UnauthorizedException,
    BannedException,
    TooManyPeopleException,
    KickedException,
    authorize_joining,
    kick_check,
    join,
    get_userlist,
    disconnect,
    send_quit_message,
)
from charat2.model import sm, AnyChat, Ban, ChatUser, Message, User, SearchCharacter
from charat2.model.connections import redis_pool

redis = StrictRedis(connection_pool=redis_pool)


origin_regex = re.compile("^https?:\/\/%s$" % os.environ["BASE_DOMAIN"].replace(".", "\."))


sockets = set()


class ChatHandler(WebSocketHandler):

    def get_chat_user(self):
        return self.db.query(
            ChatUser, User, AnyChat,
        ).join(
            User, ChatUser.user_id == User.id,
        ).join(
            AnyChat, ChatUser.chat_id == AnyChat.id,
        ).filter(and_(
            ChatUser.user_id == self.user_id,
            ChatUser.chat_id == self.chat_id,
        )).one()

    def set_typing(self, is_typing):
        command = redis.sadd if is_typing else redis.srem
        typing_key = "chat:%s:typing" % self.chat_id
        if command(typing_key, self.user_number):
            redis.publish(self.channels["typing"], json.dumps({
                "typing": list(int(_) for _ in redis.smembers(typing_key)),
            }))

    def check_origin(self, origin):
        return origin_regex.match(origin) is not None

    def prepare(self):
        self.id = str(uuid4())
        self.joined = False
        try:
            self.session_id = self.cookies["session"].value
            self.chat_id = int(self.path_args[0])
            self.user_id = int(redis.get("session:%s" % self.session_id))
        except (KeyError, TypeError, ValueError):
            self.send_error(400)
            return
        self.db = sm()
        try:
            self.chat_user, self.user, self.chat = self.get_chat_user()
        except NoResultFound:
            self.send_error(404)
            return
        # Remember the user number so typing notifications can refer to it
        # without reopening the database session.
        self.user_number = self.chat_user.number
        self.user.last_online = datetime.now()
        self.user.last_ip = self.request.headers["X-Forwarded-For"]
        if self.user.group == "banned":
            self.send_error(403)
            return
        try:
            authorize_joining(redis, self.db, self)
        except (UnauthorizedException, BannedException, TooManyPeopleException):
            self.send_error(403)
            return

    def open(self, chat_id):
        sockets.add(self)
        redis.sadd("chat:%s:sockets:%s" % (self.chat_id, self.session_id), self.id)
        print "socket opened:", self.id, self.chat.url, self.user.username

        try:
            kick_check(redis, self)
        except KickedException:
            self.write_message(json.dumps({"exit": "kick"}))
            self.close()
            return

        # Subscribe
        self.channels = {
            "chat": "channel:%s" % self.chat_id,
            "user": "channel:%s:%s" % (self.chat_id, self.user_id),
            "typing": "channel:%s:typing" % self.chat_id,
        }
        if self.chat.type == "pm":
            self.channels["pm"] = "channel:pm:%s" % self.user_id
        self.redis_listen()

        # Send backlog.
        try:
            after = int(self.request.query_arguments["after"][0])
        except (KeyError, IndexError, ValueError):
            after = 0
        messages = redis.zrangebyscore("chat:%s" % self.chat_id, "(%s" % after, "+inf")
        self.write_message(json.dumps({
            "chat": self.chat.to_dict(),
            "messages": [json.loads(_) for _ in messages],
        }))

        join_message_sent = join(redis, self.db, self)
        self.joined = True

        # Send userlist if nothing was sent by join().
        if not join_message_sent:
            self.write_message(json.dumps({"users": get_userlist(self.db, redis, self.chat)}))

        self.db.commit()

    def on_message(self, message):
        print "message:", message
        if message in ("typing", "stopped_typing"):
            self.set_typing(message == "typing")

    def on_close(self):
        # Unsubscribe here and let the exit callback handle disconnecting.
        if hasattr(self, "redis_client"):
            self.redis_client.unsubscribe(self.redis_client.subscribed)
        if self.joined and disconnect(redis, self.chat_id, self.id):
            try:
                send_quit_message(self.db, redis, *self.get_chat_user())
            except NoResultFound:
                send_userlist(self.db, redis, self.chat)
            self.db.commit()
        self.set_typing(False)
        print "socket closed:", self.id
        redis.srem("chat:%s:sockets:%s" % (self.chat_id, self.session_id), self.id)
        sockets.remove(self)

    def finish(self, *args, **kwargs):
        if hasattr(self, "db"):
            self.db.close()
            del self.db
        super(ChatHandler, self).finish(*args, **kwargs)

    @engine
    def redis_listen(self):
        self.redis_client = Client(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            selected_db=int(os.environ["REDIS_DB"]),
        )
        yield Task(self.redis_client.subscribe, self.channels.values())
        self.redis_client.listen(self.on_redis_message, self.on_redis_unsubscribe)

    def on_redis_message(self, message):
        print "redis message:", message
        if message.kind != "message":
            return
        self.write_message(message.body)
        if message.channel == self.channels["user"]:
            data = json.loads(message.body)
            if "exit" in data:
                self.joined = False
                self.close()

    def on_redis_unsubscribe(self, callback):
        self.redis_client.disconnect()


def sig_handler(sig, frame):
    print "Caught signal %s." % sig
    ioloop.add_callback_from_signal(shutdown)


def shutdown():
    print "Shutting down."
    for socket in sockets:
        ioloop.add_callback(socket.close)
    deadline = time.time() + 10
    def stop_loop():
        now = time.time()
        if now < deadline and (ioloop._callbacks or ioloop._timeouts):
            ioloop.add_timeout(now + 0.1, stop_loop)
        else:
            ioloop.stop()
    stop_loop()

class HealthHandler(RequestHandler):
    def prepare(self):
        self.db = sm()

    def get(self):
        redis.set("health", 1)
        self.db.query(SearchCharacter).first()
        self.write("ok")

    def finish(self, *args, **kwargs):
        if hasattr(self, "db"):
            self.db.close()
            del self.db
        super(HealthHandler, self).finish(*args, **kwargs)

if __name__ == "__main__":

    application = Application([
        (r"/(\d+)", ChatHandler),
        (r"/health", HealthHandler)
    ])

    http_server = HTTPServer(application)
    http_server.listen(8000)

    ioloop = IOLoop.instance()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    ioloop.start()

