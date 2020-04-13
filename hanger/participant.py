from hanger.enums import try_enum, InvitationStatus
from hanger.user import User
import hanger


class Participant(User):
    def __init__(self, cache, data, conversation_data, conversation):
        self._conversation_data = conversation_data
        self.conversation: hanger.Conversation = conversation

        super().__init__(cache, data)
        self._update_participant(self._conversation_data)

    def _update(self, data):
        super()._update(data)

    def _update_participant(self, participant_data):
        self.fallback_name: str = getattr(participant_data, 'fallback_name', None)
        self.invitation_status: InvitationStatus = try_enum(InvitationStatus,
                                                            getattr(participant_data, 'invitation_status', None))
