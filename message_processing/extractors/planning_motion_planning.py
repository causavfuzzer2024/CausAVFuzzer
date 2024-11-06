from math import sqrt, dist
from .utils.st_graph_utils import get_planning_trajectory


def motion_planning_result(planning_msg, npc_points_gt, index, ev, margin=0):
    features = {}

    ev_traj = get_planning_trajectory(planning_msg)
    threshold = sqrt(
        ev.front_edge_to_center * ev.front_edge_to_center + ev.left_edge_to_center * ev.left_edge_to_center) + margin
    npc_ids = list(npc_points_gt.keys())
    for npc_id in npc_ids:
        risky_pt = set()
        for pt in ev_traj:  # x, y, s, v, t
            x, y = pt[0], pt[1]
            for i in range(len(npc_points_gt[npc_id][index:])):
                for chpt in npc_points_gt[npc_id][index + i]:
                    if dist(chpt, (x, y)) < threshold:
                        risky_pt.add((x, y))
        feature = (len(risky_pt) / len(ev_traj)) if ev_traj else 0.0
        if feature > 0: 
            features[npc_id] = 'PLN_ERROR'
        else: 
            features[npc_id] = 'NO_PLN_ERROR'

    return features
