import asyncio
import logging
import math
import os
import time
from datetime import datetime

import aiohttp
import coloredlogs as coloredlogs
import requests
from aiohttp import ClientSession
from dotenv import load_dotenv
from influxdb import InfluxDBClient

# Load all the environment variables from the appropriate file
load_dotenv()

logger = logging.getLogger('HyGraphs')

# Retrieve the environment variables which we use to fetch
# data from Hypixel
hypixel_api_key = os.environ.get('HYPIXEL_API_KEY')
uuid = os.environ.get('UUID')


def write_point(measurement: str, fields: dict):
    """
    Writes a single measurement into the InfluxDB database configured
    in the main method.

    :param measurement: The name of the measurement being inserted into the DB.
    :param fields:      A dictionary containing all the fields which should be inserted.
    """

    client.write_points([{
        "measurement": measurement,
        "time": get_time(),
        "fields": fields
    }])


def get_time():
    """
    :return: The current time correctly formatted for InfluxDB
    """

    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def calculate_hypixel_level(experience: int):
    """
    Calculates an exact network level from the given experience value.

    :param experience: The player's total network experience.
    :return:           Their exact network level.
    """
    return (math.sqrt(experience + 15312.5) - 88.38834764831843) / 35.3553390593273


async def fetch_hypixel_player(session: ClientSession):
    """
    Fetches player data from the Hypixel API using the provided
    UUID and Hypixel API key.
    """

    try:
        json: dict = await (await session.get(
            'https://api.hypixel.net/player'
            f'?key={hypixel_api_key}'
            f'&uuid={uuid}'
        )).json()

        write_point('player', {
            "karma": json['player']['karma'],
            "experience": json['player']['networkExp'],
            "level": calculate_hypixel_level(json['player']['networkExp'])
        })

        logger.info('[PLAYER] Fetched successfully')
    except Exception as ex:
        logger.error('[PLAYER] Error whilst fetching', exc_info=ex)


async def fetch_autotip(session: ClientSession):
    """
    Fetches information from the AutoTip API to provide the
    number of online, active and total players.
    """

    try:
        json: dict = await (await session.get('https://api.autotip.pro/counts')).json()
        write_point('autotip', {
            "total": json['total'],
            "active": json['active'],
            "online": json['online']
        })
        logger.info('[AUTOTIP] Fetched successfully')
    except Exception as ex:
        logger.error('[AUTOTIP] Error whilst fetching', exc_info=ex)


async def fetch_counts(session: ClientSession):
    """
    Fetches the player counts in each game on the Hypixel network.
    """

    try:
        json: dict = await (await session.get(
            'https://api.hypixel.net/gameCounts'
            f'?key={hypixel_api_key}'
        )).json()

        # Store the total player counts of each game in a format that
        # InfluxDB can easily read
        counts_fields = {}
        games: dict = json['games']

        for game in games.keys():
            counts_fields[game] = games[game].get('players') or 0

        write_point('counts', counts_fields)
        write_point('server', {
            "online": json['playerCount']
        })

        logger.info('[COUNTS] Fetched successfully')
    except Exception as ex:
        logger.error('[COUNTS] Error whilst fetching', exc_info=ex)


async def fetch_mods(session: ClientSession):
    """
    Fetches statistics across multiple popular modders and their APIs
    to provide an insight to how many players are currently using them.
    """

    # Stores all the fields that we've retrieved across multiple
    # requests so we can put it in a bulk write
    fields = {}

    try:
        json: dict = await (await session.get('https://mediamodapi.conorthedev.me/stats')).json()
        fields['cbyrne_all'] = json['allUsers']
        fields['cbyrne_online'] = json['allOnlineUsers']
        logger.info('[CBYRNE] Fetched successfully')
    except Exception as ex:
        logger.error('[CBYRNE] Error whilst fetching', exc_info=ex)

    try:
        json: dict = await (await session.get('https://api.sk1er.club/online')).json()
        fields['sk1er_online'] = json['count']
        logger.info('[SK1ER] Fetched successfully')
    except Exception as ex:
        logger.error('[SK1ER] Error whilst fetching', exc_info=ex)

    try:
        json: dict = await (await session.get('https://api.hyperium.cc/users')).json()

        fields['hyperium_online'] = json['online']
        fields['hyperium_day'] = json['day']
        fields['hyperium_week'] = json['week']
        fields['hyperium_all'] = json['all']

        logger.info('[HYPERIUM] Fetched successfully')
    except Exception as ex:
        logger.error('[HYPERIUM] Error whilst fetching', exc_info=ex)

    write_point('mods', fields)


async def start():
    """
    Main loop run after we've connected to the InfluxDB server to
    provide constant analytics.
    """

    i = 0
    while True:
        i += 1
        logger.info(f'======= ITERATION {i} =======')

        async with aiohttp.ClientSession(headers={
            'User-Agent': 'HyGraphs'
        }) as session:
            await fetch_hypixel_player(session)
            await fetch_autotip(session)
            await fetch_counts(session)
            await fetch_mods(session)

        logger.info('[ITERATION] Done!')
        await asyncio.sleep(30)


if __name__ == '__main__':
    db = os.environ.get('INFLUX_DB', 'hygraphs')
    found_client = False
    client = None

    while not found_client:
        try:
            client = InfluxDBClient(
                os.environ.get('INFLUX_HOST', 'localhost'),
                int(os.environ.get('INFLUX_PORT', 8086)),
                os.environ.get('INFLUX_USERNAME', 'root'),
                os.environ.get('INFLUX_PASSWORD', 'root'),
                db
            )

            # Run a single request to connect and allow us to check the
            # connection is working
            client.create_database(db)

            found_client = True
            logger.info('Connected to InfluxDB successfully!')
        except requests.exceptions.ConnectionError:
            logger.error('Couldn\'t connect to InfluxDB. Waiting 5s')
            time.sleep(5)

    # Enable logging and start the importer
    coloredlogs.install(fmt='%(asctime)s %(name)s %(levelname)s %(message)s')
    asyncio.get_event_loop().run_until_complete(start())
