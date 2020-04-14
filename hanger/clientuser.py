from collections import namedtuple

from hanger.enums import try_enum, PhoneVerificationStatus, PhoneDiscoverabilityStatus
from hanger.user import User

country = namedtuple('Country', ['region_code', 'country_code'])
phone = namedtuple('Phone', ['phone_number', 'google_voice', 'verification_status',
                             'discoverable', 'discoverable_status', 'primary'])


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
