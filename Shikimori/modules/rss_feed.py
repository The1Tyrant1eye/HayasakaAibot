"""
STATUS: Code is working. ✅
"""

"""
BSD 2-Clause License

Copyright (C) 2022, SOME-1HING [https://github.com/SOME-1HING]

Credits:-
    I don't know who originally wrote this code. If you originally wrote this code, please reach out to me. 

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import html
import re

from feedparser import parse
from Shikimori import dispatcher, updater, SUPPORT_CHAT
from Shikimori.modules.helper_funcs.chat_status import user_admin
from Shikimori.modules.sql import rss_sql as sql
from telegram import ParseMode, Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler

@user_admin
def subscribe(update: Update, context: CallbackContext):
    tg_chat_id = str(update.effective_chat.id)

    tg_feed_link = "https://www.animenewsnetwork.com/all/rss.xml?ann-edition=in"

    link_processed = parse(tg_feed_link)

    # check if link is a valid RSS Feed link
    if link_processed.bozo == 0:
        if len(link_processed.entries[0]) >= 1:
            tg_old_entry_link = link_processed.entries[0].link
        else:
            tg_old_entry_link = ""

        # gather the row which contains exactly that telegram group ID and link for later comparison
        row = sql.check_url_availability(tg_chat_id, tg_feed_link)

        # check if there's an entry already added to DB by the same user in the same group with the same link
        if row:
            update.effective_message.reply_text(
                "You have already subscribed to Anime News Network.")
        else:
            sql.add_url(tg_chat_id, tg_feed_link, tg_old_entry_link)

            update.effective_message.reply_text("Added Anime News Network to subscription")
    else:
        update.effective_message.reply_text(
            f"Something went worng. Contact {SUPPORT_CHAT}")

@user_admin
def unsubscribe(update: Update, context: CallbackContext):
    tg_chat_id = str(update.effective_chat.id)

    tg_feed_link = "https://www.animenewsnetwork.com/all/rss.xml?ann-edition=in"

    link_processed = parse(tg_feed_link)

    if link_processed.bozo == 0:
        user_data = sql.check_url_availability(tg_chat_id, tg_feed_link)

        if user_data:
            sql.remove_url(tg_chat_id, tg_feed_link)

            update.effective_message.reply_text(
                "Removed Anime News Network from subscription")
        else:
            update.effective_message.reply_text(
                "You haven't subscribed to this Anime News Subscription yet")
    
    else:
        update.effective_message.reply_text(
            f"Something went worng. Contact {SUPPORT_CHAT}")

def show_url(update: Update, context: CallbackContext):
    tg_chat_id = str(update.effective_chat.id)
    bot = context.bot
    args = context.args
    if len(args) >= 1:
        tg_feed_link = args[0]
        link_processed = parse(tg_feed_link)

        if link_processed.bozo == 0:
            feed_title = link_processed.feed.get("title", default="Unknown")
            feed_description = "<i>{}</i>".format(
                re.sub(
                    '<[^<]+?>', '',
                    link_processed.feed.get("description", default="Unknown")))
            feed_link = link_processed.feed.get("link", default="Unknown")

            feed_message = "<b>Feed Title:</b> \n{}" \
                           "\n\n<b>Feed Description:</b> \n{}" \
                           "\n\n<b>Feed Link:</b> \n{}".format(html.escape(feed_title),
                                                               feed_description,
                                                               html.escape(feed_link))

            if len(link_processed.entries) >= 1:
                entry_title = link_processed.entries[0].get(
                    "title", default="Unknown")
                entry_description = "<i>{}</i>".format(
                    re.sub(
                        '<[^<]+?>', '', link_processed.entries[0].get(
                            "description", default="Unknown")))
                entry_link = link_processed.entries[0].get(
                    "link", default="Unknown")

                entry_message = "\n\n<b>Entry Title:</b> \n{}" \
                                "\n\n<b>Entry Description:</b> \n{}" \
                                "\n\n<b>Entry Link:</b> \n{}".format(html.escape(entry_title),
                                                                     entry_description,
                                                                     html.escape(entry_link))
                final_message = feed_message + entry_message

                bot.send_message(
                    chat_id=tg_chat_id,
                    text=final_message,
                    parse_mode=ParseMode.HTML)
            else:
                bot.send_message(
                    chat_id=tg_chat_id,
                    text=feed_message,
                    parse_mode=ParseMode.HTML)
        else:
            update.effective_message.reply_text(
                "This link is not an RSS Feed link")
    else:
        update.effective_message.reply_text("URL missing")


def list_urls(update: Update, context: CallbackContext):
    tg_chat_id = str(update.effective_chat.id)
    bot = context.bot
    user_data = sql.get_urls(tg_chat_id)

    # this loops gets every link from the DB based on the filter above and appends it to the list
    links_list = [row.feed_link for row in user_data]

    final_content = "\n\n".join(links_list)

    # check if the length of the message is too long to be posted in 1 chat bubble
    if len(final_content) == 0:
        bot.send_message(
            chat_id=tg_chat_id, text="This chat is not subscribed to any links")
    elif len(final_content) <= constants.MAX_MESSAGE_LENGTH:
        bot.send_message(
            chat_id=tg_chat_id,
            text="This chat is subscribed to the following links:\n" +
            final_content)
    else:
        bot.send_message(
            chat_id=tg_chat_id,
            parse_mode=ParseMode.HTML,
            text="<b>Warning:</b> The message is too long to be sent")


@user_admin
def add_url(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if len(args) >= 1:
        chat = update.effective_chat
        tg_chat_id = str(update.effective_chat.id)

        tg_feed_link = args[0]

        link_processed = parse(tg_feed_link)

        # check if link is a valid RSS Feed link
        if link_processed.bozo == 0:
            if len(link_processed.entries[0]) >= 1:
                tg_old_entry_link = link_processed.entries[0].link
            else:
                tg_old_entry_link = ""

            # gather the row which contains exactly that telegram group ID and link for later comparison
            row = sql.check_url_availability(tg_chat_id, tg_feed_link)

            # check if there's an entry already added to DB by the same user in the same group with the same link
            if row:
                update.effective_message.reply_text(
                    "This URL has already been added")
            else:
                sql.add_url(tg_chat_id, tg_feed_link, tg_old_entry_link)

                update.effective_message.reply_text("Added URL to subscription")
        else:
            update.effective_message.reply_text(
                "This link is not an RSS Feed link")
    else:
        update.effective_message.reply_text("URL missing")


@user_admin
def remove_url(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if len(args) >= 1:
        tg_chat_id = str(update.effective_chat.id)

        tg_feed_link = args[0]

        link_processed = parse(tg_feed_link)

        if link_processed.bozo == 0:
            user_data = sql.check_url_availability(tg_chat_id, tg_feed_link)

            if user_data:
                sql.remove_url(tg_chat_id, tg_feed_link)

                update.effective_message.reply_text(
                    "Removed URL from subscription")
            else:
                update.effective_message.reply_text(
                    "You haven't subscribed to this URL yet")
        else:
            update.effective_message.reply_text(
                "This link is not an RSS Feed link")
    else:
        update.effective_message.reply_text("URL missing")


def rss_update(context: CallbackContext):
    user_data = sql.get_all()
    job = context.job
    bot = context.bot
    # this loop checks for every row in the DB
    for row in user_data:
        row_id = row.id
        tg_chat_id = row.chat_id
        tg_feed_link = row.feed_link

        feed_processed = parse(tg_feed_link)

        tg_old_entry_link = row.old_entry_link

        new_entry_links = []
        new_entry_titles = []
        new_entry_description = []

        # this loop checks for every entry from the RSS Feed link from the DB row
        for entry in feed_processed.entries:
            # check if there are any new updates to the RSS Feed from the old entry
            if entry.link != tg_old_entry_link:
                new_entry_links.append(entry.link)
                new_entry_titles.append(entry.title)
                new_entry_description.append(entry.description)
            else:
                break

        # check if there's any new entries queued from the last check
        if new_entry_links:
            sql.update_url(row_id, new_entry_links)
        else:
            pass

        if len(new_entry_links) < 5:
            # this loop sends every new update to each user from each group based on the DB entries
            for link, title, description in zip(
                    reversed(new_entry_links), reversed(new_entry_titles), reversed(new_entry_description)):
                description = description.replace("cite", "b")
                final_message = '💫<b>{}</b>💫\n\n<i>{}</i>\n<a href="{}">_</a>'.format(
                    html.escape(title), html.escape(description), html.escape(link))
                buttons = [[InlineKeyboardButton("More Info", url=link)]]

                if len(final_message) <= constants.MAX_MESSAGE_LENGTH:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text=final_message,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        disable_web_page_preview=False,
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text="<b>Warning:</b> The message is too long to be sent",
                        parse_mode=ParseMode.HTML)
        else:
            for link, title, description in zip(
                    reversed(new_entry_links[-5:]),
                    reversed(new_entry_titles[-5:]),
                    reversed(new_entry_description[-5:])):
                description = description.replace("cite", "b")
                final_message = '💫<b>{}</b>💫\n\n<i>{}</i>\n<a href="{}">_</a>'.format(
                    html.escape(title), html.escape(description), html.escape(link))
                buttons = [[InlineKeyboardButton("More Info", url=link)]]

                if len(final_message) <= constants.MAX_MESSAGE_LENGTH:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text=final_message,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        disable_web_page_preview=False,
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text="<b>Warning:</b> The message is too long to be sent",
                        parse_mode=ParseMode.HTML)

            bot.send_message(
                chat_id=tg_chat_id,
                parse_mode=ParseMode.HTML,
                text="<b>Warning: </b>{} occurrences have been left out to prevent spam"
                .format(len(new_entry_links) - 5))


def rss_set(context: CallbackContext):
    user_data = sql.get_all()
    bot, job = context.bot, context.job
    # this loop checks for every row in the DB
    for row in user_data:
        row_id = row.id
        tg_feed_link = row.feed_link
        tg_old_entry_link = row.old_entry_link

        feed_processed = parse(tg_feed_link)

        new_entry_links = []
        new_entry_titles = []
        new_entry_description = []

        # this loop checks for every entry from the RSS Feed link from the DB row
        for entry in feed_processed.entries:
            # check if there are any new updates to the RSS Feed from the old entry
            if entry.link != tg_old_entry_link:
                new_entry_links.append(entry.link)
                new_entry_titles.append(entry.title)
                new_entry_description.append(entry.description)
            else:
                break

        # check if there's any new entries queued from the last check
        if new_entry_links:
            sql.update_url(row_id, new_entry_links)
        else:
            pass


__help__ = """
 • `/addrss <link>`*:* add an RSS link to the subscriptions.
 • `/removerss <link>`*:* removes the RSS link from the subscriptions.
 • `/rss <link>`*:* shows the link's data and the last entry, for testing purposes.
 • `/listrss`*:* shows the list of rss feeds that the chat is currently subscribed to
 • `/subscribe` : Suscribes to Anime News Network feeds.
 • `/unsubscribe` : Suscribes to Anime News Network feeds..

*NOTE:* In groups, only admins can add/remove RSS links to the group's subscription
"""

__mod_name__ = "RSS Feed🪄"

job = updater.job_queue

job_rss_set = job.run_once(rss_set, 5)
job_rss_update = job.run_repeating(rss_update, interval=60, first=60)
job_rss_set.enabled = True
job_rss_update.enabled = True

SHOW_URL_HANDLER = CommandHandler("rss", show_url)
ADD_URL_HANDLER = CommandHandler("addrss", add_url)
REMOVE_URL_HANDLER = CommandHandler("removerss", remove_url)
LIST_URLS_HANDLER = CommandHandler("listrss", list_urls)
SUBSCRIBE_HANDLER = CommandHandler("subscribe", subscribe)
UNSUBSCRIBE_HANDLER = CommandHandler("unsubscribe", unsubscribe)

dispatcher.add_handler(SUBSCRIBE_HANDLER)
dispatcher.add_handler(UNSUBSCRIBE_HANDLER)
dispatcher.add_handler(SHOW_URL_HANDLER)
dispatcher.add_handler(ADD_URL_HANDLER)
dispatcher.add_handler(REMOVE_URL_HANDLER)
dispatcher.add_handler(LIST_URLS_HANDLER)
