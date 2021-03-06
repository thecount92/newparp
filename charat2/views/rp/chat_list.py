import paginate

from flask import abort, g, jsonify, render_template, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased, joinedload

from charat2.helpers import alt_formats
from charat2.helpers.auth import log_in_required
from charat2.model import (
    case_options,
    AnyChat,
    GroupChat,
    RequestedChat,
    RouletteChat,
    SearchedChat,
    PMChat,
    ChatUser,
)
from charat2.model.connections import use_db

chat_classes = {
    None: AnyChat,
    "group": GroupChat,
    "pm": PMChat,
#    "requested": RequestedChat,
    "roulette": RouletteChat,
    "searched": SearchedChat,
    "unread": AnyChat,
}


@alt_formats({"json"})
@use_db
@log_in_required
def chat_list(fmt=None, type=None, page=1):

    try:
        ChatClass = chat_classes[type]
    except KeyError:
        abort(404)

    if type in (None, "pm", "unread"):

        # Join opposing ChatUser on PM chats so we know who the other person is.
        PMChatUser = aliased(ChatUser)
        chats = g.db.query(ChatUser, ChatClass, PMChatUser).filter(
            ChatUser.subscribed == True,
        ).join(ChatClass).outerjoin(
            PMChatUser,
            and_(
                ChatClass.type == "pm",
                PMChatUser.chat_id == ChatClass.id,
                PMChatUser.user_id != g.user.id,
            ),
        ).options(joinedload(PMChatUser.user))

        if type == "pm":
            chats = chats.filter(ChatClass.type == "pm")
        elif type == "unread":
            chats = chats.filter(ChatClass.last_message > ChatUser.last_online)

    else:

        chats = g.db.query(ChatUser, ChatClass).join(ChatClass).filter(and_(
            ChatUser.subscribed == True,
            ChatClass.type == type,
        ))

    chats = chats.filter(
        ChatUser.user_id == g.user.id,
    ).order_by(
        ChatClass.last_message.desc(),
    ).offset((page - 1) * 50).limit(50).all()

    if len(chats) == 0 and page != 1:
        abort(404)

    chat_count = g.db.query(func.count('*')).select_from(ChatUser).filter(and_(
        ChatUser.user_id == g.user.id,
        ChatUser.subscribed == True,
    ))
    if type == "unread":
        chat_count = chat_count.join(ChatClass).filter(
            ChatClass.last_message > ChatUser.last_online,
        )
    elif type is not None:
        chat_count = chat_count.join(ChatClass).filter(ChatClass.type == type)
    chat_count = chat_count.scalar()

    chat_dicts = []
    for c in chats:
        cd = c[1].to_dict()
        online_user_ids = g.redis.hvals("chat:%s:online" % cd["id"])
        cd["online"] = len(set(online_user_ids))
        if c[1].type == "pm":
            cd["title"] = "Messaging " + c[2].user.username
            cd["url"] = "pm/" + c[2].user.username
            cd["partner_online"] = c[2].user.id in (int(_) for _ in online_user_ids)
        elif c[1].type != "group":
            cd["title"] = cd["url"]
        cd["unread"] = c[1].last_message > c[0].last_online
        chat_dicts.append(cd)

    if fmt == "json":

        return jsonify({
            "total": chat_count,
            "chats": chat_dicts,
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=chat_count,
        url_maker=lambda page: url_for("rp_chat_list", page=page, type=type),
    )

    return render_template(
        "rp/chat_list.html",
        type=type,
        chats=chat_dicts,
        paginator=paginator,
        chat_classes=chat_classes,
    )

