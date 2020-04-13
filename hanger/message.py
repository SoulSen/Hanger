from typing import List

from hangups import ChatMessageSegment
from hangups.hangouts_pb2 import MessageContent

from hanger.abc import HangupsObject


class Message(HangupsObject):
    def __init__(self, text: str):
        self.text: str = text
        self._segment: List[ChatMessageSegment] = ChatMessageSegment.from_str(text)

    def _build_hangups_object(self) -> MessageContent:
        for index, segment in enumerate(self._segment):
            self._segment[index] = segment.serialize()

        return MessageContent(
            segment=self._segment
        )
