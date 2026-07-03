import time
from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from game.models import Location
import re


def normalize_address(address):
    address = address.lower().strip()
    address = re.sub(r'улица|ул\.?', '', address)
    address = re.sub(r'проспект|пр\.?', '', address)
    address = re.sub(r'[,.]', '', address)
    address = re.sub(r'\s+', ' ', address).strip()
    return address


class Command(BaseCommand):
    help = 'Импорт адресов из CSV'

    def handle(self, *args, **kwargs):
        geolocator = Nominatim(user_agent="map_trainer")

        with open('addresses.csv', encoding='utf-8') as f:
            for line in f:
                address = line.strip()
                if not address:
                    continue

                address_normalized = normalize_address(address)

                if Location.objects.filter(address_normalized=address_normalized).exists():
                    self.stdout.write(f'⚠ Уже есть: {address}')
                    continue

                try:
                    loc = geolocator.geocode(address)
                except GeocoderTimedOut:
                    self.stdout.write(f'✗ Таймаут: {address}')
                    continue

                if loc:
                    Location.objects.create(
                        address=address,
                        address_normalized=address_normalized,
                        lat=loc.latitude,
                        lng=loc.longitude,
                        difficulty='easy',
                    )
                    self.stdout.write(f'✓ {address}')
                else:
                    self.stdout.write(f'✗ Не найден: {address}')

                time.sleep(1)