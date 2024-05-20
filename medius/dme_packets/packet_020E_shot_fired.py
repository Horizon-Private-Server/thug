from collections import deque
from butils.utils import *
import os
from constants.constants import WEAPON_MAP
'''
P0 moby: 1
P1 moby: 268435457
P2 moby: 536870913

P0 n60 :
P0 bltz:
P0 flux:
P0 rckt:
P0 grav:
P0 mine:
P0 lava:
P0 mrph:
P1 hypr:

P1 flux: 4108
P2 flux: 4208
'''

standard_object_id_map = {
    1: 0,
    268435457: 1,
    536870913: 2,
    805306369: 3,
    1073741825: 4,
    1342177281: 5,
    1610612737: 6,
    1879048193: 7,
    4294967295: -1
}

# alt_object_id_map = {
#     13: 0,
#     1: 1,
#     2: 2,
#     3: 3,
#     6: 4,
#     5: 5,
#     4: 6,
#     7: 7,
#     4294967295: -1
# }

alt_object_id_map = {
    13: 0,
    268435457: 1,
    536870913: 2,
    805306369: 3,
    1610612737: 4,
    1342177281: 5,
    1073741825: 6,
    1879048193: 7,
    4294967295: -1
}


WEAPON_MAP_SRC = {
    'n60': '0{}',
    'blitz': '0{}',
    'flux': '4{}',
    'rocket': '0{}',
    'grav': '0{}',
    'mine': '0{}',
    'lava': '0{}',
    'morph': '0{}',
    'hyper': '0{}',
}

class packet_020E_shot_fired:
    def __init__(self, network:str, map:str=None, weapon:str=None,
                           src_player:int=None,
                           unk1:str='08',
                           time:int=None,
                           object_id:int=None,
                           unk2:str="0000",
                           local_x:int=0,
                           unk3:str="0000",
                           local_y:int=0,
                           unk4:str="0000",
                           local_z:int=0,
                           unk5:str="0000",
                           local_x_2:int=0,
                           unk6:str="0000",
                           local_y_2:int=0,
                           unk7:str="0000",
                           local_z_2:int=0
                        ):

        self.name = os.path.basename(__file__).split(".py")[0]
        self.network = network
        self.id = b'\x02\x0E'
        self.map = map
        self.weapon = weapon
        self.src_player = src_player
        self.time = time
        self.object_id = object_id
        self.unk1 = unk1
        self.unk2 = unk2
        self.local_x = local_x
        self.unk3 = unk3
        self.local_y = local_y
        self.unk4 = unk4
        self.local_z = local_z
        self.unk5 = unk5
        self.local_x_2 = local_x_2
        self.unk6 = unk6
        self.local_y_2 = local_y_2
        self.unk7 = unk7
        self.local_z_2 = local_z_2

    @classmethod
    def serialize(self, network, data: deque):
        weapon = WEAPON_MAP[data.popleft()]
        t = data.popleft()
        src_player = hex_to_int_little(data.popleft())
        unk1 = data.popleft()

        time = hex_to_int_little(''.join([data.popleft() for i in range(4)]))
        moby_id = hex_to_int_little(''.join([data.popleft() for i in range(4)]))

        if moby_id in standard_object_id_map.keys():
            object_id = standard_object_id_map[moby_id]
        elif moby_id in alt_object_id_map.keys():
            object_id = alt_object_id_map[moby_id]
        else:
            object_id = moby_id

        unk2 = ''.join([data.popleft() for i in range(2)])
        local_x = hex_to_int_little(''.join([data.popleft() for i in range(2)]))
        unk3 = ''.join([data.popleft() for i in range(2)])
        local_y = hex_to_int_little(''.join([data.popleft() for i in range(2)]))
        unk4 = ''.join([data.popleft() for i in range(2)])
        local_z = hex_to_int_little(''.join([data.popleft() for i in range(2)]))

        unk5 = ''.join([data.popleft() for i in range(2)])
        #local_x_2 = ''.join([data.popleft() for i in range(2)])
        local_x_2 = hex_to_int_little(''.join([data.popleft() for i in range(2)]))
        unk6 = ''.join([data.popleft() for i in range(2)])
        #local_y_2 = ''.join([data.popleft() for i in range(2)])
        local_y_2 = hex_to_int_little(''.join([data.popleft() for i in range(2)]))
        unk7 = ''.join([data.popleft() for i in range(2)])
        #local_z_2 = ''.join([data.popleft() for i in range(2)])
        local_z_2 = hex_to_int_little(''.join([data.popleft() for i in range(2)]))

        return packet_020E_shot_fired(network, '', weapon, src_player, unk1, time, object_id, unk2, local_x, unk3, local_y, unk4, local_z, unk5, local_x_2, unk6, local_y_2, unk7, local_z_2)

    def to_bytes(self):

        if self.map in {'hoven_gorge', 'outpost_x12', 'metropolis'}:
            object_id = {v: k for k, v in alt_object_id_map.items()}[self.object_id]
        else:
            object_id = {v: k for k, v in standard_object_id_map.items()}[self.object_id]

        return self.id + \
            hex_to_bytes({v: k for k, v in WEAPON_MAP.items()}[self.weapon]) + \
            hex_to_bytes("00") + \
            hex_to_bytes(WEAPON_MAP_SRC[self.weapon].format(self.src_player)) + \
            hex_to_bytes(self.unk1) + \
            int_to_bytes_little(4, self.time) + \
            int_to_bytes_little(4, object_id) + \
            hex_to_bytes(self.unk2) + \
            int_to_bytes_little(2, self.local_x) + \
            hex_to_bytes(self.unk3) + \
            int_to_bytes_little(2, self.local_y) + \
            hex_to_bytes(self.unk4) + \
            int_to_bytes_little(2, self.local_z) + \
            hex_to_bytes(self.unk5) + \
            int_to_bytes_little(2, self.local_x_2) + \
            hex_to_bytes(self.unk6) + \
            int_to_bytes_little(2, self.local_y_2) + \
            hex_to_bytes(self.unk7) + \
            int_to_bytes_little(2, self.local_z_2)

    def __str__(self):
        return f"{self.network}_{self.name}; map:{self.map} weapon:{self.weapon} src_player:{self.src_player} unk1:{self.unk1} time:{self.time} object_id:{self.object_id} " + \
                f"unk2:{self.unk2} local_x:{self.local_x} unk3:{self.unk3}  local_y:{self.local_y} unk4:{self.unk4} local_z:{self.local_z} " + \
                f"unk5:{self.unk5} local_x_2:{self.local_x_2} unk6:{self.unk6}  local_y_2:{self.local_y_2} unk7:{self.unk7} local_z_2:{self.local_z_2}"
