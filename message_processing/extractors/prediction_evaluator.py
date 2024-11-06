def evaluator_assigning(features):
    npc_ids = list(features.keys())
    evaluators = {}
    for npc in npc_ids:
        type_curr, area_curr, speed_curr, priority_curr, tag_curr = features[npc]['type'], features[npc]['area'], \
            features[npc]['speed'], features[npc]['priority'], features[npc]['tag']
        # evaluators[npc] = 'skip_evaluating'
        if 'VEHICLE' == type_curr:
            if 'ON_LANE' == area_curr:
                if 'CAUTION' == priority_curr:
                    evaluators[npc] = 'CRUISE_MLP_EVALUATOR'
                else:
                    evaluators[npc] = 'CRUISE_MLP_EVALUATOR'
            if 'JUNCTION' == area_curr:
                if 'CAUTION' == priority_curr:
                    evaluators[npc] = 'JUNCTION_MAP_EVALUATOR'
                else:
                    evaluators[npc] = 'JUNCTION_MLP_EVALUATOR'
            continue  # Evaluate
        elif 'BICYCLE' == type_curr:
            if 'ON_LANE' == area_curr:
                evaluators[npc] = 'CYCLIST_KEEP_LANE_EVALUATOR'
        elif 'PEDESTRIAN' == type_curr:
            if 'CAUTION' == priority_curr:
                evaluators[npc] = 'SEMANTIC_LSTM_EVALUATOR'
        else:
            if 'ON_LANE' == area_curr:
                evaluators[npc] = 'MLP_EVALUATOR'
    return evaluators
