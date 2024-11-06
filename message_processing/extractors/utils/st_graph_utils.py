from math import dist, sqrt
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from .parser_utils import obj_id_string2int


def boundary_deciding_checking(planning_msg, npc_points_gt, i, ev, decider):
    boundary_features = {}

    st_boundaries = {}
    boundary_types = []
    # boundary_types = ['ST_BOUNDARY_TYPE_YIELD', 'ST_BOUNDARY_TYPE_OVERTAKE', 'ST_BOUNDARY_TYPE_UNKNOWN,
                      # 'ST_BOUNDARY_TYPE_DRIVABLE_REGION']
    if 'debug' in planning_msg and 'planningData' in planning_msg['debug']:
        if 'stGraph' in planning_msg['debug']['planningData']:
            for stg in planning_msg['debug']['planningData']['stGraph']:
                boundary = []
                if 'SPEED_BOUNDS_PRIORI' == decider:
                    if 'name' in stg and 'SPEED_HEURISTIC_OPTIMIZER' == stg['name'] and 'boundary' in stg:
                        boundary = stg['boundary']
                        boundary_types = ['ST_BOUNDARY_TYPE_FOLLOW', 'ST_BOUNDARY_TYPE_OVERTAKE',
                                          'ST_BOUNDARY_TYPE_STOP',
                                          'ST_BOUNDARY_TYPE_UNKNOWN', 'ST_BOUNDARY_TYPE_YIELD',
                                          'ST_BOUNDARY_TYPE_KEEP_CLEAR']
                elif 'SPEED_BOUNDS_FINAL' == decider:
                    if 'name' in stg and 'PIECEWISE_JERK_NONLINEAR_SPEED_OPTIMIZER' == stg['name'] \
                            and 'boundary' in stg:
                        boundary = stg['boundary']
                        boundary_types = ['ST_BOUNDARY_TYPE_FOLLOW', 'ST_BOUNDARY_TYPE_OVERTAKE',
                                          'ST_BOUNDARY_TYPE_STOP',
                                          'ST_BOUNDARY_TYPE_UNKNOWN', 'ST_BOUNDARY_TYPE_YIELD',
                                          'ST_BOUNDARY_TYPE_KEEP_CLEAR']
                else:  # ST_BOUNDS
                    if 'name' not in stg and 'boundary' in stg:
                        boundary = stg['boundary']
                        boundary_types = ['ST_BOUNDARY_TYPE_YIELD', 'ST_BOUNDARY_TYPE_OVERTAKE',
                                          'ST_BOUNDARY_TYPE_UNKNOWN']
                for stgbd in boundary:
                    if 'type' in stgbd and stgbd['type'] in boundary_types:
                        ob_id = obj_id_string2int(stgbd['name'])
                        boundary_pts = []
                        for pt in stgbd['point']:
                            boundary_pts.append([pt['s'], pt['t']])
                        st_polygon = Polygon(boundary_pts)
                        st_convex = st_polygon.convex_hull
                        st_boundaries[ob_id] = st_convex

    npc_ids = list(npc_points_gt.keys())
    ev_traj = get_planning_trajectory(planning_msg)
    for npc_id in npc_ids:
        risky_st, st_sum = get_risky_st(npc_points_gt[npc_id][i:], ev_traj, ev)
        counter = 0
        if npc_id in st_boundaries:
            for st in risky_st:
                st = Point(st)
                if st_boundaries[npc_id].contains(st):  # inside the obstacle block
                    counter += 1
        feature = (counter / st_sum) if st_sum else 0.0
        boundary_features[npc_id] = feature

    return boundary_features


def speed_limits_checking(planning_msg, npc_points_gt, i, ev):
    feature = {}
    speed_limits = []
    ev_traj = get_planning_trajectory(planning_msg)

    if 'debug' in planning_msg and 'planningData' in planning_msg['debug']:
        if 'stGraph' in planning_msg['debug']['planningData']:
            for stgraph in planning_msg['debug']['planningData']['stGraph']:
                if 'name' in stgraph and 'SPEED_HEURISTIC_OPTIMIZER' == stgraph['name']:
                    if 'speedLimit' in stgraph:
                        for sl in stgraph['speedLimit']:
                            speed_limits.append((sl['s'], sl['v']))

    feature = get_sv_feature(npc_points_gt, ev_traj, i, ev, speed_limits)

    return feature



def speed_planning_checking(planning_msg, npc_points_gt, index, ev, margin=0):
    features = {}

    speed_profile = []
    if 'debug' in planning_msg and 'planningData' in planning_msg['debug']:
        if 'stGraph' in planning_msg['debug']['planningData']:
            for stgraph in planning_msg['debug']['planningData']['stGraph']:
                if 'name' in stgraph and 'SPEED_HEURISTIC_OPTIMIZER' == stgraph['name']:
                    if 'speedProfile' in stgraph:
                        for sp in stgraph['speedProfile']:
                            speed_profile.append((sp['s'], sp['t']))

    ev_traj = get_planning_trajectory(planning_msg)
    speed_planning = []
    for sp in speed_profile:
        p = 0
        for j in range(p, len(ev_traj)):
            if abs(sp[0] - ev_traj[j][2]) < 0.01:  # x, y, s, v, t
                speed_planning.append((ev_traj[j][0], ev_traj[j][1], sp[0], sp[1]))
                p = j

    threshold = sqrt(
        ev.front_edge_to_center * ev.front_edge_to_center + ev.left_edge_to_center * ev.left_edge_to_center) + margin
    npc_ids = list(npc_points_gt.keys())
    for npc_id in npc_ids:
        risky_pt = set()
        for sp in speed_planning:
            x, y = sp[0], sp[1]  # x, y, s, t
            for i in range(len(npc_points_gt[npc_id][index:])):
                for chpt in npc_points_gt[npc_id][index + i]:
                    if dist(chpt, (x, y)) < threshold:
                        risky_pt.add((x, y))
        feature = (len(risky_pt) / len(speed_planning)) if speed_planning else 0.0
        features[npc_id] = feature

    return features


def speed_constraints_checking(planning_msg, npc_points_gt, i, ev):
    feature = {}
    upperBound = []
    ev_traj = get_planning_trajectory(planning_msg)

    if 'debug' in planning_msg and 'planningData' in planning_msg['debug']:
        if 'stGraph' in planning_msg['debug']['planningData']:
            for stgraph in planning_msg['debug']['planningData']['stGraph']:
                if 'name' in stgraph and 'PIECEWISE_JERK_NONLINEAR_SPEED_OPTIMIZER' == stgraph['name']:
                    if 'speedConstraint' in stgraph and 'upperBound' in stgraph['speedConstraint']:
                        for v in stgraph['speedConstraint']['upperBound']:
                            upperBound.append(v)

    feature = get_vt_feature(npc_points_gt, ev_traj, i, ev, upperBound)

    return feature


def get_planning_trajectory(planning_msg):
    traj = []
    i = 0
    # x, y, s, v, t
    if 'trajectoryPoint' in planning_msg:
        for tjpt in planning_msg['trajectoryPoint']:
            if abs(tjpt['relativeTime'] - i * 0.1) < 0.01:
                v, t = tjpt['v'], tjpt['relativeTime']
                x, y, s = tjpt['pathPoint']['x'], tjpt['pathPoint']['y'], tjpt['pathPoint']['s']
                traj.append([x, y, s, v, t])
                i += 1
    return traj


def get_risky_st(npc_points_gt, ev_traj, ev, margin=0):
    st = []
    st_sum = 0

    threshold = sqrt(
        ev.front_edge_to_center * ev.front_edge_to_center + ev.left_edge_to_center * ev.left_edge_to_center) + margin

    for i in range(min(len(npc_points_gt), len(ev_traj))):
        x, y = ev_traj[i][0], ev_traj[i][1]
        for chpt in npc_points_gt[i]:
            st_sum += 1
            if dist(chpt, (x, y)) < threshold:
                st.append((ev_traj[i][2], ev_traj[i][-1]))  # x, y, s, v, t

    return st, st_sum


def get_sv_feature(npc_points_gt, ev_traj, index, ev, sv_list, margin=0):

    threshold = sqrt(
        ev.front_edge_to_center * ev.front_edge_to_center + ev.left_edge_to_center * ev.left_edge_to_center) + margin

    for i in range(len(ev_traj)):
        p = 0
        for j in range(p, len(sv_list)):
            if abs(ev_traj[i][2] - sv_list[j][0]) < 0.01:
                ev_traj[i][3] = sv_list[j][1]
                p = j
                break

    npc_ids = list(npc_points_gt.keys())
    features = {}
    for npc_id in npc_ids:
        risky_sv = set()
        # print('   ', npc_id, min(len(npc_points_gt[npc_id][index:]), len(ev_traj)))
        for i in range(min(len(npc_points_gt[npc_id][index:]), len(ev_traj))):
            x, y, v = ev_traj[i][0], ev_traj[i][1], ev_traj[i][3]  # x, y, s, v, t
            for chpt in npc_points_gt[npc_id][index + i]:
                # print('        distance: {}'.format(dist(chpt, (x, y))))
                if dist(chpt, (x, y)) < (threshold + 1 * v):
                    risky_sv.add((x, y))
        feature = (len(risky_sv) / len(ev_traj)) if ev_traj else 0.0
        features[npc_id] = feature

    return features


def get_vt_feature(npc_points_gt, ev_traj, index, ev, v_list, margin=0):

    threshold = sqrt(
        ev.front_edge_to_center * ev.front_edge_to_center + ev.left_edge_to_center * ev.left_edge_to_center) + margin

    for i in range(min(len(ev_traj), len(v_list))):
        ev_traj[i][3] = v_list[i]

    npc_ids = list(npc_points_gt.keys())
    features = {}
    for npc_id in npc_ids:
        risky_vt = set()
        for i in range(min(len(npc_points_gt[npc_id][index:]), len(ev_traj))):
            x, y, v = ev_traj[i][0], ev_traj[i][1], ev_traj[i][3]  # x, y, s, v, t
            for chpt in npc_points_gt[npc_id][index + i]:
                if dist(chpt, (x, y)) < (threshold + 1 * v):
                    risky_vt.add((x, y))
        feature = (len(risky_vt) / len(ev_traj)) if ev_traj else 0.0
        features[npc_id] = feature

    return features
