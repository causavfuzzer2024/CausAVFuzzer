from .planning_lane_follow import lane_follow_default_stage, dummy_planning_result
from .planning_traffic_light_protected import traffic_light_protected_approach_stage, \
    traffic_light_protected_intersection_cruise_stage


def get_planning_info(planning_msg, npc_points_gt, i, ev):
    scenario, stage = get_planning_scenario_stage(planning_msg)
    planning_info = dummy_planning_info(planning_msg, npc_points_gt, i, ev)
    if 'LANE_FOLLOW' == scenario:
        # print('LANE_FOLLOW')
        if 'LANE_FOLLOW_DEFAULT_STAGE' == stage:
            planning_info = lane_follow_default_stage(planning_msg, npc_points_gt, i, ev)
            # print('LANE_FOLLOW_DEFAULT_STAGE', len(planning_info), planning_info[-1])
    elif 'TRAFFIC_LIGHT_PROTECTED' == scenario:
        # print('TRAFFIC_LIGHT_PROTECTED')
        if 'TRAFFIC_LIGHT_PROTECTED_APPROACH' == stage:
            planning_info = traffic_light_protected_approach_stage(planning_msg, npc_points_gt, i, ev)
            # print('TRAFFIC_LIGHT_PROTECTED_APPROACH', len(planning_info), planning_info[-1])
        elif 'TRAFFIC_LIGHT_PROTECTED_INTERSECTION_CRUISE' == stage:
            planning_info = traffic_light_protected_intersection_cruise_stage(planning_msg, npc_points_gt, i, ev)
            # print('TRAFFIC_LIGHT_PROTECTED_INTERSECTION_CRUISE', len(planning_info), planning_info[-1])
    return planning_info


def get_planning_scenario_stage(planning_msg):
    if 'debug' in planning_msg and 'planningData' in planning_msg['debug'] and \
            'scenario' in planning_msg['debug']['planningData']:
        scenario = planning_msg['debug']['planningData']['scenario']
        if 'scenarioType' in scenario and 'stageType' in scenario:
            return scenario['scenarioType'], scenario['stageType']
    return '', ''


def dummy_planning_info(planning_msg, npc_points_gt, i, ev):
    return dummy_planning_result(planning_msg, npc_points_gt, i, ev)
