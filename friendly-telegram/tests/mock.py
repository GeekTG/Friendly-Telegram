import asyncio
import random
import os

from .. import utils


class Tester:
    def __init__(self, client):
        self._client = client

    async def test_all(self, modules):
        ops = []
        for name, command in modules.commands.items():
            ops += [self.test_command(command, name)]
        ops = await asyncio.gather(*ops, return_exceptions=True)
        return dict(zip(modules.commands.keys(), ops))

    async def test_command(self, command_func, command_name):
        if not getattr(command_func, "is_testable", False):
            raise CommandNotTestable()
        msgs = await self.make_messages(command_name, command_func.mock_texts, command_func.mock_type)
        ops = [command_func(msg) for msg in msgs]
        return await asyncio.gather(*ops, return_exceptions=True)

    async def make_messages(self, command_name, texts, mock_type):
        if mock_type == "text":
            file = None
        else:
            file = os.path.join(utils.get_dir(__file__), "img_test.jpg")
        if mock_type == "file":
            fdoc = True
        else:
            fdoc = False
        texts += [""]
        for i in range(10):
            texts += random.sample(["hello", "world", "the", "brown", "cow", "jumped", "over",
                                    "a", "moon", "made", "of", "cheese"], random.randint(1, 10))
        ret = []
        for text in texts:
            ret += [self._client.send_message('me', "." + command_name + " " + text, file=file, force_document=fdoc)]
        return await asyncio.gather(*ret)


class CommandNotTestable(RuntimeError):
    pass
