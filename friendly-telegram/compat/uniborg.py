# flake8: noqa: I didnt finish coding it lol

from functools import wraps
from inspect import signature

class UniborgClient:
    def __init__(self, clients):
        
    def __call__(self, *args, **kwargs):
        return self._client.__call__(*args, **kwargs)

    def __getattr__(

    def on(**kwargs):
        def subreg(func):
            @wraps(func)
            def magicfunc(message):
                func()
            sig = signature(func)
            newsig = sig.replace(parameters=tuple(sig.parameters) + (Parameter("borg", KEYWORD_ONLY),
                                                                     Parameter("logger", KEYWORD_ONLY),
                                                                     Parameter("storage", KEYWORD_ONLY)))
            func.__signature__ = newsig
            return magicfunc
        return subreg
