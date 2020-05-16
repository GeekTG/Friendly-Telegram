import logging
try:
    import coloredlogs  # Optional support for https://pypi.org/project/coloredlogs
except ModuleNotFoundError:
    _formatter = logging.Formatter
else:
    _formatter = coloredlogs.ColoredFormatter


class MemoryHandler(logging.Handler):
    """Keeps 2 buffers. One for dispatched messages. One for unused messages. When the length of the 2 together is 100
       truncate to make them 100 together, first trimming handled then unused."""
    def __init__(self, target, capacity):
        super().__init__(0)
        self.target = target
        self.capacity = capacity
        self.buffer = []
        self.handledbuffer = []
        self.lvl = logging.WARNING  # Default loglevel

    def setLevel(self, level):
        self.lvl = level

    def dump(self):
        """Return a list of logging entries"""
        return self.handledbuffer + self.buffer

    def dumps(self, lvl=0):
        """Return all entries of minimum level as list of strings"""
        return [self.target.format(record) for record in (self.buffer + self.handledbuffer) if record.levelno >= lvl]

    def emit(self, record):
        if len(self.buffer) + len(self.handledbuffer) >= self.capacity:
            if self.handledbuffer:
                del self.handledbuffer[0]
            else:
                del self.buffer[0]
        self.buffer.append(record)
        if record.levelno >= self.lvl and self.lvl >= 0:
            self.acquire()
            try:
                for precord in self.buffer:
                    self.target.handle(precord)
                self.handledbuffer = self.handledbuffer[-(self.capacity - len(self.buffer)):] + self.buffer
                self.buffer = []
            finally:
                self.release()


def init():
    formatter = _formatter(logging.BASIC_FORMAT, "")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logging.getLogger().handlers = []
    logging.getLogger().addHandler(MemoryHandler(handler, 500))
    logging.getLogger().setLevel(0)
    logging.captureWarnings(True)
