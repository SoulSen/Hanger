from datetime import datetime, timezone

import hangups
from hangups import parsers
from hangups.hangouts_pb2 import StateUpdate, GetEntityByIdRequest, EntityLookupSpec, GetConversationRequest, \
    ConversationSpec, ConversationId, CreateConversationRequest, CONVERSATION_TYPE_ONE_TO_ONE, InviteeID, \
    MEMBERSHIP_CHANGE_TYPE_JOIN, RemoveUserRequest, DeleteConversationRequest, CONVERSATION_TYPE_GROUP, \
    RenameConversationRequest, SetTypingRequest, TYPING_TYPE_STARTED, TYPING_TYPE_PAUSED, \
    TYPING_TYPE_STOPPED, TYPING_TYPE_UNKNOWN, QueryPresenceRequest, ParticipantId, FIELD_MASK_LAST_SEEN, \
    FIELD_MASK_DEVICE, FIELD_MASK_MOOD, FIELD_MASK_AVAILABLE, FIELD_MASK_REACHABLE, SetFocusRequest

from hanger.cache import _Cache
from hanger.conversation import Conversation
from hanger.conversation_event import ChatMessageEvent, ParticipantJoinEvent, ParticipantLeaveEvent, \
    ParticipantKickEvent, ConversationRenameEvent, HangoutEvent, GroupLinkSharingEvent, OTRModificationEvent
from hanger.enums import TypingStatus
from hanger.events import EventHandler
from hanger.presence import Presence
from hanger.user import User


class Client:
    def __init__(self, cookies):
        self._hangups_client: hangups.Client = hangups.Client(cookies)
        self._event_handler: EventHandler = EventHandler(self._hangups_client)
        self._cache: _Cache = _Cache(self)
        self._session = None

        self._event_handler.create_event('on_message')
        self._event_handler.create_event('on_ready')
        self._event_handler.create_event('on_participant_leave')
        self._event_handler.create_event('on_participant_kick')
        self._event_handler.create_event('on_participant_join')
        self._event_handler.create_event('on_conversation_rename')
        self._event_handler.create_event('on_hangout')
        self._event_handler.create_event('on_group_link_sharing_modification')
        self._event_handler.create_event('on_history_modification')

        self._event_handler.register_event('on_connect', self.on_ready)
        self._event_handler.register_event('on_disconnect', self.on_reconnect)
        self._event_handler.register_event('on_reconnect', self.on_reconnect)
        self._event_handler.register_event('on_participant_leave', self.on_participant_leave)
        self._event_handler.register_event('on_participant_kick', self.on_participant_kick)
        self._event_handler.register_event('on_participant_join', self.on_participant_join)
        self._event_handler.register_event('on_state_update', self.on_state_update)
        self._event_handler.register_event('on_state_update', self._on_conversation_state_update)
        self._event_handler.register_event('on_message', self.on_message)
        self._event_handler.register_event('on_conversation_rename', self.on_conversation_rename)
        self._event_handler.register_event('on_hangout', self.on_hangout)
        self._event_handler.register_event('on_group_link_sharing_modification',
                                           self.on_group_link_sharing_modification)
        self._event_handler.register_event('on_history_modification',
                                           self.on_history_modification)

    def event(self, func):
        self._event_handler.register_event(func.__name__, func)
        return func

    async def on_ready(self) -> None:
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

    async def _on_conversation_state_update(self, payload: StateUpdate) -> None:
        notification_type = payload.WhichOneof('state_update')

        if payload.HasField('conversation'):
            await self._update_users(
                payload.conversation
            )
            await self._update_conversation(
                payload.conversation
            )

        if notification_type == 'event_notification':
            event_ = payload.event_notification.event

            conversation = self._cache.get_conversation(event_.conversation_id.id)
            user = conversation.get_participant(event_.sender_id.gaia_id)

            if event_.HasField('chat_message'):
                await self._event_handler.invoke_event('on_message', ChatMessageEvent(event_, user, conversation))

            elif event_.HasField('membership_change'):
                if event_.membership_change.type == MEMBERSHIP_CHANGE_TYPE_JOIN:
                    participants = [conversation.get_participant(user.gaia_id) for user in
                                    event_.membership_change.participant_ids]

                    await self._event_handler.invoke_event('on_participant_join',
                                                           ParticipantJoinEvent(event_, user,
                                                                                conversation, participants))
                else:
                    participants = [(await self.fetch_user(gaia_id=user.gaia_id)) for user in
                                    event_.membership_change.participant_ids]

                    if user in participants:
                        await self._event_handler.invoke_event('on_participant_leave',
                                                               ParticipantLeaveEvent(event_, user,
                                                                                     conversation, participants))
                    else:
                        await self._event_handler.invoke_event('on_participant_kick',
                                                               ParticipantKickEvent(event_, user,
                                                                                    conversation, participants))

                    # Prevent invalid caching
                    for user in participants:
                        try:
                            self._cache.remove_user(user.id)
                        except KeyError:
                            pass

            elif event_.HasField('conversation_rename'):
                await self._event_handler.invoke_event('on_conversation_rename',
                                                       ConversationRenameEvent(event_.conversation_rename,
                                                                               user, conversation))

            elif event_.HasField('hangout_event'):
                participants = [conversation.get_participant(user.gaia_id)
                                for user in event_.membership_change.participant_ids]
                await self._event_handler.invoke_event('on_hangout',
                                                       HangoutEvent(event_, user, conversation, participants))

            elif event_.HasField('group_link_sharing_modification'):
                await self._event_handler.invoke_event('on_group_link_sharing_modification',
                                                       GroupLinkSharingEvent(event_, user, conversation))

            elif event_.HasField('otr_modification'):
                await self._event_handler.invoke_event('on_history_modification',
                                                       OTRModificationEvent(event_, user, conversation))

    async def _update_users(self, payload: StateUpdate) -> None:
        for participant in payload.participant_data:
            user_id = participant.id.gaia_id
            user = self._cache.get_user(user_id)

            if not user:
                user = await self.fetch_user(gaia_id=user_id)
                self._cache.store_user(user)
            else:
                _updated_user = await self.fetch_user(gaia_id=user_id)
                user._update(_updated_user._data)

            await self._update_presence(user)

    async def _update_conversation(self, payload: StateUpdate) -> None:
        conversation_id = payload.conversation_id.id
        conversation = self._cache.get_conversation(conversation_id)

        if conversation is None:
            conversation = await self.fetch_conversation(conversation_id)
            self._cache.store_conversation(conversation)
        else:
            _updated_conversation = await self.fetch_conversation(conversation_id)
            conversation._update(_updated_conversation._data)

    async def fetch_user(self, **kwargs) -> User:
        data = await self._hangups_client.get_entity_by_id(GetEntityByIdRequest(
            request_header=self._hangups_client.get_request_header(),
            batch_lookup_spec=[
                EntityLookupSpec(
                    **kwargs
                )
            ]
        ))

        return User(self, data)

    async def fetch_conversation(self, id_) -> Conversation:
        data = await self._hangups_client.get_conversation(GetConversationRequest(
            request_header=self._hangups_client.get_request_header(),
            conversation_spec=ConversationSpec(
                conversation_id=ConversationId(
                    id=str(id_)
                )
            )
        ))

        return Conversation(self, data.conversation_state.conversation)

    async def create_private_conversation(self, user: User) -> Conversation:
        data = await self._hangups_client.create_conversation(CreateConversationRequest(
            request_header=self._hangups_client.get_request_header(),
            type=CONVERSATION_TYPE_ONE_TO_ONE,
            invitee_id=[
                InviteeID(
                    gaia_id=str(user.id)
                )
            ],
            client_generated_id=self._hangups_client.get_client_generated_id()
        ))

        return Conversation(self, data.conversation)

    async def leave_conversation(self, conversation: Conversation) -> Conversation:
        if conversation.type == CONVERSATION_TYPE_GROUP:
            await self._hangups_client.remove_user(RemoveUserRequest(
                request_header=self._hangups_client.get_request_header(),
                event_request_header=conversation._get_event_request_header()
            ))
        else:
            await self._hangups_client.delete_conversation(DeleteConversationRequest(
                request_header=self._hangups_client.get_request_header(),
                conversation_id=conversation._get_conversation_id(),
                delete_upper_bound_timestamp=parsers.to_timestamp(
                    datetime.now(tz=timezone.utc)
                )
            ))
        return self._cache.remove_conversation(conversation.id)

    async def rename_conversation(self, conversation: Conversation, name: str) -> None:
        await self._hangups_client.rename_conversation(RenameConversationRequest(
            request_header=self._hangups_client.get_request_header(),
            new_name=name,
            event_request_header=conversation._get_event_request_header()
        ))

    async def set_typing(self, conversation: Conversation, typing: TypingStatus) -> None:
        aliases = {TypingStatus.STARTED: TYPING_TYPE_STARTED, TypingStatus.PAUSED: TYPING_TYPE_PAUSED,
                   TypingStatus.STOPPED: TYPING_TYPE_STOPPED, TypingStatus.UNKNOWN: TYPING_TYPE_UNKNOWN}

        await self._hangups_client.set_typing(SetTypingRequest(
            request_header=self._hangups_client.get_request_header(),
            conversation_id=conversation._get_conversation_id(),
            type=aliases[typing]
        ))

    async def _update_presence(self, user: User):
        data = await self._hangups_client.query_presence(QueryPresenceRequest(
            request_header=self._hangups_client.get_request_header(),
            participant_id=[
                ParticipantId(
                    gaia_id=user.id
                )
            ],
            field_mask=[
                FIELD_MASK_REACHABLE,
                FIELD_MASK_AVAILABLE,
                FIELD_MASK_MOOD,
                FIELD_MASK_DEVICE,
                FIELD_MASK_LAST_SEEN,
            ]
        ))

        presence_result = getattr(data, 'presence_result', None)[0]
        user.presence = Presence(getattr(presence_result, 'presence', None))
        return user

    async def set_focus(self, conversation, _type, timeout=10):
        data = await self._hangups_client.set_focus(SetFocusRequest(
            request_header=self._hangups_client.get_request_header(),
            conversation_id=ConversationId(
                id=conversation.id
            ),
            type=_type,
            timeout_secs=timeout
        ))

        return data.timestamp
