from flask import Flask

from charat2.helpers.auth import get_request_user, set_cookie
from charat2.model.connections import (
    db_connect,
    db_commit,
    db_disconnect,
    redis_connect,
    redis_disconnect,
)
from charat2.views import home, account, chat, chat_api

app = Flask(__name__)

app.before_request(redis_connect)
app.before_request(db_connect)
app.before_request(get_request_user)

app.after_request(set_cookie)
app.after_request(db_commit)

app.teardown_request(db_disconnect)
app.teardown_request(redis_disconnect)

app.add_url_rule("/", "home", home, methods=("GET",))

app.add_url_rule("/log-in", "log_in", account.log_in, methods=("POST",))
app.add_url_rule("/log-out", "log_out", account.log_out, methods=("POST",))
app.add_url_rule("/register", "register", account.register, methods=("POST",))

app.add_url_rule("/create_chat", "create_chat", chat.create_chat, methods=("POST",))
app.add_url_rule("/chat/<url>", "chat", chat.chat, methods=("GET",))

app.add_url_rule("/chat_api/messages", "messages", chat_api.messages, methods=("POST",))
app.add_url_rule("/chat_api/send", "send", chat_api.send, methods=("post",))
app.add_url_rule("/chat_api/set_state", "set_state", chat_api.set_state, methods=("POST",))
app.add_url_rule("/chat_api/set_group", "set_group", chat_api.set_group, methods=("POST",))
app.add_url_rule("/chat_api/user_action", "user_action", chat_api.user_action, methods=("POST",))
app.add_url_rule("/chat_api/set_flag", "set_flag", chat_api.set_flag, methods=("POST",))
app.add_url_rule("/chat_api/set_info", "set_info", chat_api.set_info, methods=("POST",))
app.add_url_rule("/chat_api/save", "save", chat_api.save, methods=("POST",))
app.add_url_rule("/chat_api/ping", "ping", chat_api.ping, methods=("POST",))
app.add_url_rule("/chat_api/quit", "quit", chat_api.quit, methods=("POST",))

