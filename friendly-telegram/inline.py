"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the Creative Commons CC BY-NC-ND 4.0

    Full license text can be found at:
    https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode

    Human-friendly one:
    https://creativecommons.org/licenses/by-nc-nd/4.0
"""

from types import FunctionType
from typing import Union, Any, List

from aiogram import Bot, Dispatcher, executor, types
import aiogram

import re
import time
import random
import asyncio

from telethon.tl.types import *
import telethon

from . import utils
import logging
import requests
import io
import json
import functools

logger = logging.getLogger(__name__)

photo = io.BytesIO(requests.get('https://github.com/GeekTG/Friendly-Telegram/raw/beta/friendly-telegram/bot_avatar.png').content)
photo.name = "avatar.png"

class InlineError(Exception):
    """Exception raised when implemented error is occured in InlineManager"""
    pass

class InlineCall:
    def __init__(self):
        self.delete = None
        self.unload = None
        self.edit = None


def rand(size: int) -> str:
    """Return random string of len `size`"""
    return ''.join([random.choice('abcdefghijklmnopqrstuvwzyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(size)])


def array_sum(array: list) -> Any:
    """Performs basic sum operation on array"""
    result = []
    for item in array:
        result += item

    return result


async def edit(text: str, reply_markup: List[List[dict]] = [], force_me: Union[bool, None] = None, always_allow: Union[List[int], None] = None, self: Any = None, query: Any = None, form: Any = None, form_uid: Any = None, inline_message_id: Union[str, None] = None) -> None:
    """Do not edit or pass `self`, `query`, `form`, `form_uid` params, they are for internal use only"""
    assert isinstance(text, str)
    if isinstance(reply_markup, list):
        form['buttons'] = reply_markup
    if isinstance(force_me, bool):
        form['force_me'] = force_me
    if isinstance(always_allow, list):
        form['always_allow'] = always_allow
    try:
        await self._bot.edit_message_text(text,
                            inline_message_id=inline_message_id or query.inline_message_id,
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                            reply_markup=self._generate_markup(form_uid))
    except aiogram.utils.exceptions.MessageNotModified:
        await query.answer()
    except aiogram.utils.exceptions.RetryAfter as e:
        logger.info(f'Sleeping {e.timeout}s on aiogram FloodWait...')
        await asyncio.sleep(e.timeout)
        return await edit(text, reply_markup, force_me, always_allow, self, query, form, form_uid, inline_message_id)

async def delete(self: Any = None, form: Any = None, form_uid: Any = None) -> bool:
    """Params `self`, `form`, `form_uid` are for internal use only, do not try to pass them"""
    try:
        await self._client.delete_messages(form['chat'], [form['message_id']])
        del self._forms[form_uid]
    except Exception:
        return False

    return True

async def unload(self: Any = None, form_uid: Any = None) -> bool:
    """Params `self`, `form_uid` are for internal use only, do not try to pass them"""
    try:
        del self._forms[form_uid]
    except Exception:
        return False

    return True

class InlineManager:
    def __init__(self, client, db, allmodules) -> None:
        """Initialize InlineManager to create forms"""
        self._client = client
        self._db = db
        self._allmodules = allmodules

        self._token = db.get('geektg.inline', 'bot_token', False)

        self._forms = {}

        self._forms_db_path = os.path.join(utils.get_base_dir(), '../inline-forms-db.json')

        self._markup_ttl = 60 * 60 * 24

        self.init_complete = False
        self._empty_markup = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        self._empty_markup.row(
            aiogram.types.inline_keyboard.InlineKeyboardButton(
                "✌️ Wait",
                url="https://t.me/chat_ftg"
            )
        )

        try:
            self._forms = json.loads(open(self._forms_db_path, 'r').read())
        except Exception:
            pass

    async def _create_bot(self) -> None:
        # This is called outside of conversation, so we can start the new one
        # We create new bot
        logger.info('User don\'t have bot, attemping creating new one')
        async with self._client.conversation('@BotFather', exclusive=False) as conv:
            m = await conv.send_message('/cancel')
            r = await conv.get_response()

            await m.delete()
            await r.delete()

            m = await conv.send_message('/newbot')
            r = await conv.get_response()

            if '20' in m.raw_text:
                return False

            await m.delete()
            await r.delete()

            # Set its name to user's name + GeekTG Userbot
            m = await conv.send_message(f"{self._name}'s GeekTG Userbot")
            r = await conv.get_response()

            await m.delete()
            await r.delete()

            # Generate and set random username for bot
            uid = rand(6)
            username = f'geektg_{uid}_bot'

            m = await conv.send_message(username)
            r = await conv.get_response()

            await m.delete()
            await r.delete()

            # Set bot profile pic
            m = await conv.send_message('/setuserpic')
            r = await conv.get_response()

            await m.delete()
            await r.delete()

            m = await conv.send_message(username)
            r = await conv.get_response()

            await m.delete()
            await r.delete()

            m = await conv.send_file(photo)
            r = await conv.get_response()

            await m.delete()
            await r.delete()



        # Re-attempt search. If it won't find newly created (or not created?) bot
        # it will return `False`, that's why `init_complete` will be `False`
        return await self._assert_token(False)


    async def _assert_token(self, create_new_if_needed=True) -> None:
        # If the token is set in db
        if self._token:
            # Just return `True`
            return True

        logger.info('Bot token not found in db, attempting search in BotFather')
        # Start conversation with BotFather to attemp search
        async with self._client.conversation('@BotFather') as conv:
            # Wrap it in try-except in case user banned BotFather
            try:
                # Try sending command
                m = await conv.send_message('/cancel')
            except telethon.errors.rpcerrorlist.YouBlockedUserError:
                # If user banned BotFather, unban him
                await self._client(telethon.tl.functions.contacts.UnblockRequest(
                    id='@BotFather'
                ))
                # And resend message
                m = await conv.send_message('/cancel')

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            m = await conv.send_message('/token')
            r = await conv.get_response()

            await m.delete()
            await r.delete()

            # User do not have any bots yet, so just create new one
            if not hasattr(r, 'reply_markup') or not hasattr(r.reply_markup, 'rows'):
                # Cancel current conversation (search)
                # bc we don't need it anymore
                await conv.cancel_all()
                return await self._create_bot()

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if re.search(r'@geektg_[0-9a-zA-Z]{6}_bot', button.text):
                        m = await conv.send_message(button.text)
                        r = await conv.get_response()

                        token = r.raw_text.splitlines()[1]
                        
                        await m.delete()
                        await r.delete()

                        # Enable inline mode or change its placeholder in case it is not set
                        m = await conv.send_message('/setinline')
                        r = await conv.get_response()

                        await m.delete()
                        await r.delete()

                        m = await conv.send_message(button.text)
                        r = await conv.get_response()

                        await m.delete()
                        await r.delete()

                        m = await conv.send_message('GeekQuery')
                        r = await conv.get_response()

                        await m.delete()
                        await r.delete()

                        m = await conv.send_message('/setinlinefeedback')
                        r = await conv.get_response()

                        await m.delete()
                        await r.delete()

                        m = await conv.send_message(button.text)
                        r = await conv.get_response()

                        await m.delete()
                        await r.delete()

                        m = await conv.send_message('Enabled')
                        r = await conv.get_response()

                        await m.delete()
                        await r.delete()

                        # Save token to database, now this bot is ready-to-use
                        self._db.set('geektg.inline', 'bot_token', token)
                        self._token = token

                        # Return `True` to say, that everything is okay
                        return True

        # And we are not returned after creation
        if create_new_if_needed:
            # Create new bot. It's recursive, so we will return
            # the result from this `if` branch
            return await self._create_bot()
        else:
            # User reached the limit of bots, or other error occured
            # while creating new bot, so just return `False`,
            # in case modules/loader.py knows, that we don't have
            # inline mode currently available. `init_complete`
            # will be set to `False`
            return False

    async def _cleaner(self) -> None:
        """Cleans outdated _forms"""
        while True:
            for form_uid, form in self._forms.copy().items():
                if form['ttl'] < time.time():
                    del self._forms[form_uid]

            try:
                open(self._forms_db_path, 'w').write(json.dumps(self._forms, indent=4, ensure_ascii=False))
            except Exception:
                # If we are on Heroku, or Termux, we can't properly save forms,
                # but it's not critical. Just ignore it.
                # On these platforms forms will be reset after every restart
                pass

            await asyncio.sleep(10)

    async def _register_manager(self) -> None:
        # Get info about user to use it in this class
        me = await self._client.get_me()
        self._me = me.id
        self._name = telethon.utils.get_display_name(me)

        # Assert that token is set to valid, and if not, 
        # set `init_complete` to `False` and return
        is_token_asserted = await self._assert_token()
        if not is_token_asserted:
            self.init_complete = False
            return
        
        # We successfully asserted token, so set `init_complete` to `True`
        self.init_complete = True

        # Create bot instance and dispatcher
        self._bot = Bot(token=self._token)
        self._dp = Dispatcher(self._bot)

        # Register required event handlers inside aiogram
        self._dp.register_inline_handler(self._inline_handler, lambda inline_query: True)
        self._dp.register_callback_query_handler(self._callback_query_handler, lambda query: True)
        self._dp.register_chosen_inline_handler(self._chosen_inline_handler, lambda chosen_inline_query: True)

        # And get bot username to call inline queries
        self._bot_username = (await self._bot.get_me()).username

        # Start polling as the separate task, just in case we will need
        # to force stop this coro. It should be cancelled only by `stop`
        # because it stops the bot from getting updates
        self._task = asyncio.ensure_future(self._dp.start_polling())
        self._cleaner_task = asyncio.ensure_future(self._cleaner())

    async def stop(self) -> None:
        await self._bot.close()
        self._task.cancel()

    def _generate_markup(self, form_uid: Union[str, list]) -> "aiogram.types.inline_keyboard.InlineKeyboardMarkup":
        """Generate markup for form"""
        markup = aiogram.types.inline_keyboard.InlineKeyboardMarkup()

        for row in (self._forms[form_uid]['buttons'] if isinstance(form_uid, str) else form_uid):
            for button in row:
                # logger.info(button)
                if 'callback' in button and \
                    not isinstance(button['callback'], str):
                    func = button['callback']
                    button['callback'] = f"{func.__self__.__class__.__name__}.{func.__func__.__name__}"

                if 'callback' in button and \
                    '_callback_data' not in button:
                    button['_callback_data'] = rand(30)

                if 'handler' in button and \
                    not isinstance(button['handler'], str):
                    func = button['handler']
                    button['handler'] = f"{func.__self__.__class__.__name__}.{func.__func__.__name__}"

                if 'input' in button and \
                    '_switch_query' not in button:
                    button['_switch_query'] = rand(10)


        for row in (self._forms[form_uid]['buttons'] if isinstance(form_uid, str) else form_uid):
            markup.row(*[
                aiogram.types.inline_keyboard.InlineKeyboardButton(
                    button['text'],
                    url=button.get('url', None)
                ) if 'url' in button else \
                (
                    aiogram.types.inline_keyboard.InlineKeyboardButton(
                        button['text'],
                        callback_data=button['_callback_data']
                    ) if 'callback' in button else \
                    aiogram.types.inline_keyboard.InlineKeyboardButton(
                        button['text'],
                        switch_inline_query_current_chat=button['_switch_query'] + ' '
                    )
                ) for button in row
            ]
            )

        return markup

    async def _inline_handler(self, inline_query: aiogram.types.InlineQuery) -> None:
        """Inline query handler (forms' calls)"""
        # Retrieve query from passed object
        query = inline_query.query

        if not query:
            return

        # Find Loader instance to access security layers
        if not hasattr(self, '_loader'):
            for mod in self._allmodules.modules:
                if mod.__class__.__name__ == "LoaderMod":
                    self._loader = mod
                    break

        for form_uid, form in self._forms.copy().items():
            for button in array_sum(form.get('buttons', [])):
                if '_switch_query' in button and \
                    'input' in button and \
                    button['_switch_query'] == query.split()[0] and \
                    inline_query.from_user.id in [self._me] + \
                    self._loader.dispatcher.security._owner + \
                    form['always_allow']:
                    await inline_query.answer([aiogram.types.inline_query_result.InlineQueryResultArticle(
                        id=rand(20),
                        title=button['input'],
                        description="⚠️ Please, do not remove identifier!",
                        input_message_content=aiogram.types.input_message_content.InputTextMessageContent(
                            '🔄 <b>Transfering value to usebot...</b>\n<i>This message is gonna be deleted...</i>',
                            'HTML',
                            disable_web_page_preview=True
                        ),
                        reply_markup=self._empty_markup,
                    )], cache_time=60)
                    return

        # If we don't know, what this query is for, just ignore it
        if query not in self._forms:
            return

        # Otherwise, answer it with templated form
        await inline_query.answer([aiogram.types.inline_query_result.InlineQueryResultArticle(
            id=rand(20),
            title='GeekTG',
            input_message_content=aiogram.types.input_message_content.InputTextMessageContent(
                self._forms[query]['text'],
                'HTML',
                disable_web_page_preview=True
            ),
            reply_markup=self._generate_markup(query)
        )], cache_time=60)

    async def _callback_query_handler(self, query: aiogram.types.CallbackQuery, reply_markup: List[List[dict]] = []) -> None:
        """Callback query handler (buttons' presses)"""
        for form_uid, form in self._forms.copy().items():
            for button in array_sum(form.get('buttons', [])):
                if button.get('_callback_data', None) == query.data:
                    if form['force_me'] and \
                        query.from_user.id != self._me and \
                        query.from_user.id not in self._loader.dispatcher.security._owner and \
                        query.from_user.id not in form['always_allow']:
                        await query.answer('You are not allowed to press this button!')
                        return

                    query.delete = functools.partial(delete, self=self, form=form, form_uid=form_uid)
                    query.unload = functools.partial(unload, self=self, form_uid=form_uid)
                    query.edit = functools.partial(edit, self=self, query=query, form=form, form_uid=form_uid)

                    query.form = {'id': form_uid, **form}

                    for module in self._allmodules.modules:
                        if module.__class__.__name__ == button['callback'].split('.')[0] and \
                            hasattr(module, button['callback'].split('.')[1]):
                            return await getattr(module, button['callback'].split('.')[1])\
                                        (query, *button.get('args', []), **button.get('kwargs', {}))

                    del self._forms[form_uid]

    async def _chosen_inline_handler(self, chosen_inline_query: aiogram.types.ChosenInlineResult) -> None:
        query = chosen_inline_query.query

        for form_uid, form in self._forms.copy().items():
            for button in array_sum(form.get('buttons', [])):
                if '_switch_query' in button and \
                    'input' in button and \
                    button['_switch_query'] == query.split()[0] and \
                    chosen_inline_query.from_user.id in [self._me] + \
                    self._loader.dispatcher.security._owner + \
                    form['always_allow']:

                    query = query.split(maxsplit=1)[1] if len(query.split()) > 1 else ''

                    call = InlineCall()

                    call.delete = functools.partial(delete, self=self, form=form, form_uid=form_uid)
                    call.unload = functools.partial(unload, self=self, form_uid=form_uid)
                    call.edit = functools.partial(edit, self=self, query=chosen_inline_query, form=form, form_uid=form_uid)

                    for module in self._allmodules.modules:
                        if module.__class__.__name__ == button['handler'].split('.')[0] and \
                            hasattr(module, button['handler'].split('.')[1]):
                            return await getattr(module, button['handler'].split('.')[1])\
                                        (call, query, *button.get('args', []), **button.get('kwargs', {}))


    async def form(self, text: str, message: Union[Message, int], reply_markup: List[List[dict]] = [], force_me: bool = True, always_allow: List[int] = [], ttl: Union[int, bool] = False) -> bool:
        """Creates inline form with callback

                Args:
                        text
                                Content of inline form. HTML markdown supported

                        message
                                Where to send inline. Can be either `telethon.tl.types.Message` or `int`

                        reply_markup
                                List of buttons to insert in markup. List of dicts with
                                keys: text, callback

                        force_me
                                Either this form buttons must be pressed only by owner scope or no

                        always_allow
                                Users, that are allowed to press buttons in addition to previous rules

                        ttl
                                Time, when the form is going to be unloaded. Unload means, that the form
                                buttons with inline queries and callback queries will become unusable, but
                                buttons with type url will still work as usual. Pay attention, that ttl can't
                                be bigger, than default one (1 day) and must be either `int` or `False`
                        

        """

        if not isinstance(text, str):
            raise InlineError('Invalid type for `text`')

        if not isinstance(message, (Message, int)):
            raise InlineError('Invalid type for `message`')

        if not isinstance(reply_markup, list):
            raise InlineError('Invalid type for `reply_markup`')

        if not isinstance(force_me, bool):
            raise InlineError('Invalid type for `force_me`')

        if not isinstance(always_allow, list):
            raise InlineError('Invalid type for `always_allow`')

        if not isinstance(ttl, int) and ttl:
            raise InlineError('Invalid type for `ttl`')

        if isinstance(ttl, int) and (ttl > self._markup_ttl or ttl < 10):
            ttl = self._markup_ttl
            logger.debug("Defaulted ttl, because it breaks out of limits")

        form_uid = rand(30)

        self._forms[form_uid] = {
            'text': text,
            'buttons': reply_markup,
            'ttl': round(time.time()) + ttl or self._markup_ttl,
            'force_me': force_me,
            'always_allow': always_allow,
            'chat': None,
            'message_id': None
        }

        q = await self._client.inline_query(self._bot_username, form_uid)
        m = await q[0].click(utils.get_chat_id(message) if isinstance(message, Message) else message)
        self._forms[form_uid]['chat'] = utils.get_chat_id(m)
        self._forms[form_uid]['message_id'] = m.id
        if isinstance(message, Message):
            await message.delete()


if __name__ == "__main__":
    raise InlineError('This file must be called as a module')
