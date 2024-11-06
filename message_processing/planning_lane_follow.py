from .extractors.planning_decision_making import decision_making_result
from .extractors.planning_motion_planning import motion_planning_result


def lane_follow_default_stage(planning_msg, npc_points_gt, i, ev):
    decn_ret = decision_making_result(planning_msg)
    spd_ret = motion_planning_result(planning_msg, npc_points_gt, i, ev)

    planning_info = [decn_ret, spd_ret]
    return planning_info


def dummy_planning_result(planning_msg, npc_points_gt, i, ev):
    decn_ret = decision_making_result(planning_msg)
    spd_ret = motion_planning_result(planning_msg, npc_points_gt, i, ev)

    planning_info = [decn_ret, spd_ret]
    return planning_info
