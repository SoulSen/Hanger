from typing import Callable

from hangups import event, MEMBERSHIP_CHANGE_TYPE_JOIN

from hanger.conversation_event import ChatMessageEvent, ParticipantJoinEvent, ParticipantLeaveEvent, \
    ParticipantKickEvent, ConversationRenameEvent, HangoutEvent, OTRModificationEvent, GroupLinkSharingEvent


class EventHandler:
    def __init__(self, client):
        self._client = client

        self.aliases = {'on_ready': 'on_connect'}

        self.events = {'on_connect': self._client._hangups_client.on_connect,
                       'on_disconnect': self._client._hangups_client.on_disconnect,
                       'on_state_update': self._client._hangups_client.on_state_update,
                       'on_reconnect': self._client._hangups_client.on_reconnect}

        self.create_event('on_message',
                          'on_participant_leave',
                          'on_participant_kick',
                          'on_participant_join',
                          'on_conversation_rename',
                          'on_hangout',
                          'on_group_link_sharing_modification',
                          'on_history_modification')

    def register_event(self, event_name: str, hook: Callable):
        event_name = self.aliases.get(event_name) or event_name

        event_ = self.events.get(event_name)
        if event_:
            event_.add_observer(hook)

    def create_event(self, *event_name: str) -> None:
        for event_ in event_name:
            self.events[event_] = event.Event('hanger.{}'.format(event_name))

    async def invoke_event(self, event_name: str, *args, **kwargs) -> None:
        event_name = self.aliases.get(event_name) or event_name

        event_ = self.events.get(event_name)
        if event_:
            await event_.fire(*args, **kwargs)

    def get_hooks(self, event_name: str) -> Callable:
        event_name = self.aliases.get(event_name) or event_name

        return self.events.get(event_name)._observers

    async def handle_event(self, event_):
        conversation = self._client.get_conversation(event_.conversation_id.id)
        user = conversation.get_participant(event_.sender_id.gaia_id)

        if event_.HasField('chat_message'):
            await self.invoke_event('on_message', ChatMessageEvent(event_, user, conversation))

        elif event_.HasField('membership_change'):
            if event_.membership_change.type == MEMBERSHIP_CHANGE_TYPE_JOIN:
                participants = [conversation.get_participant(user.gaia_id) for user in
                                event_.membership_change.participant_ids]

                await self.invoke_event('on_participant_join',
                                        ParticipantJoinEvent(event_, user,
                                                             conversation, participants))
            else:
                participants = [(await self._client.fetch_user(user.gaia_id)) for user in
                                event_.membership_change.participant_ids]

                if user in participants:
                    await self.invoke_event('on_participant_leave',
                                            ParticipantLeaveEvent(event_, user,
                                                                  conversation, participants))
                else:
                    await self.invoke_event('on_participant_kick',
                                            ParticipantKickEvent(event_, user,
                                                                 conversation, participants))

                # Prevent invalid caching
                for user in participants:
                    try:
                        self._client._cache.remove_user(user.id)
                    except KeyError:
                        pass

        elif event_.HasField('conversation_rename'):
            await self.invoke_event('on_conversation_rename',
                                    ConversationRenameEvent(event_.conversation_rename,
                                                            user, conversation))

        elif event_.HasField('hangout_event'):
            participants = [conversation.get_participant(user.gaia_id)
                            for user in event_.membership_change.participant_ids]
            await self.invoke_event('on_hangout',
                                    HangoutEvent(event_, user, conversation, participants))

        elif event_.HasField('group_link_sharing_modification'):
            await self.invoke_event('on_group_link_sharing_modification',
                                    GroupLinkSharingEvent(event_, user, conversation))

        elif event_.HasField('otr_modification'):
            await self.invoke_event('on_history_modification',
                                    OTRModificationEvent(event_, user, conversation))
