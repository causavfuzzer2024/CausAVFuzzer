from .extractors.prediction_scenario_analyzer import get_npc_feature
from .extractors.prediction_evaluator import evaluator_assigning
from .extractors.prediction_predictor import predictor_assigning, trajectories_predicting
from math import dist


def get_prediction_object_info(prediction_msg, map):
    features = get_npc_feature(prediction_msg, map)
    priorities = {}  # prioritizer
    interactive_tag = {}  # interactive tag
    npc_id = list(features.keys())
    for npc in npc_id:
        priorities[npc] = features[npc]['priority']
        interactive_tag[npc] = features[npc]['tag']
    evaluator = evaluator_assigning(features)  # evaluator
    predictor = predictor_assigning(features)  # predictor
    prediction_info = [priorities, interactive_tag, evaluator, predictor]
    return prediction_info


def get_prediction_result(npcs_traj_gt, index_curr, prediction_msg):
    prediction_result = {}
    npcs_traj_pred = trajectories_predicting(prediction_msg)
    npcs_id_all = list(npcs_traj_gt.keys())
    for id in npcs_id_all:
        prediction_result[id] = 'NO_PRED_ERROR'
    npcs_id_curr = list(npcs_traj_pred.keys())
    for id in npcs_id_curr:
        if id in npcs_traj_gt:
            npc_traj_gt_seg = npcs_traj_gt[id][index_curr:]
            for traj_p in npcs_traj_pred[id]:
                traj = traj_p[-1]
                error_sum, counter = 0, 0
                # error_sum = 0
                len_traj = min(len(npc_traj_gt_seg), len(traj))
                for i in range(len_traj):
                    if (-1, -1) != npc_traj_gt_seg[i]:
                        error_sum += dist(npc_traj_gt_seg[i], traj[i])
                        counter += 1
                error_sum /= counter if counter else 1
                if error_sum > 0.8: 
                    prediction_result[id] = 'PRED_ERROR'
                else: 
                    prediction_result[id] = 'NO_PRED_ERROR'
    return prediction_result
