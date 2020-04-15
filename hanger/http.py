from datetime import datetime, timezone

from hangups import parsers
from hangups.hangouts_pb2 import GetConversationRequest, ConversationSpec, ConversationId, CreateConversationRequest, \
    CONVERSATION_TYPE_ONE_TO_ONE, InviteeID, RemoveUserRequest, DeleteConversationRequest, \
    RenameConversationRequest, QueryPresenceRequest, ParticipantId, FIELD_MASK_REACHABLE, FIELD_MASK_AVAILABLE, \
    FIELD_MASK_MOOD, FIELD_MASK_DEVICE, FIELD_MASK_LAST_SEEN, SetFocusRequest, GetSelfInfoRequest, GetEntityByIdRequest, \
    EntityLookupSpec, SetTypingRequest, AddUserRequest


class HTTPClient:
    def __init__(self, hangups_client):
        self._client = hangups_client

    async def fetch_user(self, user_id=None, email=None, phone=None):
        data = await self._client.get_entity_by_id(GetEntityByIdRequest(
            request_header=self._client.get_request_header(),
            batch_lookup_spec=[
                EntityLookupSpec(
                    gaia_id=user_id,
                    email=email,
                    phone=phone
                )
            ]
        ))

        return data.entity[0] or None

    async def fetch_conversation(self, conversation_id):
        data = await self._client.get_conversation(GetConversationRequest(
            request_header=self._client.get_request_header(),
            conversation_spec=ConversationSpec(
                conversation_id=ConversationId(
                    id=conversation_id
                )
            )
        ))

        return data.conversation_state.conversation

    async def create_private_conversation(self, user_id):
        data = await self._client.create_conversation(CreateConversationRequest(
            request_header=self._client.get_request_header(),
            type=CONVERSATION_TYPE_ONE_TO_ONE,
            invitee_id=[
                InviteeID(
                    gaia_id=user_id
                )
            ],
            client_generated_id=self._client.get_client_generated_id()
        ))

        return data.conversation

    async def leave_group_conversation(self, request_header):
        await self._client.remove_user(RemoveUserRequest(
            request_header=self._client.get_request_header(),
            event_request_header=request_header
        ))

    async def leave_private_conversation(self, conversation_id):
        await self._client.delete_conversation(DeleteConversationRequest(
            request_header=self._client.get_request_header(),
            conversation_id=conversation_id,
            delete_upper_bound_timestamp=parsers.to_timestamp(
                datetime.now(tz=timezone.utc)
            )
        ))

    async def rename_conversation(self, request_header, name: str):
        await self._client.rename_conversation(RenameConversationRequest(
            request_header=self._client.get_request_header(),
            new_name=name,
            event_request_header=request_header
        ))

    async def set_typing(self, conversation_id, typing):
        await self._client.set_typing(SetTypingRequest(
            request_header=self._client.get_request_header(),
            conversation_id=conversation_id,
            type=typing
        ))

    async def fetch_presence(self, user_id):
        data = await self._client.query_presence(QueryPresenceRequest(
            request_header=self._client.get_request_header(),
            participant_id=[
                ParticipantId(
                    gaia_id=user_id
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
        return getattr(presence_result, 'presence', None)

    async def set_focus(self, conversation_id, _type, timeout=10):
        data = await self._client.set_focus(SetFocusRequest(
            request_header=self._client.get_request_header(),
            conversation_id=ConversationId(
                id=conversation_id
            ),
            type=_type,
            timeout_secs=timeout
        ))

        return data.timestamp

    async def fetch_self_user(self):
        data = await self._client.get_self_info(GetSelfInfoRequest(
            request_header=self._client.get_request_header()
        ))

        return data

    async def remove_user_conversation(self, request_header, user_id):
        await self._client.remove_user(RemoveUserRequest(
            request_header=request_header,
            participant_id=user_id
        ))

    async def add_user_conversation(self, request_header, user_id):
        await self._client.add_user(AddUserRequest(
            request_header=request_header,
            participant_id=user_id
        ))
