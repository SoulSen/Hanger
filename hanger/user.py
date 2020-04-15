from collections import namedtuple

from hangups.hangouts_pb2 import GetEntityByIdResponse

from .abc import Messageable
from .enums import try_enum, Gender, ProfileType, PhotoUrlStatus, UserType, PastHangoutState, ConversationType, \
    PhoneVerificationStatus, PhoneDiscoverabilityStatus
from .presence import Presence

country = namedtuple('Country', ['region_code', 'country_code'])
phone = namedtuple('Phone', ['phone_number', 'google_voice', 'verification_status',
                             'discoverable', 'discoverable_status', 'primary'])


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
                    any(participant_id == self.id for participant_id in conversation._participants):
                return (await conversation._get_conversation_id())

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


class ClientUser(User):
    def __init__(self, client, data):
        super().__init__(client, data)

    def _update(self, data) -> None:
        super()._update(getattr(data, 'self_entity'))

        self.is_known_minor = getattr(data, 'is_known_minor')
        self.dnd_state = getattr(data, 'dnd_state')
        self.desktop_off_setting = getattr(data, 'desktop_off_setting')

        phone_data = getattr(data, 'phone_data')

        self.phone = [phone(getattr(getattr(_phone, 'phone_number'), 'e164'),
                            getattr(_phone, 'google_voice'),
                            try_enum(PhoneVerificationStatus, getattr(_phone, 'verification_status')),
                            getattr(_phone, 'discoverable'),
                            try_enum(PhoneDiscoverabilityStatus, getattr(_phone, 'discoverability_status')),
                            getattr(_phone, 'primary')) for _phone in getattr(phone_data, 'phone')]

        self.configuration_bit = getattr(data, 'configuration_bit')
        self.google_plus_user = getattr(data, 'google_plus_user')
        self.desktop_sound_setting = getattr(data, 'desktop_sound_setting')
        self.rich_presence_state = getattr(data, 'rich_presence_state')

        default_country = getattr(data, 'default_country')

        self.default_country = country(getattr(default_country, 'region_code'),
                                       getattr(default_country, 'country_code'))
