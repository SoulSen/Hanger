from hangups import parsers, ChatMessageSegment


class Presence:
    def __init__(self, data):
        self._data = data

        self._update(data)

    def _update(self, data) -> None:
        self.reachable = getattr(data, 'reachable', None)
        self.available = getattr(data, 'available', None)

        device_status = getattr(data, 'device_status', None)

        self.mobile = getattr(device_status, 'mobile', None)
        self.desktop = getattr(device_status, 'desktop', None)
        self.tablet = getattr(device_status, 'tablet', None)

        mood_message = getattr(data, 'mood_message', None)
        mood_content = getattr(mood_message, 'mood_content', None)
        segment = getattr(mood_content, 'segment', None)
        mood_segment = [ChatMessageSegment.deserialize(segment) for segment in segment]

        self.mood_message = [segment.text for segment in mood_segment]

        last_seen = getattr(data, 'last_seen', None)

        self.last_seen = parsers.from_timestamp(getattr(last_seen, 'last_seen_timestamp_usec', None))
        self.since_last_seen = getattr(last_seen, 'usec_since_last_seen', None) // 1000000
