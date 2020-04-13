from typing import List

from hanger.conversation import Conversation
from hanger.user import User


class _Cache:
    def __init__(self, client):
        self._client = client
        self._conversations = {}
        self._users = {}

    def get_user(self, id_) -> User:
        return self._users.get(id_, None)

    def get_all_users(self) -> List[User]:
        return list(self._users.values())

    def get_conversation(self, id_) -> Conversation:
        return self._conversations.get(id_, None)

    def get_all_conversations(self) -> List[Conversation]:
        return list(self._conversations.values())

    def store_user(self, user: User) -> User:
        self._users[user.id] = user

        return user

    def store_conversation(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.id] = conversation

        return conversation

    def remove_user(self, id_) -> User:
        return self._users.pop(id_)

    def remove_conversation(self, id_) -> Conversation:
        return self._conversations.pop(id_)

    async def _get_or_fetch_conversation(self, id_) -> Conversation:
        conversation = self._conversations.get(id_, None)

        if not conversation:
            return self.store_conversation(
                (await self._client.fetch_conversation(id_))
            )
        else:
            return conversation

    async def _get_or_fetch_user(self, id_) -> User:
        user = self._users.get(id_, None)

        if not user:
            return self.store_user(
                (await self._client.fetch_user(gaia_id=str(id_)))
            )
        else:
            return user
