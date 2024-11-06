def object_decision_parser(object_decision):
    if 'ignore' in object_decision[0]:
        return 'ignore'
    elif 'stop' in object_decision[0]:
        return 'stop'
    elif 'follow' in object_decision[0]:
        return 'follow'
    elif 'yield' in object_decision[0]:
        return 'yield'
    elif 'overtake' in object_decision[0]:
        return 'overtake'
    elif 'nudge' in object_decision[0]:
        return 'nudge'
    elif 'avoid' in object_decision[0]:
        return 'avoid'
    elif 'sidePass' in object_decision[0]:
        return 'sidePass'
    return 'none'


def dp_st_object_decision_parser(object_decision):
    if 'ignore' in object_decision:
        return 'ignore'
    elif 'stop' in object_decision:
        return 'stop'
    elif 'follow' in object_decision:
        return 'follow'
    elif 'yield' in object_decision:
        return 'yield'
    elif 'overtake' in object_decision:
        return 'overtake'
    elif 'nudge' in object_decision:
        return 'nudge'
    elif 'avoid' in object_decision:
        return 'avoid'
    elif 'sidePass' in object_decision:
        return 'sidePass'
    return 'none'


def main_decision_parser(main_decision):
    if 'cruise' in main_decision:
        return 'cruise'
    elif 'stop' in main_decision:
        return 'stop'
    elif 'estop' in main_decision:
        return 'estop'
    elif 'changeLane' in main_decision:
        return 'changeLane'
    elif 'missionComplete' in main_decision:
        return 'missionComplete'
    elif 'notReady' in main_decision:
        return 'notReady'
    elif 'parking' in main_decision:
        return 'parking'
    return 'none'


def obj_id_string2int(obj_id_str):
    if '_0' in obj_id_str:
        obj_id_str_tmp = obj_id_str.replace('_0', '')
        if obj_id_str_tmp.isnumeric():
            return int(obj_id_str_tmp)
    if 'TL_' in obj_id_str:
        return obj_id_str.replace('TL_', '')
    if 'DEST' in obj_id_str:
        return 'DEST'
    return obj_id_str
