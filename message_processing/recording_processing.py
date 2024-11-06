import os
from .extractors.utils.map_parser import Map
from .extractors.utils.vehicle_parser import Vehicle
from .extractors.utils.recording_parsing import messages_aligning
from .util import get_all_npcs, dummy_obj_priority, dummy_interactive_tag, dummy_evaluator_dispatcher, \
    dummy_predictor_dispatcher, dummy_prediction_result, dummy_obj_decision, dummy_speed_planning
from .prediction_ import get_prediction_object_info, get_prediction_result
from .planning_ import get_planning_info
from .execution_ import has_accident_happened


def extracting(original_record_dir, map_params_dir, vehicle_params_dir, threshold_nearby, n_column=20):
    map = Map(map_params_dir)
    map.parse()
    ev = Vehicle(vehicle_params_dir)

    record_ = original_record_dir + '.0000'
    localization_msgs, obstacles_msgs, signal_msgs, prediction_msgs, planning_msgs = [], [], [], [], []

    for i in range(0, 10):
        record_i = record_ + str(i)
        if os.path.exists(record_i):
            localization_msgs_i, obstacles_msgs_i, signal_msgs_i, prediction_msgs_i, planning_msgs_i \
                = messages_aligning(record_i)
            localization_msgs += localization_msgs_i
            obstacles_msgs += obstacles_msgs_i
            signal_msgs += signal_msgs_i
            prediction_msgs += prediction_msgs_i
            planning_msgs += planning_msgs_i

    frames = []
    npcs_focused = set()

    npcs_id, npcs_traj_gt, npc_points_gt = get_all_npcs(obstacles_msgs, signal_msgs, n_column)

    for i in range(len(obstacles_msgs)):
        frame = []

        prediction_info = get_prediction_object_info(prediction_msgs[i], map)
        frame.append(object_dispatching(npcs_id, prediction_info[0], dummy_obj_priority))  # 0. prioritizer
        frame.append(object_dispatching(npcs_id, prediction_info[1], dummy_interactive_tag))  # 1. interactive tag
        frame.append(object_dispatching(npcs_id, prediction_info[2], dummy_evaluator_dispatcher))  # 2. evaluator
        frame.append(object_dispatching(npcs_id, prediction_info[3], dummy_predictor_dispatcher))  # 3. predictor

        prediction_ret = get_prediction_result(npcs_traj_gt, i, prediction_msgs[i])
        frame.append(object_dispatching(npcs_id, prediction_ret, dummy_prediction_result))  # 4. prediction result

        planning_info = get_planning_info(planning_msgs[i], npc_points_gt, i, ev)
        frame.append(object_dispatching(npcs_id, planning_info[0], dummy_obj_decision))  # 5. decision-making result
        frame.append(object_dispatching(npcs_id, planning_info[1], dummy_speed_planning))  # 6. speed planning result

        accident, npcs_nearby = has_accident_happened(localization_msgs[i], obstacles_msgs[i], ev, threshold_nearby)

        # Find npcs nearby
        for npc in npcs_nearby:
            npcs_focused.add(npc)
        # if accident:
        #     for npc in npcs_nearby:
        #         npcs_focused.add(npc)

        frames.append(frame)
        # print(frame)

    preprocessing_ret = frames

    return npcs_focused, npcs_id, preprocessing_ret


def processing(record_filename, map_params_dir, vehicle_params_dir): 
    npcs_indices = []
    # {'tags': 'CAUTION', 'evaluators': 'MLP_EVALUATOR', 'predictors': 'FREE_MOVE_PREDICTOR', 'prediction': 'pred_error', 'decisions': 'ignore', 'planning': 'pln_error'}
    new_infos = []
    npcs_focused, npcs_id, extraction_ret = extracting(record_filename, map_params_dir, vehicle_params_dir, threshold_nearby=50)
    for npc in npcs_focused: 
        npcs_indices.append(npcs_id.index(npc))
    # extraction_ret = [timesteps, 7 features, n_column(npc)]
    for timestep in extraction_ret: 
        for npc in npcs_indices: 
            new_info1, new_info2 = {}, {}
            new_info1['id'], new_info2['id'] = npc, npc
            new_info1['tags'], new_info2['tags'] = timestep[0][npc], timestep[1][npc]
            new_info1['evaluators'], new_info2['evaluators'] = timestep[2][npc], timestep[2][npc]
            new_info1['predictors'], new_info2['predictors'] = timestep[3][npc], timestep[3][npc]
            new_info1['prediction'], new_info2['prediction'] = timestep[4][npc], timestep[4][npc]
            new_info1['decisions'], new_info2['decisions'] = timestep[5][npc], timestep[5][npc]
            new_info1['planning'], new_info2['planning'] = timestep[6][npc], timestep[6][npc]
            new_infos.append(new_info1)
            new_infos.append(new_info2)
    return new_infos


def object_dispatching(npcs_id, npcs_dict, func):
    ret = []
    for obj in npcs_id:
        if obj in npcs_dict:
            ret.append(npcs_dict[obj])
        else:
            ret.append(func())
    # print(ret)
    return ret


def is_accident_recording(original_record_dir, map, ev, threshold_nearby): 
    record_ = original_record_dir + '.0000'
    localization_msgs, obstacles_msgs, signal_msgs, prediction_msgs, planning_msgs = [], [], [], [], []

    for i in range(0, 10):
        record_i = record_ + str(i)
        if os.path.exists(record_i): 
            localization_msgs_i, obstacles_msgs_i, signal_msgs_i, prediction_msgs_i, planning_msgs_i \
                = messages_aligning(record_i)
            localization_msgs += localization_msgs_i
            obstacles_msgs += obstacles_msgs_i
            signal_msgs += signal_msgs_i
            prediction_msgs += prediction_msgs_i
            planning_msgs += planning_msgs_i

    for i in range(len(obstacles_msgs)):
        accident, _ = has_accident_happened(localization_msgs[i], obstacles_msgs[i], ev, threshold_nearby)
        if accident: 
            return (original_record_dir, i)

    return (original_record_dir, -1)