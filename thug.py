import os
import asyncio
import logging
import argparse

logger = logging.getLogger('thug')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s | %(levelname)s | %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

from butils.utils import *

from utils.timeouttimer import TimeoutTimer
from utils.config import Config

import time
import sys

from connections.networkmanager import NetworkManager

from model.model import Model

import json

from constants.constants import SKIN_MAP

import random
from datetime import datetime


class Thug:
    def __init__(self, config:dict):
        logger.info("Initializing ...")
        self._config = config

        if self._config.skin == 'random':
            skins = list(SKIN_MAP.values())
            skins.remove('NA')
            random.shuffle(skins)
            self._config.skin = skins[0]

        self._config.start_time = datetime.now()
        self._loop_time = .001

        self.loop = asyncio.new_event_loop()



        self._network_manager = NetworkManager(self.loop, self._config)
        print("SLEEPING!")
        self.loop.run_until_complete(self.sleep())

        return

        self._timer = TimeoutTimer(self.loop, self._config.start_time, self._config.timeout)




        logger.info(self._config)

        #self.loop.run_until_complete(self._tcp_conn.main(self._model))


        self._model = Model(self._config, self.loop, self._tcp_conn, self._udp_conn)

        self.loop.create_task(self._udp_conn.main(self._model))
        self.loop.run_until_complete(self._tcp_conn.main(self._model))



        self.loop.run_until_complete(self.main())
        return

    async def sleep(self):
        await asyncio.sleep(50000)

    async def main(self):
        while self.is_alive():
            #logger.info("Looping!")

            await self._network_manager.update()

            await asyncio.sleep(self._loop_time)

        logger.info("Ending main routine!")
        await self._timer.kill()

        logger.info("Thug finished.")

    def is_alive(self):
        # Check if we have fully timed out
        return self._timer.alive and self._network_manager.alive
        

        # Check if the network manager has timed out

        # Check if the model quit

        return False









# AWS Lambda handler
def handler(event, context):
    print(event)
    try:
        Thug(config = event)
    except:
        logger.exception("Thug error!")
        return 1
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Horizon's UYA Bot. (Thug)")
    parser.add_argument('--config', type=str, default=None, help='Path to JSON configuration file (default: use ENV Vars)')

    args = parser.parse_args()

    # Load configuration from the specified JSON file
    config_file = args.config
    config = Config(args.config)

    Thug(config=config)

