from hangups.hangouts_pb2 import Location as HangupsLocation, ItemType
from hangups.hangouts_pb2 import Place, EmbedItem
import hangups

from hanger.abc import HangupsObject


class Location(HangupsObject):
    def __init__(self, name, address, latitude, longitude, url=None, image_url=None):
        self.name = name
        self.address = address
        self.longitude = longitude
        self.latitude = latitude
        self.url = url
        self.image_url = image_url

    def _build_hangups_object(self):
        return HangupsLocation(
            place=Place(
                url=self.url,
                name=self.name,
                address=EmbedItem(
                    postal_address=hangups.hangouts_pb2.EmbedItem.PostalAddress(
                        street_address=self.address
                    )
                ),
                geo=EmbedItem(
                    geo_coordinates=hangups.hangouts_pb2.EmbedItem.GeoCoordinates(
                        latitude=self.latitude,
                        longitude=self.longitude
                    )
                ),
                representative_image=EmbedItem(
                    image=hangups.hangouts_pb2.EmbedItem.Image(
                        url=self.image_url
                    )
                )
            )
        )
