#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

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

from gtts import gTTS

from io import BytesIO

from .. import loader, utils


def register(cb):
    cb(TTSMod())


class TTSMod(loader.Module):
    def __init__(self):
        self.name = "Text to speech"

    async def ttscmd(self, message):
        """Convert text to speech with Google APIs"""
        args = utils.get_args_raw(message)
        if not args:
            args = (await message.get_reply_message()).message

        tts = await utils.run_sync(gTTS, args)
        voice = BytesIO()
        tts.write_to_fp(voice)
        voice.seek(0)
        voice.name = "voice.mp3"

        await utils.answer(message, voice, voice_note=True)
