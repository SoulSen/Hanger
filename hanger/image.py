from hangups.hangouts_pb2 import Photo

from hanger.abc import HangupsObject


class Image(HangupsObject):
    def __init__(self, _client, file, filename=None):
        self._client = _client
        self.file = file
        self.filename = filename

        self.uploaded = False

    async def _build_hangups_object(self):
        image = await self._client._hangups_client.upload_image(
            self.file, filename=self.filename, return_uploaded_image=True
        )

        self.uploaded = True

        return Photo(
            photo_id=image.image_id
        )
