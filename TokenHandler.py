import time

TIMEOUT = 60


class TooManyTokensException(Exception):
    def __init__(self, message):
        super().__init__(message)


class TimeoutException(Exception):
    def __init__(self, message):
        super().__init__(message)


class TokenHandler:
    def __init__(self):
        self.start = 0

    def start_token_time(self):
        self.start = time.time()

    def reset_token_time(self):
        self.start = time.time()

    def check_token_timeout(self):
        now = time.time() - self.start

        if now > TIMEOUT:
            raise TimeoutException("Timeout exceeded")
        else:
            "OK"

    def validate_token(self):
        now = time.time() - self.start

        if now < 5:
            raise TooManyTokensException("Too many tokens. Please manually remove.")