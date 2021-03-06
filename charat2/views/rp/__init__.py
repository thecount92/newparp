import os
import json
from flask import abort, g, jsonify, make_response, render_template, request, redirect, url_for
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers import alt_formats
from charat2.helpers.auth import log_in_required
from charat2.model import case_options, Character, GroupChat, SearchCharacterGroup, SearchCharacterChoice, User
from charat2.model.connections import use_db, db_connect


@use_db
def home():

    if g.user is None:
        return render_template("rp/home_guest.html")

    mode = request.args.get("mode", g.user.last_search_mode)
    g.user.last_search_mode = mode

    characters = g.db.query(Character).filter(Character.user_id == g.user.id).order_by(Character.title).all()

    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    if mode == "roulette":
        return render_template(
            "rp/home_roulette.html",
            characters=characters,
            search_character_groups=search_character_groups,
        )

    elif mode == "search":
        picky = set(_[0] for _ in g.db.query(
            SearchCharacterChoice.search_character_id,
        ).filter(
            SearchCharacterChoice.user_id == g.user.id,
        ).all())
        return render_template(
            "rp/home_search.html",
            characters=characters,
            search_character_groups=search_character_groups,
            case_options=case_options,
            replacements=json.loads(g.user.replacements),
            regexes=json.loads(g.user.regexes),
            User=User,
            picky=picky,
        )

    abort(404)


@alt_formats({"json"})
@use_db
def groups(fmt=None):

    style_filter = set()
    for style in GroupChat.style.type.enums:
        if style in request.args:
            style_filter.add(style)
    if not style_filter:
        if g.user is not None:
            style_filter = g.user.group_chat_styles
        else:
            style_filter.add("script")

    level_filter = set()
    for level in GroupChat.level.type.enums:
        if level in request.args:
            level_filter.add(level)
    if not level_filter:
        if g.user is not None:
            level_filter = g.user.group_chat_levels
        else:
            level_filter.add("sfw")

    if g.user is not None:
        g.user.group_chat_styles = style_filter
        g.user.group_chat_levels = level_filter

    groups_query = g.db.query(GroupChat).filter(and_(
        GroupChat.publicity.in_(("listed", "pinned")),
        GroupChat.style.in_(style_filter),
        GroupChat.level.in_(level_filter),
    ))
    groups = []
    for group in groups_query:
        online_users = len(set(g.redis.hvals("chat:%s:online" % group.id)))
        if online_users > 0:
            groups.append((group, online_users))
    groups.sort(key=lambda _: (_[0].publicity, _[1]), reverse=True)
    chat_dicts = []
    for chat, online in groups:
        cd = chat.to_dict()
        cd["online"] = online
        chat_dicts.append(cd)
    if fmt == "json":
        return jsonify({
            "chats": chat_dicts,
        })

    return render_template(
        "rp/groups.html",
        groups=chat_dicts,
        style_filter=style_filter,
        level_filter=level_filter,
    )

