from math import dist, sqrt
from .util import get_ev_trajectory, get_planning_trajectory
from .extractors.utils.vehicle_parser import cos_theta_calculating, sin_theta_calculating


def get_execution_result(localization_msgs_clip, planning_msg):
    ev_traj = get_ev_trajectory(localization_msgs_clip)
    pln_traj = get_planning_trajectory(planning_msg, localization_msgs_clip[0])
    max_len = min(len(ev_traj), len(pln_traj))
    error_sum = 0
    for i in range(max_len):
        ev_pos_gt = ev_traj[i][0]
        ev_pos_pln = pln_traj[i][0]
        # print(ev_pos_gt, ev_pos_pln)
        error_sum += dist(ev_pos_gt, ev_pos_pln)
    error_sum /= max_len if max_len else 1
    return error_sum


def has_accident_happened(localization_msg, obstacle_msg, ev, threshold_nearby):
    # threshold = sqrt(ev.front_edge_to_center ** 2 + ev.left_edge_to_center ** 2)
    has_accident = False
    npcs_nearby = []
    # ev_pos = (0, 0)
    # if 'pose' in localization_msg and 'position' in localization_msg['pose']:
    #     ev_pos = (localization_msg['pose']['position']['x'], localization_msg['pose']['position']['y'])
    # if 'perceptionObstacle' in obstacle_msg:
    #     for obs in obstacle_msg['perceptionObstacle']:
    #         obs_id = obs['id'] if 'id' in obs else -1
    #         obs_pos = (obs['position']['x'], obs['position']['y']) if 'position' in obs else (100, 100)
    #         dist_curr = dist(ev_pos, obs_pos)
    #         ret[obs_id] = 1 if dist_curr < threshold else 0

    threshold_lon_front, threshold_lon_back = ev.front_edge_to_center, -ev.back_edge_to_center
    threshold_lat = ev.left_edge_to_center  # for filtering accident recordings
    ev_pos = (localization_msg['pose']['position']['x'], localization_msg['pose']['position']['y'],
              localization_msg['pose']['position']['z'])
    ev_pos_dict = localization_msg['pose']['position']
    ev_heading = localization_msg['pose']['heading']
    if 'perceptionObstacle' in obstacle_msg:
        for obs in obstacle_msg['perceptionObstacle']:
            obs_id = obs['id'] if 'id' in obs else -1

            obs_pos = (obs['position']['x'], obs['position']['y'], obs['position']['z'])
            obs_pos_dict = obs['position']
            distance = dist(ev_pos, obs_pos)
            cos_theta = cos_theta_calculating(ev_heading, ev_pos_dict, obs_pos_dict)
            sin_theta = sin_theta_calculating(ev_heading, ev_pos_dict, obs_pos_dict)
            distance_lon, distance_lat = distance * cos_theta, distance * sin_theta

            if cos_theta >= 0:  # in front of ev
                if distance_lon <= threshold_lon_front and distance_lat <= threshold_lat:
                    # obs_shape = (obs['length'], obs['width'], obs['height'])
                    # print(f'  FRONT: EV: {ev_pos}, NPC {obs_id}: {obs_pos}, NPC_SHAPE: {obs_shape}')
                    # print(f'  distance: {distance_lon}, {distance_lat}, threshold: {threshold_lon_front}, {threshold_lat}')
                    has_accident = True
            else:  # behind ev and not filtering accident recordings
                if distance_lon >= threshold_lon_back and distance_lat <= threshold_lat:
                    # obs_shape = (obs['length'], obs['width'], obs['height'])
                    # print(f'  BEHIND: EV: {ev_pos}, NPC {obs_id}: {obs_pos}, NPC_SHAPE: {obs_shape}')
                    # print(f'  distance: {distance_lon}, {distance_lat}, threshold: {threshold_lon_back}, {threshold_lat}')
                    has_accident = False
            for pts in obs['polygonPoint']:
                pt = (pts['x'], pts['y'], pts['z'])
                distance = dist(ev_pos, pt)
                cos_theta = cos_theta_calculating(ev_heading, ev_pos_dict, pts)
                sin_theta = sin_theta_calculating(ev_heading, ev_pos_dict, pts)
                distance_lon, distance_lat = distance * cos_theta, distance * sin_theta
                if cos_theta >= 0:  # in front of ev
                    if distance_lon <= threshold_lon_front and distance_lat <= threshold_lat:
                        # obs_shape = (obs['length'], obs['width'], obs['height'])
                        # print(f'  FRONT: EV: {ev_pos}, NPC {obs_id}: {obs_pos}, NPC_SHAPE: {obs_shape}')
                        # print(f'  distance: {distance_lon}, {distance_lat}, threshold: {threshold_lon_front}, {threshold_lat}')
                        has_accident = True
                else:  # behind ev and not filtering accident recordings
                    if distance_lon >= threshold_lon_back and distance_lat <= threshold_lat:
                        # obs_shape = (obs['length'], obs['width'], obs['height'])
                        # print(f'  BEHIND: EV: {ev_pos}, NPC {obs_id}: {obs_pos}, NPC_SHAPE: {obs_shape}')
                        # print(f'  distance: {distance_lon}, {distance_lat}, threshold: {threshold_lon_back}, {threshold_lat}')
                        has_accident = False
            
            if distance < threshold_nearby:  # Threshold for finding nearby npcs
                npcs_nearby.append(obs_id)

    return has_accident, npcs_nearby
