import logging

types = ["text", "image", "file"]


def testable(texts=[], t="text"):
    if t not in types:
        logging.error("Invalid self-test type " + repr(t))
        return lambda x: x
    if not isinstance(texts, list):
        logging.error("Invalid self-test text " + repr(texts))

    def sub(func):
        func.is_testable = True
        func.mock_texts = texts
        func.mock_type = t
        return func
    return sub
