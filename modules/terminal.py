from .. import loader, utils
import logging, asyncio, telethon

def register(cb):
    logging.debug("Registering %s", __file__)
    cb(TerminalMod())

class TerminalMod(loader.Module):
    def __init__(self):
        logging.debug("%s started", __file__)
        self.commands = {"terminal":self.terminalcmd, "terminate":self.terminatecmd, "kill":self.killcmd}
        self.config = {"FLOOD_WAIT_PROTECT":5}
        self.name = "Terminal"
        self.help = "Runs commands"
        self.activecmds = {}

    async def terminalcmd(self, message):
        await self.runcmd(message, utils.get_args_raw(message))


    async def runcmd(self, message, cmd):
        sproc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        msg = MessageEditor(message, cmd, self.config["FLOOD_WAIT_PROTECT"])
        self.activecmds[hash_msg(message)] = sproc
        await msg.redraw()
        await asyncio.gather(read_stream(msg.update_stdout, sproc.stdout), read_stream(msg.update_stderr, sproc.stderr))
        await msg.cmd_ended(await sproc.wait())
        del self.activecmds[hash_msg(message)]

    async def terminatecmd(self, message):
        if hash_msg(await message.get_reply_message()) in self.activecmds:
            self.activecmds[hash_msg(await message.get_reply_message())].terminate()
        else:
            await message.edit("No command is running in that message.")

    async def killcmd(self, message):
        if hash_msg(await message.get_reply_message()) in self.activecmds:
            self.activecmds[hash_msg(await message.get_reply_message())].kill()
        else:
            await message.edit("No command is running in that message.")

def hash_msg(message):
    return str(utils.get_chat_id(message))+"/"+str(message.id)

async def read_stream(func, stream):
    data = ""
    while True:
        dat = (await stream.readline()).decode("utf-8")
        if not dat:
            break
        data += dat
        asyncio.create_task(func(data))

class MessageEditor():
    def __init__(self, message, command, floodwaittime):
        self.message = message
        self.command = command
        self.stdout = ""
        self.stderr = ""
        self.rc = None
        self.redraws = 0
        self.floodwaittime = floodwaittime
    async def update_stdout(self, stdout):
        self.stdout = stdout
        await self.redraw()
    async def update_stderr(self, stderr):
        self.stderr = stderr
        await self.redraw()
    async def redraw(self):
        # Avoid spamming telegram servers with requests. Require a pause before sending data.
        self.redraws += 1
        await asyncio.sleep(self.floodwaittime)
        self.redraws -= 1
        if self.redraws > 0:
            return

        text = "<code>Running command: "+utils.escape_html(self.command)+"\n"
        if self.rc != None:
            text += "Process exited with code "+utils.escape_html(str(self.rc))
        text += "\nStdout:\n"
        text += utils.escape_html(self.stdout[max(len(self.stdout) - 2048, 0):])+"\n\nStderr:\n"
        text += utils.escape_html(self.stderr[max(len(self.stdout) - 1024, 0):])+"</code>"
        try:
            await self.message.edit(text, parse_mode="HTML")
        except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
            logging.warning(e)
        except telethon.errors.rpcerrorlist.MessageTooLongError as e:
            logging.error(e)
            logging.error(text)
    async def cmd_ended(self, rc):
        self.rc = rc
        await self.redraw()
