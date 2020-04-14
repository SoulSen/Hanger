from hangups.auth import get_auth_stdin


class Authenticator:
    def __init__(self, refresh_token_path):
        self.refresh_token_path = refresh_token_path

    def authenticate(self):
        return get_auth_stdin(self.refresh_token_path, manual_login=True)
