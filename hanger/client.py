import asyncio
import inspect

import hangups
from hangups.conversation import _sync_all_conversations
from hangups.hangouts_pb2 import StateUpdate, CONVERSATION_TYPE_GROUP

from hanger._authenticator import Authenticator
from hanger.cache import _Cache
from hanger.clientuser import ClientUser
from hanger.conversation import Conversation
from hanger.conversation_event import ChatMessageEvent, ParticipantJoinEvent, ParticipantLeaveEvent, \
    ParticipantKickEvent, ConversationRenameEvent, HangoutEvent, GroupLinkSharingEvent, OTRModificationEvent
from hanger.events import EventHandler
from hanger.http import HTTPClient
from hanger.presence import Presence
from hanger.user import User


class Client:
    def __init__(self, refresh_token):
        self._authenticator = Authenticator(refresh_token)
        self._hangups_client: hangups.Client = hangups.Client(self._authenticator.authenticate())
        self._event_handler: EventHandler = EventHandler(self)
        self._cache: _Cache = _Cache(self)
        self.http = HTTPClient(self._hangups_client)
        self.loop = asyncio.get_event_loop()

        for event_name, event_func in inspect.getmembers(self, predicate=inspect.ismethod):
            event_ = self._event_handler.events.get(event_name)
            if event_:
                self._event_handler.register_event(event_name, event_func)

        self._event_handler.register_event('on_connect', self._prepare)

    def event(self, func):
        self._event_handler.register_event(func.__name__, func)
        return func

    async def on_ready(self) -> None:
        pass

    async def on_connect(self) -> None:
        pass

    async def on_disconnect(self) -> None:
        pass

    async def on_reconnect(self) -> None:
        pass

    async def on_state_update(self, payload: StateUpdate) -> None:
        pass

    async def on_participant_leave(self, event: ParticipantLeaveEvent) -> None:
        pass

    async def on_participant_kick(self, event: ParticipantKickEvent) -> None:
        pass

    async def on_participant_join(self, event: ParticipantJoinEvent) -> None:
        pass

    async def on_conversation_rename(self, event: ConversationRenameEvent) -> None:
        pass

    async def on_hangout(self, event: HangoutEvent) -> None:
        pass

    async def on_group_link_sharing_modification(self, event: GroupLinkSharingEvent) -> None:
        pass

    async def on_history_modification(self, event: OTRModificationEvent) -> None:
        pass

    async def on_message(self, event: ChatMessageEvent) -> None:
        pass

    async def _prepare(self) -> None:
        self.me = await self.fetch_self_user()

        conv_states, _ = await _sync_all_conversations(self._hangups_client)
        for state in conv_states:
            await self._cache._update_cache(
                state.conversation
            )

        await self._event_handler.invoke_event('on_ready')

    async def _on_conversation_state_update(self, payload: StateUpdate) -> None:
        notification_type = payload.WhichOneof('state_update')

        if payload.HasField('conversation'):
            await self._cache._update_cache(
                payload.conversation
            )

        if notification_type == 'event_notification':
            await self._event_handler.handle_event(payload.event_notification.event)

    def connect(self) -> None:
        self.loop.run_until_complete(self._hangups_client.connect())

    async def disconnect(self) -> None:
        await self._hangups_client.disconnect()

    def get_user(self, user_id) -> User:
        return self._cache.get_user(user_id)

    def get_conversation(self, conversation_id) -> Conversation:
        return self._cache.get_conversation(conversation_id)

    async def fetch_user(self, user_id=None, email=None, phone=None) -> User:
        data = await self.http.fetch_user(user_id, email, phone)

        return User(self, data)

    async def fetch_conversation(self, conversation_id) -> Conversation:
        data = await self.http.fetch_conversation(conversation_id)

        return Conversation(self, data)

    async def create_private_conversation(self, user: User) -> Conversation:
        data = self.http.create_private_conversation(user.id)

        return Conversation(self, data)

    async def leave_conversation(self, conversation: Conversation) -> Conversation:
        if conversation.type == CONVERSATION_TYPE_GROUP:
            await self.http.leave_private_conversation(conversation.id)
        else:
            await self.http.leave_group_conversation(conversation._get_event_request_header())

        return self._cache.remove_conversation(conversation.id)

    async def rename_conversation(self, conversation: Conversation, name: str) -> None:
        await self.http.rename_conversation(conversation._get_event_request_header(), name)

    async def set_typing(self, conversation: Conversation, typing) -> None:
        await self.http.set_typing(conversation.id, typing.value)

    async def _update_presence(self, user: User):
        data = await self.http.fetch_presence(user.id)
        user.presence = Presence(data)

        return user

    async def set_focus(self, conversation, _type, timeout=10):
        data = await self.http.set_focus(conversation.id, _type.value, timeout)

        return data.timestamp

    async def fetch_self_user(self):
        data = await self.http.fetch_self_user()

        return ClientUser(self, data)
