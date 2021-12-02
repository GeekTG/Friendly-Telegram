"""
    Copyright 2021 t.me/innocoffee
    Licensed under the Apache License, Version 2.0
    
    Author is not responsible for any consequencies caused by using this
    software or any of its parts. If you have any questions or wishes, feel
    free to contact Dan by sending pm to @innocoffee_alt.
"""

#<3 title: AdvancedSettings
#<3 pic: https://img.icons8.com/fluency/48/000000/voice-id.png
#<3 desc: Расширенные настройки для GeekTG форка FTG.

from .. import loader, utils, main
import logging

logger = logging.getLogger(__name__)


@loader.tds
class AdvancedSettingsMod(loader.Module):
    """Advanced settings for GeekTG only"""
    strings = {
        "name": "AdvancedSettings",
        'watchers': '👾 <b>Watchers:</b>\n\n<b>{}</b>',
        'mod404': '👾 <b>Watcher {} not found</b>',
        'already_disabled': '👾 <b>Watcher {} already disabled</b>',
        'disabled': '👾 <b>Watcher {} is now disabled</b>',
        'enabled': '👾 <b>Watcher {} is now enabled</b>',
        'args': '👾 <b>You need to specify watcher name</b>'
    }

    def get_watchers(self):
        return [str(_.__self__.__class__.strings['name']) for _ in self.allmodules.watchers if _.__self__.__class__.strings is not None], self.db.get(main.__name__, 'disabled_watchers', {})

    async def client_ready(self, client, db):
        self.db = db

    async def watcherscmd(self, message):
        """List current watchers"""
        watchers, disabled_watchers = self.get_watchers()
        watchers = [f'♻️ {_}' for _ in watchers if _ not in list(disabled_watchers.keys())]
        watchers += [f'💢 {k} {v}' for k, v in disabled_watchers.items()]
        await utils.answer(message, self.strings('watchers').format('\n'.join(watchers)))


    async def watcherblcmd(self, message):
        """<module> - Toggle watcher in current chat"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings('args'))

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in [_.lower() for _ in watchers]:
            return await utils.answer(message, self.strings('mod404').format(args))

        args = [_ for _ in watchers if _.lower() == args.lower()][0]

        current_bl = [v for k, v in disabled_watchers.items() if k.lower() == args.lower()]
        current_bl = current_bl[0] if current_bl else []

        chat = utils.get_chat_id(message)
        if chat not in current_bl:
            if args in disabled_watchers:
                for k, v in disabled_watchers.items():
                    if k.lower() == args.lower():
                        disabled_watchers[k].append(chat)
                        break
            else:
                disabled_watchers[args] = [chat]

            await utils.answer(message, self.strings('disabled').format(args) + ' <b>in current chat</b>')
        else:
            for k, v in disabled_watchers.items():
                if k.lower() == args.lower():
                    disabled_watchers[k].remove(chat)
                    if not disabled_watchers[k]:
                        del disabled_watchers[k]
                    break

            await utils.answer(message, self.strings('enabled').format(args) + ' <b>in current chat</b>')

        self.db.set(main.__name__, 'disabled_watchers', disabled_watchers)

    async def watchercmd(self, message):
        """<module> - Toggle global watcher rules
Args:
[-c - only in chats]
[-p - only in pm]
[-o - only out]
[-i - only incoming]"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings('args'))

        chats, pm, out, incoming = False, False, False, False

        if '-c' in args:
            args = args.replace('-c', '').replace('  ', ' ').strip()
            chats = True

        if '-p' in args:
            args = args.replace('-p', '').replace('  ', ' ').strip()
            pm = True

        if '-o' in args:
            args = args.replace('-o', '').replace('  ', ' ').strip()
            out = True

        if '-i' in args:
            args = args.replace('-i', '').replace('  ', ' ').strip()
            incoming = True

        if chats and pm: pm = False
        if out and incoming: incoming = False

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in [_.lower() for _ in watchers]:
            return await utils.answer(message, self.strings('mod404').format(args))

        args = [_ for _ in watchers if _.lower() == args.lower()][0]

        if chats or pm or out or incoming:
            disabled_watchers[args] = [
                *(['only_chats'] if chats else []), 
                *(['only_pm'] if pm else []), 
                *(['out'] if out else []), 
                *(['in'] if incoming else []), 
            ]
            self.db.set(main.__name__, 'disabled_watchers', disabled_watchers)
            await utils.answer(message, self.strings('enabled').format(args) + f' (<code>{disabled_watchers[args]}</code>)')
            return


        if args in disabled_watchers and '*' in disabled_watchers[args]:
            await utils.answer(message, self.strings('enabled').format(args))
            del disabled_watchers[args]
            self.db.set(main.__name__, 'disabled_watchers', disabled_watchers)
            return
        else:
            disabled_watchers[args] = ['*']
        self.db.set(main.__name__, 'disabled_watchers', disabled_watchers)
        await utils.answer(message, self.strings('disabled').format(args))

