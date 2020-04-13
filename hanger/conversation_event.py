from hangups import parsers, hangouts_pb2, ChatMessageSegment
from hangups.client import logger

from hanger.enums import try_enum, GroupLinkSharingStatus, ConversationHistoryToggleable, ConversationHistoryStatus


class ConversationEvent:
    def __init__(self, event, user, conversation):
        self._event = event
        self.user = user
        self.conversation = conversation

    @property
    def timestamp(self):
        return parsers.from_timestamp(self._event.timestamp)

    @property
    def event_id(self):
        return self._event.event_id


class ChatMessageEvent(ConversationEvent):
    @property
    def text(self):
        txt = ''
        for segment in self._segments:
            if segment.type_ == hangouts_pb2.SEGMENT_TYPE_LINE_BREAK:
                txt += '\n'
            else:
                txt += segment.text

        return txt

    @property
    def _segments(self):
        """List of :class:`ChatMessageSegment` in message (:class:`list`)."""
        seg_list = self._event.chat_message.message_content.segment
        return [ChatMessageSegment.deserialize(seg) for seg in seg_list]

    @property
    def attachments(self):
        """List of attachments in the message (:class:`list`)."""
        raw_attachments = self._event.chat_message.message_content.attachment
        if raw_attachments is None:
            raw_attachments = []
        attachments = []
        for attachment in raw_attachments:
            for embed_item_type in attachment.embed_item.type:
                known_types = [
                    hangouts_pb2.ITEM_TYPE_PLUS_PHOTO,
                    hangouts_pb2.ITEM_TYPE_PLACE_V2,
                    hangouts_pb2.ITEM_TYPE_PLACE,
                    hangouts_pb2.ITEM_TYPE_THING,
                ]
                if embed_item_type not in known_types:
                    logger.warning('Received chat message attachment with '
                                   'unknown embed type: %r', embed_item_type)

            if attachment.embed_item.HasField('plus_photo'):
                attachments.append(
                    attachment.embed_item.plus_photo.thumbnail.image_url
                )
        return attachments


class MembershipChangeEvent(ConversationEvent):
    def __init__(self, event, user, conversation, participants):
        super().__init__(event, user, conversation)

        self.participants = participants


class ParticipantJoinEvent(MembershipChangeEvent):
    pass


class ParticipantLeaveEvent(MembershipChangeEvent):
    pass


class ParticipantKickEvent(MembershipChangeEvent):
    def __init__(self, event, user, conversation, participants):
        super().__init__(event, user, conversation, participants)
        self.kicker = self.user
        self.kicked = participants

        del self.user
        del self.participants


class ConversationRenameEvent(ConversationEvent):
    @property
    def new_name(self) -> str:
        return self._event.conversation_rename.new_name

    @property
    def old_name(self) -> str:
        return self._event.conversation_rename.old_name


class HangoutEvent(ConversationEvent):
    def __init__(self, event, user, conversation, participants):
        super().__init__(event, user, conversation)

        self.participants = participants


class GroupLinkSharingEvent(ConversationEvent):
    @property
    def new_status(self):
        return try_enum(GroupLinkSharingStatus, self._event.group_link_sharing_modification.new_status)


class OTRModificationEvent(ConversationEvent):
    @property
    def old_otr_status(self):
        return try_enum(ConversationHistoryStatus, self._event.otr_modification.old_otr_status)

    @property
    def new_otr_status(self):
        return try_enum(ConversationHistoryStatus, self._event.otr_modification.new_otr_status)

    @property
    def old_otr_toggle(self):
        return try_enum(ConversationHistoryToggleable, self._event.otr_modification.old_otr_toggle)

    @property
    def new_otr_toggle(self):
        return try_enum(ConversationHistoryToggleable, self._event.otr_modification.new_otr_toggle)
