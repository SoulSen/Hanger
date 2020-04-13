import abc

from hangups.hangouts_pb2 import SendChatMessageRequest, EventRequestHeader, \
    EventAnnotation, ConversationId, ExistingMedia

import hanger


class Messageable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def _get_conversation_id(self) -> ConversationId:
        raise NotImplementedError

    async def send(self, text='', location=None, image=None, me=False) -> None:
        if me:
            me = 4
        else:
            me = 2

        if location:
            location = location._build_hangups_object()

        if image:
            image = await image._build_hangups_object()

        conversation_id = await self._get_conversation_id()
        text = hanger.Message(text)._build_hangups_object()

        request = SendChatMessageRequest(
            request_header=self._client._hangups_client.get_request_header(),
            event_request_header=EventRequestHeader(
                conversation_id=conversation_id,
                client_generated_id=self._client._hangups_client.get_client_generated_id()
            ),
            message_content=text,
            annotation=[
                EventAnnotation(
                    type=me
                )
            ],
            existing_media=ExistingMedia(
                photo=image
            ),
            location=location
        )

        await self._client._hangups_client.send_chat_message(request)


class HangupsObject(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def _build_hangups_object(self):
        raise NotImplementedError
