from .. import loader, utils
import logging, asyncio, telethon, os, re

logger = logging.getLogger(__name__)

def register(cb):
    cb(TerminalMod())

class TerminalMod(loader.Module):
    """Runs commands"""
    def __init__(self):
        self.commands = {"terminal":self.terminalcmd, "terminate":self.terminatecmd, "kill":self.killcmd, "apt":self.aptcmd, "neofetch":self.neocmd, "uptime":self.upcmd, "speedtest":self.speedcmd}
        self.config = {"FLOOD_WAIT_PROTECT":2, "INTERACTIVE_AUTH_STRING":"Interactive authentication required.", "INTERACTIVE_PRIV_AUTH_STRING":"Please edit this message to the password for user {user} to run command {command}", "AUTHENTICATING_STRING":"Authenticating...", "AUTH_FAILED_STRING":"Authentication failed, please try again.", "AUTH_TOO_MANY_TRIES_STRING":"Authentication failed, please try again later."}
        self.name = "Terminal"
        self.activecmds = {}

    async def terminalcmd(self, message):
        """.terminal <command>"""
        await self.runcmd(message, utils.get_args_raw(message))

    async def aptcmd(self, message):
        """Shorthand for '.terminal apt'"""
        await self.runcmd(message, ("apt " if os.geteuid() == 0 else "sudo -S apt ")+utils.get_args_raw(message) + ' -y', RawMessageEditor(message, "apt "+utils.get_args_raw(message), self.config, True))

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
        sproc = await asyncio.create_subprocess_shell(cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=utils.get_base_dir())
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
        """Use in reply to send SIGTERM to a process"""
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
        """Use in reply to send SIGKILL to a process"""
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
        """Show system stats via neofetch"""
        await self.runcmd(message, "neofetch --stdout", RawMessageEditor(message, "neofetch --stdout", self.config))

    async def upcmd(self, message):
        """Show system uptime"""
        await self.runcmd(message, "uptime", RawMessageEditor(message, "uptime", self.config))

    async def speedcmd(self, message):
        """Make an internet speed test"""
        await message.edit("<code>Running speedtest...</code>", parse_mode="HTML")
        await self.runcmd(message, "speedtest --simple --secure", RawMessageEditor(message, "speedtest --simple --secure", self.config))

def hash_msg(message):
    return str(utils.get_chat_id(message))+"/"+str(message.id)

async def read_stream(func, stream, delay):
    last_task = None
    data = ""
    while True:
        dat = (await stream.read(1)).decode("utf-8")
        if not dat:
            if last_task:
                last_task.cancel()
                await func(data) # If there is no last task there is inherantly no data, so theres no point sending a blank string
            break
        data += dat
        if last_task:
            last_task.cancel()
        last_task = asyncio.create_task(sleep_for_task(func(data), delay))

async def sleep_for_task(coro, delay):
    try:
        await asyncio.sleep(delay)
        await coro
    except asyncio.CancelledError:
        del coro
        raise

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
            pass
        except telethon.errors.rpcerrorlist.MessageTooLongError as e:
            logger.error(e)
            logger.error(text)
        # The message is never empty due to the template header
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
        logger.debug("stderr update "+stderr)
        self.stderr = stderr
        lines = stderr.strip().split("\n")
        lastline = lines[-1]
        lastlines = lastline.rsplit(" ", 1)
        handled = False
        if len(lines) > 1 and re.fullmatch(self.WRONG_PASS, lines[-2]) and lastlines[0] == self.PASS_REQ and self.state == 1:
            logger.debug("switching state to 0")
            await self.authmsg.edit(self.config["AUTH_FAILED_STRING"])
            self.state = 0
            handled = True
            await asyncio.sleep(2)
            await self.authmsg.delete()
        logger.debug("got here")
        if lastlines[0] == self.PASS_REQ and self.state == 0:
            logger.debug("Success to find sudo log!")
            text = r'<a href="tg://user?id='
            text += str((await self.message.client.get_me()).id)
            text += r'">'
            text += utils.escape_html(self.config["INTERACTIVE_AUTH_STRING"])
            text += r"</a>"
            try:
                await self.message.edit(text, parse_mode="HTML")
            except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
                logger.debug(e)
            logger.debug("edited message with link to self")
            self.authmsg = await self.message.client.send_message('me', self.config["INTERACTIVE_PRIV_AUTH_STRING"].format(command="<code>"+utils.escape_html(self.command)+"</code>", user=utils.escape_html(lastlines[1][:-1])), parse_mode="HTML")
            logger.debug("sent message to self")
            self.message.client.remove_event_handler(self.on_message_edited)
            self.message.client.add_event_handler(self.on_message_edited, telethon.events.messageedited.MessageEdited(chats=['me']))
            logger.debug("registered handler")
            handled = True
        if len(lines) > 1 and re.fullmatch(self.TOO_MANY_TRIES, lastline) and (self.state == 1 or self.state == 3 or self.state == 4):
            logger.debug("password wrong lots of times")
            await self.message.edit(self.config["AUTH_TOO_MANY_TRIES_STRING"])
            await self.authmsg.delete()
            self.state = 2
            handled = True
        if not handled:
            logger.debug("Didn't find sudo log.")
            if self.authmsg != None:
                await self.authmsg.delete()
                self.authmsg = None
            self.state = 2
            await self.redraw()
        logger.debug(self.state)
    async def update_stdout(self, stdout):
        self.stdout = stdout
        if self.state != 2:
            self.state = 3 # Means that we got stdout only
        if self.authmsg != None:
            await self.authmsg.delete()
            self.authmsg = None
        await self.redraw()
    async def on_message_edited(self, message):
        # Message contains sensitive information.
        if self.authmsg == None:
            return
        logger.debug("got message edit update in self"+str(message.id))
        if hash_msg(message) == hash_msg(self.authmsg):
            # The user has provided interactive authentication. Send password to stdin for sudo.
            try:
                self.authmsg = await message.edit(self.config["AUTHENTICATING_STRING"])
            except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
                pass
            self.state = 1
            self.process.stdin.write(message.message.message.split("\n", 1)[0].encode("utf-8")+b"\n")

class RawMessageEditor(SudoMessageEditor):
    def __init__(self, message, command, config, show_done=False):
        super().__init__(message, command, config)
        self.show_done = show_done
    async def redraw(self, skip_wait=False):
        logger.debug(self.rc)
        if self.rc == None:
            text = '<code>' + utils.escape_html(self.stdout[max(len(self.stdout) - 4095, 0):]) + '</code>'
        elif self.rc == 0:
            text = '<code>' + utils.escape_html(self.stdout[max(len(self.stdout) - 4090, 0):]) + '</code>'
        else:
            text = '<code>' + utils.escape_html(self.stderr[max(len(self.stderr) - 4095, 0):]) + '</code>'
        if self.rc != None and self.show_done:
            text += "\nDone"
        logger.debug(text)
        try:
            await self.message.edit(text, parse_mode="HTML")
        except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
            pass
        except telethon.errors.rpcerrorlist.MessageEmptyError as e:
            pass
        except telethon.errors.rpcerrorlist.MessageTooLongError as e:
            logger.error(e)
            logger.error(text)

