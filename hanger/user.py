from hangups.hangouts_pb2 import GetEntityByIdResponse

from .abc import Messageable
from .enums import try_enum, Gender, ProfileType, PhotoUrlStatus, UserType, PastHangoutState, ConversationType
from .presence import Presence


class User(Messageable):
    def __init__(self, client, data: GetEntityByIdResponse):
        self._client = client
        self._data = data
        self._update(self._data)

    async def block(self):
        raise NotImplementedError

    async def archive(self):
        raise NotImplementedError

    async def _get_conversation_id(self):
        for conversation in self._client._cache.get_all_conversations():
            if conversation.type == ConversationType.ONE_TO_ONE and \
                    any(participant.id == self.id for participant in conversation.participants):
                return conversation._get_conversation_id()

        return (await self._client.create_private_conversation(self))._get_conversation_id()

    def _update(self, data) -> None:
        properties = getattr(data, 'properties', None)

        self.user_type = try_enum(UserType, getattr(data, 'entity_type', None))

        self.had_past_hangout_state = try_enum(PastHangoutState, getattr(data, 'had_past_hangout_state', None))
        self.presence = Presence(getattr(data, 'presence', None))

        self.id = getattr(getattr(data, 'id', None), 'gaia_id', None)
        self.type = try_enum(ProfileType, getattr(properties, 'type', None))
        self.display_name = getattr(properties, 'display_name', None)
        self.first_name = getattr(properties, 'first_name', None)
        self.photo_url = getattr(properties, 'photo_url', None)

        if self.photo_url:
            self.photo_url = 'https:' + self.photo_url

        self.in_users_domain = getattr(properties, 'in_users_domain', None)
        self.gender = try_enum(Gender, getattr(properties, 'gender', None))
        self.photo_url_status = try_enum(PhotoUrlStatus, getattr(properties, 'photo_url_status', None))
        self.canonical_email = getattr(properties, 'canonical_email', None)
