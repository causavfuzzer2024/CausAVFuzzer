def predictor_assigning(features):
    npc_ids = list(features.keys())
    predictors = {}
    for npc in npc_ids:
        type_curr, area_curr, speed_curr, priority_curr, tag_curr, is_static = \
            features[npc]['type'], features[npc]['area'], features[npc]['speed'], features[npc]['priority'], \
            features[npc]['tag'], features[npc]['is_static']
        # predictors[npc] = ''
        predictors[npc] = ''
        if 'IGNORE' == priority_curr:
            predictors[npc] = 'EMPTY_PREDICTOR'
        elif is_static:
            predictors[npc] = 'EMPTY_PREDICTOR'
        else:
            if 'VEHICLE' == type_curr:
                if 'INTERACTION' == tag_curr:
                    predictors[npc] = 'EMPTY_PREDICTOR'
                    continue  # Predict
                if 'CAUTION' == priority_curr:
                    if 'JUNCTION' == area_curr:
                        predictors[npc] = 'INTERACTION_PREDICTOR'
                    elif 'ON_LANE' == area_curr:
                        predictors[npc] = 'MOVE_SEQUENCE_PREDICTOR'
                    else:
                        predictors[npc] = 'EXTRAPOLATION_PREDICTOR'
                    continue  # Predict
                if 'OFF_LANE' == area_curr:
                    predictors[npc] = 'FREE_MOVE_PREDICTOR'
                elif 'JUNCTION' == area_curr:
                    predictors[npc] = 'LANE_SEQUENCE_PREDICTOR'
                else:
                    predictors[npc] = 'LANE_SEQUENCE_PREDICTOR'
                continue  # Predict
            elif 'PEDESTRIAN' == type_curr:
                predictors[npc] = 'FREE_MOVE_PREDICTOR'
            elif 'BICYCLE' == type_curr:
                if 'OFF_LANE' == area_curr:
                    predictors[npc] = 'FREE_MOVE_PREDICTOR'
                else:
                    predictors[npc] = 'LANE_SEQUENCE_PREDICTOR'
            else:
                if 'OFF_LANE' == area_curr:
                    predictors[npc] = 'FREE_MOVE_PREDICTOR'
                else:
                    predictors[npc] = 'LANE_SEQUENCE_PREDICTOR'
    return predictors


def trajectories_predicting(prediction_msg):
    traj_pred = {}
    if 'predictionObstacle' in prediction_msg:
        for obs in prediction_msg['predictionObstacle']:
            obs_id, obs_trajs = 0, []
            if 'perceptionObstacle' in obs and 'id' in obs['perceptionObstacle']:
                obs_id = obs['perceptionObstacle']['id']
            if 'trajectory' in obs:
                for traj in obs['trajectory']:
                    probability, traj_points = 0, []
                    if 'probability' in traj:
                        probability = traj['probability']
                    for tp in traj['trajectoryPoint']:
                        waypoint = (tp['pathPoint']['x'], tp['pathPoint']['y'])
                        # theta, v, a = tp['pathPoint']['theta'], tp['v'], tp['a']
                        # traj_points.append((waypoint, theta, v, a))
                        traj_points.append(waypoint)
                    obs_trajs.append((probability, traj_points))
            traj_pred[obs_id] = obs_trajs
    return traj_pred