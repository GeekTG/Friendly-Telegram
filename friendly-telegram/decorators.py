#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#    Friendly Telegram Userbot
#    by GeekTG Team

import functools
import shlex

import telethon

from . import core


def test(*, func=None, resp=None, pre=None, post=None, edits=0, stages=[5], args=[], timeout=5, total_timeout=15):
	if func is None and resp is None:
		def decorator(func):
			@functools.wraps(func)
			async def inner(target, db, client, cmd):
				stage = db.get(core.__name__, "stage", 0)
				if stage not in stages:
					return
				if pre is not False:
					async with telethon.custom.Conversation(client, target, timeout=timeout,
					                                        total_timeout=total_timeout, max_messages=None,
					                                        exclusive=True, replies_are_responses=True) as conv:
						if args is not None:
							await conv.send_message("." + cmd + " " + " ".join([shlex.quote(arg) for arg in args]))
						try:
							ret = await func(conv)
						except TypeError:
							ret = await func(stage, conv)
						if post is not False:
							if isinstance(ret, type) and issubclass(ret, Exception):
								try:
									resp = await conv.get_response()
								except ret:
									pass
								else:
									raise AssertionError("Expected {} but got {}".format(ret, resp))
							elif isinstance(ret, str):
								resp = await conv.get_response()
								for i in range(edits):
									resp = await conv.get_edit()
								assert resp.text == ret, (resp, ret)
							elif callable(ret):
								resp = await conv.get_response()
								ret(resp)
				else:
					await func(target, db, client, cmd)

			return inner
	elif not pre and not post:
		def decorator(cmd):
			if resp is None:
				cmd.test = func
			else:
				@test(pre=True, post=True, edits=edits, stages=stages)
				async def inner(conv):
					return resp

				cmd.test = inner
			return cmd
	else:
		raise TypeError("Bad parameters")
	return decorator
