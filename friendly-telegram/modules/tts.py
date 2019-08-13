import logging

from gtts import gTTS

from io import BytesIO

from .. import loader, utils

def register(cb):
    cb(TTSMod())

class TTSMod(loader.Module):
    def __init__(self):
        self.commands = {"tts":self.ttscmd}
        self.config = {}
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
