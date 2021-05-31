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

#    Modded by GeekTG Team

import functools
import logging

import telethon
from telethon.tl.functions.channels import GetParticipantRequest

from . import main

logger = logging.getLogger(__name__)

OWNER = 1 << 0
SUDO = 1 << 1
SUPPORT = 1 << 2
GROUP_OWNER = 1 << 3
GROUP_ADMIN_ADD_ADMINS = 1 << 4
GROUP_ADMIN_CHANGE_INFO = 1 << 5
GROUP_ADMIN_BAN_USERS = 1 << 6
GROUP_ADMIN_DELETE_MESSAGES = 1 << 7
GROUP_ADMIN_PIN_MESSAGES = 1 << 8
GROUP_ADMIN_INVITE_USERS = 1 << 9
GROUP_ADMIN = 1 << 10
GROUP_MEMBER = 1 << 11
PM = 1 << 12

BITMAP = {"OWNER": OWNER,
          "SUDO": SUDO,
          "SUPPORT": SUPPORT,
          "GROUP_OWNER": GROUP_OWNER,
          "GROUP_ADMIN_ADD_ADMINS": GROUP_ADMIN_ADD_ADMINS,
          "GROUP_ADMIN_CHANGE_INFO": GROUP_ADMIN_CHANGE_INFO,
          "GROUP_ADMIN_BAN_USERS": GROUP_ADMIN_BAN_USERS,
          "GROUP_ADMIN_DELETE_MESSAGES": GROUP_ADMIN_DELETE_MESSAGES,
          "GROUP_ADMIN_PIN_MESSAGES": GROUP_ADMIN_PIN_MESSAGES,
          "GROUP_ADMIN_INVITE_USERS": GROUP_ADMIN_INVITE_USERS,
          "GROUP_ADMIN": GROUP_ADMIN,
          "GROUP_MEMBER": GROUP_MEMBER,
          "PM": PM}

GROUP_ADMIN_ANY = (GROUP_ADMIN_ADD_ADMINS | GROUP_ADMIN_CHANGE_INFO | GROUP_ADMIN_BAN_USERS
                   | GROUP_ADMIN_DELETE_MESSAGES | GROUP_ADMIN_PIN_MESSAGES | GROUP_ADMIN_INVITE_USERS | GROUP_ADMIN)

DEFAULT_PERMISSIONS = (OWNER | SUDO)

PUBLIC_PERMISSIONS = (GROUP_OWNER | GROUP_ADMIN_ANY | GROUP_MEMBER | PM)

ALL = (1 << 13) - 1


def owner(func):
	return _sec(func, OWNER)


def sudo(func):
	return _sec(func, OWNER | SUDO)


def support(func):
	return _sec(func, OWNER | SUDO | SUPPORT)


def group_owner(func):
	return _sec(func, OWNER | SUDO | GROUP_OWNER)


def group_admin_add_admins(func):
	return _sec(func, OWNER | SUDO | GROUP_ADMIN_ADD_ADMINS)


def group_admin_change_info(func):
	return _sec(func, OWNER | SUDO | GROUP_ADMIN_CHANGE_INFO)


def group_admin_ban_users(func):
	return _sec(func, OWNER | SUDO | GROUP_ADMIN_BAN_USERS)


def group_admin_delete_messages(func):
	return _sec(func, OWNER | SUDO | GROUP_ADMIN_DELETE_MESSAGES)


def group_admin_pin_messages(func):
	return _sec(func, OWNER | SUDO | GROUP_ADMIN_PIN_MESSAGES)


def group_admin_invite_users(func):
	return _sec(func, OWNER | SUDO | GROUP_ADMIN_INVITE_USERS)


def group_admin(func):
	return _sec(func, OWNER | SUDO | GROUP_ADMIN)


def group_member(func):
	return _sec(func, OWNER | SUDO | GROUP_MEMBER)


def pm(func):
	return _sec(func, OWNER | SUDO | PM)


def unrestricted(func):
	return _sec(func, ALL)


def _sec(func, flags):
	prev = getattr(func, "security", 0)
	func.security = prev | flags
	return func


if __debug__:
	class _SafeCoroutine:
		def __init__(self, coroutine):
			self._coroutine = coroutine

		def __await__(self):
			return self._coroutine.__await__()

		def __bool__(self):
			raise ValueError("Trying to compute truthiness of un-awaited security result")

		def __eq__(self, other):
			raise ValueError("Trying to compute equality of un-awaited security result")

		def __repr__(self):
			return "<unawaited secure coroutine {} at {}>".format(repr(self._coroutine), hex(id(self)))

		__str__ = __repr__


class SecurityManager:
	def __init__(self, db, bot):
		# We read the db during init to prevent people manipulating it at runtime
		# TODO in the future this will be backed up by blocking the inspect module at runtime and blocking __setattr__
		self._any_admin = db.get(__name__, "any_admin", False)
		self._default = db.get(__name__, "default", DEFAULT_PERMISSIONS)
		self._owner = db.get(__name__, "owner", []).copy()
		self._sudo = db.get(__name__, "sudo", []).copy()
		self._support = db.get(__name__, "support", []).copy()
		self._bounding_mask = db.get(__name__, "bounding_mask", -1 if bot else DEFAULT_PERMISSIONS)
		self._perms = db.get(__name__, "masks", {}).copy()
		self._db = db

	async def init(self, client):
		if not self._owner:
			self._owner.append((await client.get_me(True)).user_id)

	def get_flags(self, func):
		if isinstance(func, int):
			config = func
		else:
			config = self._perms.get(func.__module__ + "." + func.__name__, getattr(func, "security", self._default))
		if config & ~ALL:
			logger.error("Security config contains unknown bits")
			return False
		return config & self._bounding_mask

	async def _check(self, message, func):
		config = self.get_flags(func)
		if not config:  # Either False or 0, either way we can failfast
			return False
		logger.debug("Checking security match for %d", config)

		f_owner = config & OWNER
		f_sudo = config & SUDO
		f_support = config & SUPPORT
		f_group_owner = config & GROUP_OWNER
		f_group_admin_add_admins = config & GROUP_ADMIN_ADD_ADMINS
		f_group_admin_change_info = config & GROUP_ADMIN_CHANGE_INFO
		f_group_admin_ban_users = config & GROUP_ADMIN_BAN_USERS
		f_group_admin_delete_messages = config & GROUP_ADMIN_DELETE_MESSAGES
		f_group_admin_pin_messages = config & GROUP_ADMIN_PIN_MESSAGES
		f_group_admin_invite_users = config & GROUP_ADMIN_INVITE_USERS
		f_group_admin = config & GROUP_ADMIN
		f_group_member = config & GROUP_MEMBER
		f_pm = config & PM

		f_group_admin_any = (f_group_admin_add_admins or f_group_admin_change_info or f_group_admin_ban_users
		                     or f_group_admin_delete_messages or f_group_admin_pin_messages
		                     or f_group_admin_invite_users or f_group_admin)

		if f_owner and message.sender_id in self._owner:
			return True
		if f_sudo and message.sender_id in self._sudo:
			return True
		if f_support and message.sender_id in self._support:
			return True

		if message.sender_id in self._db.get(main.__name__, "blacklist_users", []):
			return False

		if f_pm and message.is_private:
			return True

		if f_group_member and message.is_group:
			return True

		if f_group_admin_any or f_group_owner:
			if message.is_channel:
				if not message.is_group:
					if message.edit_date:
						return False  # anyone can assume identity of another in channels
					# TODO: iter admin log and search for the edit event, to check who edited
					chat = await message.get_chat()
					if not chat.creator and not (chat.admin_rights and chat.admin_rights.post_messages):
						return False
					if self._any_admin and f_group_admin_any:
						return True

					if f_group_admin:
						return True
				# TODO: when running as bot, send an inline button which allows confirmation of command
				else:
					participant = await message.client(GetParticipantRequest(await message.get_input_chat(),
					                                                         await message.get_input_sender()))
					participant = participant.participant
					if isinstance(participant, telethon.types.ChannelParticipantCreator):
						return True
					if isinstance(participant, telethon.types.ChannelParticipantAdmin):
						if self._any_admin and f_group_admin_any:
							return True
						rights = participant.admin_rights

						if f_group_admin:
							return True
						if f_group_admin_add_admins and rights.add_admins:
							return True
						if f_group_admin_change_info and rights.change_info:
							return True
						if f_group_admin_ban_users and rights.ban_users:
							return True
						if f_group_admin_delete_messages and rights.delete_messages:
							return True
						if f_group_admin_pin_messages and rights.pin_messages:
							return True
						if f_group_admin_invite_users and rights.invite_users:
							return True
			elif message.is_group:
				full_chat = await message.client(telethon.functions.messages.GetFullChatRequest(message.chat_id))
				participants = full_chat.full_chat.participants.participants
				participant = None
				for possible_participant in participants:
					if possible_participant.user_id == message.sender_id:
						participant = possible_participant
						break
				if not participant:
					return
				if isinstance(participant, telethon.types.ChatParticipantCreator):
					return True
				if (isinstance(participant, telethon.types.ChatParticipantAdmin)
				    and f_group_admin_any):
					return True
		return False

	if __debug__:
		@functools.wraps(_check)
		def check(self, *args, **kwargs):
			# This wrapper function will cause the function to raise if you don't await it
			return _SafeCoroutine(self._check(*args, **kwargs))
	else:
		check = _check
