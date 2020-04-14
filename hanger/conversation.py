from typing import Dict

from hangups.hangouts_pb2 import Conversation as HangupsConversation, EventRequestHeader, \
    OFF_THE_RECORD_STATUS_ON_THE_RECORD, OFF_THE_RECORD_STATUS_OFF_THE_RECORD, ConversationId, DeliveryMedium, \
    DELIVERY_MEDIUM_BABEL

from hanger.abc import Messageable
from hanger.context_managers import Typing, Focus
from hanger.enums import try_enum, ConversationType, ConversationHistoryStatus, ConversationHistoryToggleable, \
    NetworkType, ForceHistory, GroupLinkSharingStatus, TypingStatus, FocusType
from hanger.participant import Participant


class Conversation(Messageable):
    def __init__(self, client, data: HangupsConversation):
        self._client = client
        self._data: HangupsConversation = data

        self.typing_status: TypingStatus = TypingStatus.UNKNOWN

        self._update(data)

    def get_participant(self, id_) -> Participant:
        return self._participants.get(id_, None)

    async def rename(self, name: str) -> None:
        await self._client.rename_conversation(self, name)

    async def leave(self):
        return await self._client.leave_conversation(self)

    def typing(self):
        return Typing(self)

    async def set_typing(self, typing: TypingStatus) -> None:
        if typing == self.typing_status:
            return

        await self._client.set_typing(self, typing)
        self.typing_status = typing

    def focused(self):
        return Focus(self)

    async def focus(self, timeout=10):
        await self._client.set_focus(self, FocusType.FOCUSED, timeout)

    async def _get_conversation_id(self) -> ConversationId:
        return ConversationId(
            id=self.id
        )

    def _get_default_delivery_medium(self) -> DeliveryMedium:
        medium_options = (
            self._data.self_conversation_state.delivery_medium_option
        )
        try:
            default_medium = medium_options[0].delivery_medium
        except IndexError:
            default_medium = DeliveryMedium(
                medium_type=DELIVERY_MEDIUM_BABEL
            )

        for medium_option in medium_options:
            if medium_option.current_default:
                default_medium = medium_option.delivery_medium

        return default_medium

    def _get_event_request_header(self) -> EventRequestHeader:
        """Return EventRequestHeader for conversation."""
        if self.otr_status == ConversationHistoryStatus.ON:
            otr_status = OFF_THE_RECORD_STATUS_ON_THE_RECORD
        else:
            otr_status = OFF_THE_RECORD_STATUS_OFF_THE_RECORD

        return EventRequestHeader(
            conversation_id=ConversationId(id=self.id),
            client_generated_id=self._client._hangups_client.get_client_generated_id(),
            expected_otr=otr_status,
            delivery_medium=self._get_default_delivery_medium(),
        )

    # TODO: Implement `read_state` & `self_conversation_state`
    def _update(self, data: HangupsConversation) -> None:
        # We need this in order to allow `Client._sync`
        conversation = data

        self.id: str = getattr(getattr(conversation, 'conversation_id', None), 'id', None)
        self.type: ConversationType = try_enum(ConversationType, getattr(conversation, 'type', None))
        self.name: str = getattr(conversation, 'name', None)
        self.has_active_hangout: bool = getattr(conversation, 'has_active_hangout', None)
        self.otr_status: ConversationHistoryStatus = try_enum(ConversationHistoryStatus, getattr(conversation, 'otr_status', None))
        self.otr_toggleable: ConversationHistoryToggleable = try_enum(ConversationHistoryToggleable, getattr(conversation, 'otr_toggle', None))
        self.conversation_history_supported: bool = getattr(conversation, 'conversation_history_supported', None)

        if not hasattr(self, '_participants'):
            self._participants: Dict[str, Participant] = {}

        for participant_data in getattr(conversation, 'participant_data', []):
            user = self._client._cache.get_user(participant_data.id.gaia_id)
            participant = self.get_participant(user.id)

            if participant:
                participant._update_participant(participant_data)
            else:
                self._participants[user.id] = Participant(self._client._cache, user._data, participant_data, self)

        self.network_type: NetworkType = try_enum(NetworkType, getattr(conversation, 'network_type', None))
        self.force_history_state: ForceHistory = try_enum(ForceHistory,
                                                          getattr(conversation, 'force_history_state', None))
        self.group_link_sharing_status: GroupLinkSharingStatus = try_enum(GroupLinkSharingStatus,
                                                                          getattr(conversation,
                                                                                  'group_link_sharing_status', None))
