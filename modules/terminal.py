from .. import loader, utils
import logging, asyncio, telethon, os, re

def register(cb):
    logging.debug("Registering %s", __file__)
    cb(TerminalMod())

class TerminalMod(loader.Module):
    def __init__(self):
        logging.debug("%s started", __file__)
        self.commands = {"terminal":self.terminalcmd, "terminate":self.terminatecmd, "kill":self.killcmd, "apt":self.aptcmd, "neofetch":self.neocmd}
        self.config = {"FLOOD_WAIT_PROTECT":2, "INTERACTIVE_AUTH_STRING":"Interactive authentication required.", "INTERACTIVE_PRIV_AUTH_STRING":"Please edit this message to the password for user {user} to run command {command}", "AUTHENTICATING_STRING":"Authenticating...", "AUTH_FAILED_STRING":"Authentication failed, please try again.", "AUTH_TOO_MANY_TRIES_STRING":"Authentication failed, please try again later."}
        self.name = "Terminal"
        self.help = "Runs commands"
        self.activecmds = {}

    async def terminalcmd(self, message):
        await self.runcmd(message, utils.get_args_raw(message))

    async def aptcmd(self, message):
        await self.runcmd(message, ("apt " if os.geteuid() == 0 else "sudo -S apt ")+utils.get_args_raw(message) + ' -y', RawMessageEditor(message, "apt command dummy", self.config))

    async def runcmd(self, message, cmd, editor=None):
        if cmd.split(" ")[0] == "sudo":
            needsswitch = True
            for word in cmd.split(" ", 1)[1].split(" "):
                if word[0] != "-":
                    break
                if word == "-S":
                    needsswitch = False
        if needsswitch:
            cmd = " ".join([cmd.split(" ", 1)[0], "-S", cmd.split(" ", 1)[1]])
        sproc = await asyncio.create_subprocess_shell(cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        if editor == None:
            editor = SudoMessageEditor(message, cmd, self.config)
        else:
            editor.update_process(sproc)
        self.activecmds[hash_msg(message)] = sproc
        await editor.redraw(True)
        await asyncio.gather(read_stream(editor.update_stdout, sproc.stdout, self.config["FLOOD_WAIT_PROTECT"]), read_stream(editor.update_stderr, sproc.stderr, self.config["FLOOD_WAIT_PROTECT"]))
        await editor.cmd_ended(await sproc.wait())
        del self.activecmds[hash_msg(message)]

    async def terminatecmd(self, message):
        if hash_msg(await message.get_reply_message()) in self.activecmds:
            try:
                self.activecmds[hash_msg(await message.get_reply_message())].terminate()
            except:
                await message.edit("Could not kill!")
            else:
                await message.edit("Killed!")
        else:
            await message.edit("No command is running in that message.")

    async def killcmd(self, message):
        if hash_msg(await message.get_reply_message()) in self.activecmds:
            try:
                self.activecmds[hash_msg(await message.get_reply_message())].kill()
            except:
                await message.edit("Could not kill!")
            else:
                await message.edit("Killed!")
        else:
            await message.edit("No command is running in that message.")

    async def neocmd(self, message):
        await self.runcmd(message, "neofetch --stdout", RawMessageEditor(message, "neofetch --stdout", self.config))


def hash_msg(message):
    return str(utils.get_chat_id(message))+"/"+str(message.id)

async def read_stream(func, stream, delay):
    last_task = None
    data = ""
    while True:
        dat = (await stream.read(1)).decode("utf-8")
        if not dat:
            break
        data += dat
        if last_task:
            last_task.cancel()
        last_task = asyncio.create_task(sleep_for_task(func(data), delay))

async def sleep_for_task(coro, delay):
    await asyncio.sleep(delay)
    try:
        await coro
    except asyncio.CancelledError:
        del coro

class MessageEditor():
    def __init__(self, message, command, config):
        self.message = message
        self.command = command
        self.stdout = ""
        self.stderr = ""
        self.rc = None
        self.redraws = 0
        self.config = config
    async def update_stdout(self, stdout):
        self.stdout = stdout
        await self.redraw()
    async def update_stderr(self, stderr):
        self.stderr = stderr
        await self.redraw()
    async def redraw(self, skip_wait=False):
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
        self.state = 4
        await self.redraw(True)
    def update_process(self, process):
        pass

class SudoMessageEditor(MessageEditor):
    PASS_REQ = "[sudo] password for"
    WRONG_PASS = r"\[sudo\] password for (.*): Sorry, try again\."
    TOO_MANY_TRIES = r"\[sudo\] password for (.*): sudo: [0-9]+ incorrect password attempts"
    def __init__(self, message, command, config):
        super().__init__(message, command, config)
        self.process = None
        self.state = 0
        self.authmsg = None
    def update_process(self, process):
        self.process = process
    async def update_stderr(self, stderr):
        logging.debug("stderr update "+stderr)
        self.stderr = stderr
        lines = stderr.strip().split("\n")
        lastline = lines[-1]
        lastlines = lastline.rsplit(" ", 1)
        handled = False
        if len(lines) > 1 and re.fullmatch(self.WRONG_PASS, lines[-2]) and lastlines[0] == self.PASS_REQ and self.state == 1:
            logging.debug("switching state to 0")
            await self.authmsg.edit(self.config["AUTH_FAILED_STRING"])
            self.state = 0
            handled = True
            await asyncio.sleep(2)
            await self.authmsg.delete()
        logging.debug("got here")
        if lastlines[0] == self.PASS_REQ and self.state == 0:
            logging.debug("Success to find sudo log!")
            text = r'<a href="tg://user?id='
            text += str((await self.message.client.get_me()).id)
            text += r'">'
            text += utils.escape_html(self.config["INTERACTIVE_AUTH_STRING"])
            text += r"</a>"
            try:
                await self.message.edit(text, parse_mode="HTML")
            except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
                logging.debug(e)
            logging.debug("edited message with link to self")
            self.authmsg = await self.message.client.send_message('me', self.config["INTERACTIVE_PRIV_AUTH_STRING"].format(command="<code>"+utils.escape_html(self.command)+"</code>", user=utils.escape_html(lastlines[1][:-1])), parse_mode="HTML")
            logging.debug("sent message to self")
            self.message.client.remove_event_handler(self.on_message_edited)
            self.message.client.add_event_handler(self.on_message_edited, telethon.events.messageedited.MessageEdited(chats=['me']))
            logging.debug("registered handler")
            handled = True
        if len(lines) > 1 and re.fullmatch(self.TOO_MANY_TRIES, lastline) and (self.state == 1 or self.state == 3 or self.state == 4):
            logging.debug("password wrong lots of times")
            await self.message.edit(self.config["AUTH_TOO_MANY_TRIES_STRING"])
            await self.authmsg.delete()
            self.state = 2
            handled = True
        if not handled:
            logging.debug("Didn't find sudo log.")
            if self.authmsg != None:
                await self.authmsg.delete()
                self.authmsg = None
            self.state = 2
            await self.redraw()
        logging.debug(self.state)
    async def update_stdout(self, stdout):
        self.stdout = stdout
        if state != 2:
            self.state = 3 # Means that we got stdout only
        if self.authmsg != None:
            await self.authmsg.delete()
            self.authmsg = None
        await self.redraw()
    async def on_message_edited(self, message):
        # Message contains sensitive information.
        if self.authmsg == None:
            return
        logging.debug("got message edit update in self"+str(message.id))
        if hash_msg(message) == hash_msg(self.authmsg):
            # The user has provided interactive authentication. Send password to stdin for sudo.
            try:
                self.authmsg = await message.edit(self.config["AUTHENTICATING_STRING"])
            except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
                pass
            self.state = 1
            self.process.stdin.write(message.message.message.split("\n", 1)[0].encode("utf-8")+b"\n")

class RawMessageEditor(SudoMessageEditor):
    async def redraw(self, skip_wait=False):
        if self.rc == None:
            text = '<code>' + utils.escape_html(self.stdout[max(len(self.stdout) - 4095, 0):]) + '</code>'
        elif self.rc == 0:
            text = '<code>' + utils.escape_html(self.stdout[max(len(self.stdout) - 4090, 0):]) + '</code>\nDone'
        else:
            text = '<code>' + utils.escape_html(self.stdout[max(len(self.stderr) - 4095, 0):]) + '</code>'
        try:
            await self.message.edit(text, parse_mode="HTML")
        except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
            logging.warning(e)
        except telethon.errors.rpcerrorlist.MessageEmptyError as e:
            logging.warning(e)
            logging.error(text)
        except telethon.errors.rpcerrorlist.MessageTooLongError as e:
            logging.error(e)
            logging.error(text)

