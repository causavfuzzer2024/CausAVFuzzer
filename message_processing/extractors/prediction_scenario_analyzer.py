from .utils.map_parser import near_junction, is_in_junction, is_on_lane
from math import dist


def get_scenario(localization_msg, planning_msg, map):
    scenario = 'CRUISE'
    ev_pos = get_ev_position(localization_msg)
    if near_junction(ev_pos, map) or is_in_junction(ev_pos, map):
        scenario = 'JUNCTION'
    traj_wpts = get_planning_trajectory_waypoints(planning_msg)
    for wpt in traj_wpts:
        if is_in_junction(wpt, map):
            scenario = 'JUNCTION'
            break
    return scenario


def get_ev_position(localization_msg):
    return (localization_msg['pose']['position']['x'], localization_msg['pose']['position']['y'],
            localization_msg['pose']['position']['z'])


def get_planning_trajectory_waypoints(planning_msg):
    trajectory_waypoints = []
    if 'trajectoryPoint' in planning_msg:
        for wpt in planning_msg['trajectoryPoint']:
            if 'relativeTime' in wpt and wpt['relativeTime'] < 0:
                continue
            if 'pathPoint' in wpt:
                x, y = wpt['pathPoint']['x'], wpt['pathPoint']['y']
                trajectory_waypoints.append((x, y))
    return trajectory_waypoints


def get_npc_feature(prediction_msg, map):
    features = {}
    if 'predictionObstacle' in prediction_msg:
        for obs in prediction_msg['predictionObstacle']:
            obs_feature = {}
            obs_id_curr, type_curr, area_curr, speed_curr, priority_curr, tag_curr, is_static_curr = \
                0, '', 'OFF_LINE', 0,  '', '', False
            if 'perceptionObstacle' in obs and 'id' in obs['perceptionObstacle']:
                obs_id_curr = obs['perceptionObstacle']['id']
            if 'perceptionObstacle' in obs and 'type' in obs['perceptionObstacle']:
                type_curr = obs['perceptionObstacle']['type']
            if 'perceptionObstacle' in obs and 'position' in obs['perceptionObstacle']:
                position_curr = obs['perceptionObstacle']['position']
                obs_pos = (position_curr['x'], position_curr['y'], position_curr['z'])
                if is_on_lane(obs_pos, map):
                    area_curr = 'ON_LANE'
                if is_in_junction(obs_pos, map):
                    area_curr = 'JUNCTION'
            if 'perceptionObstacle' in obs and 'velocity' in obs['perceptionObstacle']:
                speed = obs['perceptionObstacle']['velocity']
                speed_vec = (speed['x'], speed['y'], speed['z'])
                speed_curr = dist(speed_vec, (0, 0, 0))
            if 'priority' in obs and 'priority' in obs['priority']:
                priority_curr = obs['priority']['priority']
            if 'interactiveTag' in obs and 'interactiveTag' in obs['interactiveTag']:
                tag_curr = obs['interactiveTag']['interactiveTag']
            if 'isStatic' in obs:
                is_static_curr = obs['isStatic']
            obs_feature['type'], obs_feature['area'], obs_feature['speed'], obs_feature['priority'], obs_feature['tag'],\
                obs_feature['is_static'] = type_curr, area_curr, speed_curr, priority_curr, tag_curr, is_static_curr
            features[obs_id_curr] = obs_feature
    return features
