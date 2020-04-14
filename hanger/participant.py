from hanger.enums import try_enum, InvitationStatus
from hanger.user import User


class Participant(User):
    def __init__(self, client, data, participant_data, conversation):
        self._participant_data = participant_data
        self.conversation = conversation

        super().__init__(client, data)
        self._update_participant(self._participant_data)

    def _update(self, data):
        super()._update(data)

    def _update_participant(self, participant_data):
        self.fallback_name: str = getattr(participant_data, 'fallback_name', None)
        self.invitation_status: InvitationStatus = try_enum(InvitationStatus,
                                                            getattr(participant_data, 'invitation_status', None))
