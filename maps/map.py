import numpy as np
import json
import networkx as nx
import os
from scipy.spatial import distance
from datetime import datetime
import random
import sys
import gzip
import aiofiles
import io

from butils.utils import *
from maps.local_coordinates.local_transforms import LocalTransform

import logging
logger = logging.getLogger("thug.map")
logger.setLevel(logging.DEBUG)

siege_ctf_respawn_coords = {
    "bakisi_isles": {"red": [12446, 17599, 12802], "blue": [36762, 15792, 12832]},
    "hoven_gorge": {"red": [9883, 9623, 4170], "blue": [19874, 22622, 4269]},
    "outpost_x12": {"red": [10290, 14710, 6144], "blue": [45047, 15683, 6151]},
    "korgon_outpost": {"red": [28328, 21108, 6145], "blue": [14090, 22676, 6145]},
    "metropolis": {"red": [47061, 14929, 21463], "blue": [49628, 28445, 21463]},
    "blackwater_city": {"red": [13004, 9759, 5156], "blue": [15165, 24379, 5156]},
    "command_center": {"red": [21523, 24181, 2174], "blue": [20766, 22551, 2174]},
    'aquatos_sewers': {"red": [12680, 17857, 6736], "blue": [17312, 12087, 6379]},
    "blackwater_docks": {"red": [25773, 18112, 60224], "blue": [25527, 23871, 60224]},
    "marcadia_palace": {"red": [34240, 54416, 7413], "blue": [27093, 54161, 7413]},
}

def search_heuristic(node1, node2):
    return distance.cdist([node1], [node2], 'euclidean')[0]

class Map:
    def __init__(self, map_name:str):
        self.map = map_name
        self.path_cache = None
        self.local_transform = None

    async def read_map(self):
        start_time = datetime.now()
        logger.info(f"Loading map graph {self.map} ...")
        self.G = await self.read_graph(f"maps/graphs/{self.map}.edgelist")

        assert len(list(nx.connected_components(self.G))) == 1

        self.points = np.array(self.G.nodes)
        logger.info(f"Loaded map in {(datetime.now() - start_time).total_seconds():.2f} seconds!")

        logger.info(f"Loading map local transformation ...")
        self.local_transform = LocalTransform(self.map)
        self.local_transform.read()

        # logger.info("Loading three map slice ...")
        # with open (f'maps/{self.map}.json', 'r') as f:
        #     self.map_three_slice = json.loads(f.read())

        logger.info(f"Loading waypoints ...")
        self.G_waypoints, self.waypoints = await self.read_waypoints(f"maps/graphs/{self.map}_waypoints.edgelist", f"maps/graphs/{self.map}_waypoints_only.edgelist")
        start_time = datetime.now()
        logger.info(f"Loading waypoint cache ...")
        self.waypoint_cache = await self.read_waypoint_cache(f'maps/graphs/{self.map}_waypoint_cache.json.gz')
        logger.info(f"Loaded wapoints in {(datetime.now() - start_time).total_seconds():.2f} seconds!")

    async def read_file(self, filepath, mode='r'):
        async with aiofiles.open(filepath, mode=mode) as file:
            content = await file.read()
        return content

    async def read_graph(self, filepath):
        content = await self.read_file(filepath)
        file_like_object = io.StringIO(content)
        G = nx.read_edgelist(file_like_object, nodetype=eval, delimiter='|')
        return G

    async def read_waypoints(self, G_waypoint_path, waypoints_path):
        content = await self.read_file(G_waypoint_path)
        file_like_object = io.StringIO(content)
        G_waypoints = nx.read_edgelist(file_like_object,nodetype=eval, delimiter='|')

        content = await self.read_file(waypoints_path)
        file_like_object = io.StringIO(content)
        waypoints = np.array(nx.read_edgelist(file_like_object,nodetype=eval, delimiter='|').nodes)
        return G_waypoints, waypoints

    async def read_waypoint_cache(self, filepath):
        content = await self.read_file(filepath, mode='rb')
        with gzip.GzipFile(fileobj=io.BytesIO(content)) as f:
            data = json.load(f)
        return data

    def path(self, src, dst, chargeboot=False):
        # When chargeboot = True, we want to move ~ 110
        cboot_dist = 80

        src = tuple(src)
        dst = tuple(dst)


        if self.path_cache != None and len(self.path_cache) != 0 and calculate_distance(dst, self.path_cache[-1]) < 600:
            if chargeboot:
                while len(self.path_cache) > 1 and calculate_distance(src, self.path_cache[0]) < cboot_dist:
                    self.path_cache.pop(0)
            return self.path_cache.pop(0)

        if not self.G.has_node(src):
            return src

        # if dst is not in the graph, use the closest point
        if not self.G.has_node(dst):
            # get the closest point as dst
            dst = self.find_closest_node(dst)

        src_closest_waypoint = self.get_closest_waypoint(src)
        dst_closest_waypoint = self.get_closest_waypoint(dst)

        # Use waypoints
        if src_closest_waypoint != dst_closest_waypoint:
            waypoint_path_cache = self.query_waypoint_cache(src_closest_waypoint, dst_closest_waypoint)

            # Path = A* to src_waypoint, then use waypoint_cache
            try:
                path = nx.astar_path(self.G, src, src_closest_waypoint, heuristic=search_heuristic)
                if len(path) == 0:
                    logger.exception(f"No Path Found: {src} | {dst}")
                    return src

                path = path + waypoint_path_cache
                path.pop(0)

                if chargeboot:
                    while len(path) > 1 and calculate_distance(src, path[0]) < cboot_dist:
                        path.pop(0)

                self.path_cache = path
                if len(self.path_cache) == 0:
                    logger.exception(f"No Path Found: {src} | {dst}")
                    return src

                return self.path_cache.pop(0)

            except nx.exception.NetworkXNoPath:
                logger.exception(f"No Path Found: {src} | {dst}")
                return src

        # Don't use waypoints
        else:
            try:
                path = nx.astar_path(self.G, src, dst, heuristic=search_heuristic)
                if len(path) == 1:
                    return path[0]
                elif len(path) > 1:
                    path.pop(0)
                    if chargeboot:
                        while len(path) > 1 and calculate_distance(src, path[0]) < cboot_dist:
                            path.pop(0)
                    if len(path) > 1:
                        self.path_cache = path
                    return path[0]
                else:
                    raise Exception(f"Unknown path length: {path}")
            except nx.exception.NetworkXNoPath:
                logger.exception("No Path Found:")
                return src

    def query_waypoint_cache(self, src_waypoint, dst_waypoint):
        if f'{src_waypoint}|{dst_waypoint}' in self.waypoint_cache.keys():
            return self.waypoint_cache[f'{src_waypoint}|{dst_waypoint}'].copy()
        result = self.waypoint_cache[f'{dst_waypoint}|{src_waypoint}'].copy()
        result.reverse()
        return result


    def find_closest_node(self, dst):
        distances = distance.cdist(self.points, [dst], 'euclidean')
        min_idx = np.where(distances == np.amin(distances))[0][0]
        return tuple(self.points[min_idx])

    def get_closest_waypoint(self, point):
        distances = distance.cdist(self.waypoints, [point], 'euclidean')
        min_idx = np.where(distances == np.amin(distances))[0][0]
        return tuple(self.waypoints[min_idx])

    def get_random_coord(self):
        return tuple(random.choice(np.array(self.points)))

    def get_random_coord_connected(self, coord):
        return list(random.choice(list(self.G.neighbors(tuple(coord)))))
    
    def get_random_coord_nearby(self, coord, dist=500):
        variance = 100
        dist_min = dist-variance
        dist_max = dist+variance
        distances = distance.cdist(self.points, [coord], 'euclidean').flatten()
        points = self.points[np.where((distances < dist_max) & (distances > dist_min))]
        point_chosen = list(tuple(random.choice(points)))
        return point_chosen

    def get_random_coord_connected_close(self, src_coord, dst_coord):
        if not self.G.has_node(src_coord):
            src_coord = self.find_closest_node(src_coord)

        if random.random() < .4:
            return self.get_random_coord_connected(src_coord)
        return self.path(src_coord, dst_coord)


    def get_front_gbomb_position(self, src_coord, dest_coord):
        # Step 1: Get all nodes between front gbomb distance
        # Bomb forward shoot is between 570 and 700
        distances = distance.cdist(self.points, [src_coord], 'euclidean').flatten()
        points = self.points[np.where((distances < 700) & (distances > 570))]

        # Step 2: Get the point closest to dest_coord
        distances = distance.cdist(points, [dest_coord], 'euclidean')
        min_idx = np.where(distances == np.amin(distances))[0][0]
        return tuple(points[min_idx])


    def get_respawn_location(self, team_color, game_mode):
        if game_mode == 'Deathmatch':
            return self.get_random_coord()

        # Siege/CTF
        return self.find_closest_node(siege_ctf_respawn_coords[self.map][team_color])

    def __str__(self):
        return f"Map(name={self.map})"

    def transform_global_to_local(self, point):
        transformed = self.local_transform.transform_global_to_local(point)
        return [transformed[0], transformed[1], transformed[2]]
    
    def transform_local_to_global(self, point):
        transformed = self.local_transform.transform_local_to_global(point)
        return [int(transformed[0]), int(transformed[1]), int(transformed[2])]


if __name__ == '__main__':
    print("Reading map")
    map = Map('aquatos_sewers')
    print("Done")
