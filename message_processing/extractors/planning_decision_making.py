from .utils.parser_utils import object_decision_parser, obj_id_string2int


def decision_making_result(planning_msg):
    object_decisions = {}
    if 'decision' in planning_msg and 'objectDecision' in planning_msg['decision']:
        if 'decision' in planning_msg['decision']['objectDecision']:
            for decs in planning_msg['decision']['objectDecision']['decision']:
                ob_id = obj_id_string2int(decs['id'])
                if 'objectDecision' in decs:
                    ob_decs = object_decision_parser(decs['objectDecision'])
                    object_decisions[ob_id] = ob_decs
    return object_decisions
