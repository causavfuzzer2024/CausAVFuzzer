from math import dist


def get_all_npcs(obstacle_msgs, signal_msgs, n_column):
    npcs_id = []

    for msg in obstacle_msgs:
        if 'perceptionObstacle' in msg:
            for obs in msg['perceptionObstacle']:
                if 'id' in obs and obs['id'] not in npcs_id:
                    npcs_id.append(obs['id'])

    npcs_chpts = {}
    for id in npcs_id:
        obs_checking_points = []
        for msg in obstacle_msgs:
            obs_points = []
            if 'perceptionObstacle' in msg:
                for obs in msg['perceptionObstacle']:
                    if int(id) == obs['id']:
                        polygon_points = []
                        for pp in obs['polygonPoint']:
                            polygon_points.append((pp['x'], pp['y']))
                        if 0 != len(polygon_points):
                            for i in range(1, len(polygon_points)):
                                pp1, pp2 = polygon_points[i - 1], polygon_points[i]
                                x, y = (pp1[0] + pp2[0]) / 2, (pp1[1] + pp2[1]) / 2
                                polygon_points.append((x, y))
                            else:
                                pp1, pp2 = polygon_points[-1], polygon_points[0]
                                x, y = (pp1[0] + pp2[0]) / 2, (pp1[1] + pp2[1]) / 2
                                polygon_points.append((x, y))
                        obs_points = polygon_points
            obs_checking_points.append(obs_points)
        npcs_chpts[id] = obs_checking_points

    for msg in signal_msgs:
        if 'trafficLight' in msg:
            for sgn in msg['trafficLight']:
                if 'id' in sgn and sgn['id'] not in npcs_id:
                    npcs_id.append(sgn['id'])

    for i in range(len(npcs_id), n_column-1):
        npcs_id.append('dummy-{}'.format(i))
    npcs_id.append('DEST')

    npcs_traj_gt = {}
    for id in npcs_id:
        npcs_traj_gt[id] = [(-1, -1) for _ in range(len(obstacle_msgs))]
    for i in range(len(obstacle_msgs)):
        if 'perceptionObstacle' in obstacle_msgs[i]:
            for obs in obstacle_msgs[i]['perceptionObstacle']:
                obs_pos_curr = (obs['position']['x'], obs['position']['y'])
                npcs_traj_gt[obs['id']][i] = obs_pos_curr

    return npcs_id, npcs_traj_gt, npcs_chpts


def get_ev_trajectory(localization_msgs):
    ev_traj = []
    for msg in localization_msgs:
        if 'pose' in msg:
            point = ()
            if 'position' in msg['pose']:
                point = (msg['pose']['position']['x'], msg['pose']['position']['y'])
            theta = msg['pose']['heading']
            vel_vec = ()
            if 'linearVelocity' in msg['pose']:
                vel_vec = (msg['pose']['linearVelocity']['x'], msg['pose']['linearVelocity']['y'])
            vel = dist(vel_vec, (0, 0))
            acc_vec = ()
            if 'linearAcceleration' in msg['pose']:
                acc_vec = (msg['pose']['linearAcceleration']['x'], msg['pose']['linearAcceleration']['y'])
            acc = dist(acc_vec, (0, 0))
            ev_traj.append((point, theta, vel, acc))
    return ev_traj


def get_planning_trajectory(planning_msg, localization_msg):
    ev_planning_traj = []
    relative_time = -1
    ev_pos_curr = (0, 0)
    if 'pose' in localization_msg:
        if 'position' in localization_msg['pose']:
            ev_pos_curr = (localization_msg['pose']['position']['x'], localization_msg['pose']['position']['y'])
    # delta_t = planning_msg['header']['timestampSec'] - localization_msg['header']['timestampSec']
    if 'trajectoryPoint' in planning_msg:
        for tjpt in planning_msg['trajectoryPoint']:
            point = (tjpt['pathPoint']['x'], tjpt['pathPoint']['y']) if 'pathPoint' in tjpt else (0, 0)
            if dist(ev_pos_curr, point) < 0.3:
                relative_time = tjpt['relativeTime']
            if abs(tjpt['relativeTime'] - relative_time) < 0.01:
                # point = (tjpt['pathPoint']['x'], tjpt['pathPoint']['y']) if 'pathPoint' in tjpt else (0, 0)
                theta = tjpt['pathPoint']['theta'] if 'pathPoint' in tjpt else 0
                vel = tjpt['v'] if 'v' in tjpt else 0
                ev_planning_traj.append((point, theta, vel))
                relative_time += 0.08
    return ev_planning_traj


def dummy_obj_priority():
    return 'NO_TAG'


def dummy_interactive_tag():
    return 'NO_TAG'


def dummy_evaluator_dispatcher():
    return 'NONE_EVALUATOR'


def dummy_predictor_dispatcher():
    return 'NONE_PREDICTOR'


def dummy_prediction_result():
    return 'NO_PRED_ERROR'


def dummy_obj_decision():
    return 'NONE_DECISION'


def dummy_speed_planning():
    return 'NO_PLN_ERROR'
