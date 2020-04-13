import types
from collections import namedtuple
from typing import Type


def _create_value_cls(name):
    cls = namedtuple('_EnumValue_' + name, 'name value')
    cls.__repr__ = lambda self: '<%s.%s: %r>' % (name, self.name, self.value)
    cls.__str__ = lambda self: '%s.%s' % (name, self.name)
    return cls


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class EnumMeta(type):
    def __new__(cls, name, bases, attrs):
        value_mapping = {}
        member_mapping = {}
        member_names = []

        value_cls = _create_value_cls(name)
        for key, value in list(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == '_' and not is_descriptor:
                continue

            # Special case classmethod to just pass through
            if isinstance(value, classmethod):
                continue

            if is_descriptor:
                setattr(value_cls, key, value)
                del attrs[key]
                continue

            try:
                new_value = value_mapping[value]
            except KeyError:
                new_value = value_cls(name=key, value=value)
                value_mapping[value] = new_value
                member_names.append(key)

            member_mapping[key] = new_value
            attrs[key] = new_value

        attrs['_enum_value_map_'] = value_mapping
        attrs['_enum_member_map_'] = member_mapping
        attrs['_enum_member_names_'] = member_names
        actual_cls = super().__new__(cls, name, bases, attrs)
        value_cls._actual_enum_cls_ = actual_cls
        return actual_cls

    def __iter__(cls):
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)

    def __reversed__(cls):
        return (cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_))

    def __len__(cls):
        return len(cls._enum_member_names_)

    def __repr__(cls):
        return '<enum %r>' % cls.__name__

    @property
    def __members__(cls):
        return types.MappingProxyType(cls._enum_member_map_)

    def __call__(cls, value):
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))

    def __getitem__(cls, key):
        return cls._enum_member_map_[key]

    def __setattr__(cls, name, value):
        raise TypeError('Enums are immutable.')

    def __delattr__(cls, attr):
        raise TypeError('Enums are immutable')

    def __instancecheck__(self, instance):
        # isinstance(x, Y)
        # -> __instancecheck__(Y, x)
        try:
            return instance._actual_enum_cls_ is self
        except AttributeError:
            return False


class Enum(metaclass=EnumMeta):
    @classmethod
    def try_value(cls, value):
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            return value


class Gender(Enum):
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2


class PhotoUrlStatus(Enum):
    UNKNOWN = 0
    PLACEHOLDER = 1
    USER_PHOTO = 2


class ProfileType(Enum):
    NONE = 0
    ES_USER = 1


class UserType(Enum):
    UNKNOWN = 0
    GAIA = 2
    GOOGLE_VOICE = 3


class PastHangoutState(Enum):
    UNKNOWN = 0
    HAD_PAST_HANGOUT = 1
    NO_PAST_HANGOUT = 2


class ConversationType(Enum):
    UNKNOWN = 0
    ONE_TO_ONE = 1
    GROUP = 2


class ConversationHistoryStatus(Enum):
    UNKNOWN = 0
    OFF = 1
    ON = 2


class ConversationHistoryToggleable(Enum):
    UNKNOWN = 0
    ENABLED = 1
    DISABLED = 2


class InvitationStatus(Enum):
    UNKNOWN = 0
    PENDING = 1
    ACCEPTED = 2


class NetworkType(Enum):
    UNKNOWN = 0
    BABEL = 1
    GOOGLE_VOICE = 2


class ForceHistory(Enum):
    UNKNOWN = 0
    NO = 1


class GroupLinkSharingStatus(Enum):
    UNKNOWN = 0
    ON = 1
    OFF = 2


class TypingStatus(Enum):
    UNKNOWN = 0
    STARTED = 1
    PAUSED = 2
    STOPPED = 3


class DeviceStatus(Enum):
    UNKNOWN = None
    MOBILE = 1
    DESKTOP = 2
    TABLET = 3


class FocusType(Enum):
    UNKNOWN = 0
    FOCUSED = 1
    UNFOCUSED = 2


def try_enum(cls: Type[Enum], val):
    """A function that tries to turn the value into enum ``cls``.
    If it fails it returns the value instead.
    """

    try:
        return cls._enum_value_map_[val]
    except (KeyError, TypeError, AttributeError):
        return val
