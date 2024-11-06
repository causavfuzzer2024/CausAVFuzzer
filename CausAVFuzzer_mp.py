import copy
import os
import select
import shutil
import signal
import sys
import time
import warnings
from pathlib import Path
from threading import Timer

import websockets
import json
import asyncio
from EXtraction import ExtractAll
from GeneticAlgorithm import CAVGAGeneration, EncodedTestCase, DecodedTestCase
from TestCaseRandom import TestCaseRandom
from datetime import datetime
from AssertionExtraction import SingleAssertion
from map import get_map_info
from monitor import Monitor
import logging
from spec_coverage import failure_statement
from multiprocessing import Pool

from CDModel import CAVGraph


def processing_testcases(encoded_testcase): 
    new_components = encoded_testcase.check_diverity_update()  # For updating diversity seeds
    if encoded_testcase.diversity:  # DO find a new behavior, BUT
        # encode_testcase.fitness > 0.0, NOT find a way to violate specifications
        if encoded_testcase.muti_fitness == {}:
            encoded_testcase.compute_muti_fitness()
        # logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
        logging.info("      Diversity Value: {}".format(encoded_testcase.diversity))
        # update the global cav graph
        cavgraph = encoded_testcase.get_cav_graph_updated()  # global: cav_graph
        return new_components, cavgraph
    return None, None


def newlist(parent_list, list1):
    new_element = [element for element in list1 if element not in parent_list]
    return new_element


def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, indent=4)


async def hello(scenario_msg, single_spec, generation_number=1, population_size=3, directory=None, ads_pipeline=[], map_params_dir='', vehicle_params_dir='') -> object:

    maximun = len(single_spec.sub_violations)
    remaining_sub_violations = single_spec.sub_violations

    cavgraph = CAVGraph(ads_pipeline)

    seed_spec = dict()
    mapping_spec = dict()
    # for item in remaining_sub_violations:
    #     mapping_spec[item] = -1000
    #     seed_spec[item] = None

    seed_dive = dict()
    mapping_dive = dict()
    

    # print(mapping)
    # print(seed)
    
    # spec_str = single_spec.translated_statement
    # negative_predicate_obj = failure_statement(spec_str)
    # all_predicates = negative_predicate_obj.neg_predicate()
    # all_covered_predicates = set()

    uri = "ws://localhost:8000"
    async with websockets.connect(uri,  max_size= 300000000, ping_interval=None) as websocket:
        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
        await websocket.send(init_msg)
        msg = await websocket.recv()
        msg = json.loads(msg)
        if msg['TYPE'] == 'READY_FOR_NEW_TEST' and msg['DATA']:
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            with open(directory + '/Incompleted.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            with open(directory + '/bugTestCase.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            with open(directory + '/NoTrace.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            population_spec, population_dive = [], []
            new_testcases = []
            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
            await websocket.send(init_msg)
            if len(scenario_msg) < population_size:
                test_case = scenario_msg[0]
                testcase = TestCaseRandom(test_case)
                testcase.testcase_random(population_size - len(scenario_msg))
                for i2 in range(len(testcase.cases) - 1):
                    scenario_msg.append(testcase.cases[i2 + 1])

            # Process with the initial generation(random)
            encoded_testcases_generation = []  # For batch processing
            for i in range(population_size):
                testcase_name = '{}_{}'.format(0, i+1)
                while True:
                    msg = await websocket.recv()
                    msg = json.loads(msg)
                    if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                        if msg['DATA']:
                            logging.info('Running Generation: 0, Individual: {}'.format(i + 1))
                            send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': scenario_msg[i], 'NAME': testcase_name}
                            await websocket.send(json.dumps(send_msg))  # Begin to test a new scenario
                            # filename = "G0-I{}".format(i + 1)
                            # process = multiprocessing.Process(target=recorder, args=(filename,))
                            # process.start()
                            # time.sleep(1)
                            # process.terminate()
                        else:
                            asyncio.sleep(3)
                            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                            await websocket.send(init_msg)
                    elif msg['TYPE'] == 'KEEP_SERVER_AND_CLIENT_ALIVE':
                        send_msg = {'CMD': "KEEP_SERVER_AND_CLIENT_ALIVE", 'DATA': None}
                        await websocket.send(json.dumps(send_msg))
                    elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                        print("Try to reconnect!")
                        asyncio.sleep(1)
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        await websocket.send(init_msg)
                    elif msg['TYPE'] == 'TEST_COMPLETED':
                        output_trace = msg['DATA']
                        now = datetime.now()
                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        file = directory + '/data/result' + dt_string + '.json'
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        with open(file, 'w') as outfile:
                            json.dump(output_trace, outfile, indent=2)
                        if not output_trace['destinationReached']:
                            logging.info("Not reach the destination")
                            with open(directory + '/Incompleted.txt', 'a') as f:
                                json.dump(scenario_msg[i], f, indent=2)
                                f.write('\n')
                        if len(output_trace['trace']) > 1:  # MARK: start processing testcases
                            encoded_testcase = EncodedTestCase(output_trace, single_spec, testcase_name, cavgraph, map_params_dir, vehicle_params_dir)
                            encoded_testcases_generation.append(encoded_testcase)  # For batch processing
                            if 'Accident!' in output_trace["testFailures"]: 
                                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST", 'NAME': testcase_name})
                                encoded_testcase.compute_muti_fitness()
                                # Save the accident testcase
                                with open(directory + '/AccidentTestCase.txt', 'a') as bug_file:
                                    now = datetime.now()
                                    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                    string_index = "Time:" + dt_string + "Generation: " + str(0) + ", Individual: " + str(i + 1) +", Bug: " + str(output_trace["testFailures"]) +'\n'
                                    bug_file.write(string_index)
                                    string_index2 = "The detailed fitness values:" + str(encoded_testcase.muti_fitness) + '\n'
                                    bug_file.write(string_index2)
                                    json.dump(output_trace, bug_file, indent=2)
                                    bug_file.write('\n')   
                                with open(directory + '/AccidentRecordings.txt', 'a') as record_file: 
                                    record_file.write(f'{testcase_name} \n')
                            covered = []
                            if encoded_testcase.fitness <= 0.0:  # DO find a way to violate specifications
                                if encoded_testcase.muti_fitness == {}:
                                    encoded_testcase.compute_muti_fitness()
                                logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                # logging.info("      Diversity Value: {}".format(encoded_testcase.diversity))
                                monitor = Monitor(output_trace, 0)
                                for spec in remaining_sub_violations:                                  
                                    fitness0 = monitor.continuous_monitor2(spec)                                                                         
                                    if fitness0 >= 0.0:
                                        covered.append(spec)
                                        #####
                                        # Example of adding seeds to corpus in LawBreaker: 
                                        # seed_spec[spec] = encoded_testcase
                                        # mapping_spec[spec] = fitness0
                                        #####
                                        # Add it to the spec corpus
                                        seed_spec[spec] = encoded_testcase
                                        mapping_spec[spec] = fitness0
                                    else:
                                        if spec in mapping_spec:
                                            if mapping_spec[spec] < fitness0:
                                                seed_spec[spec] = encoded_testcase
                                                mapping_spec[spec] = fitness0
                                        else:
                                            seed_spec[spec] = encoded_testcase
                                            mapping_spec[spec] = fitness0
                                for itme in covered:
                                    remaining_sub_violations.remove(itme)
                                    # del seed_spec[itme]
                                    # del mapping_spec[itme]
                            else: 
                                logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                monitor = Monitor(output_trace, 0)
                                for spec in remaining_sub_violations:                                  
                                    fitness0 = monitor.continuous_monitor2(spec)     
                                    assert fitness0 < 0.0                                                                                                             
                                    if fitness0 < 0.0: 
                                        if mapping_spec[spec] < fitness0:
                                            seed_spec[spec] = encoded_testcase
                                            mapping_spec[spec] = fitness0
                                for itme in covered:
                                    remaining_sub_violations.remove(itme)
                                    # del seed[itme]
                                    # del mapping[itme]
                            del encoded_testcase.trace 
                            # MARK: stop processing testcases
                        elif len(output_trace['trace']) == 1:
                            testcase = TestCaseRandom(output_trace)
                            testcase.testcase_random(1)
                            new_testcases.append(testcase.cases[-1])
                        else:
                            logging.info("No trace for the test cases")
                            with open(directory + '/NoTrace.txt', 'a') as f:
                                json.dump(scenario_msg[i], f, indent=2)
                                f.write('\n')
                            testcase = TestCaseRandom(output_trace)
                            testcase.testcase_random(1)
                            new_testcases.append(testcase.cases[-1])
                        await websocket.send(init_msg)
                        break
            
            # Get candidate parents for generation 1
            coverage_rate = 1- len(remaining_sub_violations) / maximun
            logging.info("total coverage rate: {}/{} = {}, uncovered predicates: {}\n".format((maximun - len(remaining_sub_violations)), maximun, coverage_rate, remaining_sub_violations))
            # MARK: batch processing
            with Pool(processes=10) as pool:
                results = [pool.apply_async(processing_testcases, args=(et,)) for et in encoded_testcases_generation]
                batch_results = [result.get() for result in results]
            for result_individual in batch_results: 
                components_updated, graph_curr = result_individual[0], result_individual[1]
                if components_updated: 
                    for new_component in components_updated: 
                        diversity_score = len(components_updated)
                        if new_component in seed_dive: 
                            if diversity_score >= mapping_dive[new_component]: 
                                seed_dive[new_component] = encoded_testcase
                                mapping_dive[new_component] = diversity_score
                        else: 
                            seed_dive[new_component] = encoded_testcase
                            mapping_dive[new_component] = diversity_score
                if graph_curr: 
                    cavgraph.add_graph(graph_curr)
            # MARK: end batch processing
            logging.info("total detected components: {}\n".format(len(list(seed_dive.keys()))))
            cavgraph.show_relations()
            print()
            # For specifications
            mapping_spec = sorted(mapping_spec.items(), key=lambda item: item[1], reverse=True)
            mapping_spec = dict(mapping_spec)
            # For diversity
            mapping_dive = sorted(mapping_dive.items(), reverse=True)
            mapping_dive = dict(mapping_dive)
            # print(mapping)
            if generation_number:
                for key in mapping_spec:
                    population_spec.append(seed_spec[key])
                    population_spec[-1].fitness = mapping_spec[key]
                for key in mapping_dive: 
                    population_dive.append(seed_dive[key])
                    population_dive[-1].fitness = mapping_dive[key]
                new_population_obj = CAVGAGeneration(population_spec, population_dive, crossover_prob=0.8, mutation_prob=0.8)
                new_population = new_population_obj.one_generation_cav(population_size)  # MARK
                
                decoder = DecodedTestCase(new_population)
                next_new_testcases = decoder.decoding()
                new_testcases = copy.deepcopy(next_new_testcases)
                assert len(new_testcases)==population_size

                with open(directory + '/TestCase.txt', 'w') as outfile:
                    for i1 in range(len(new_testcases)):
                        json.dump(new_testcases[i1], outfile, indent=2)
                        outfile.write('\n')

                # Begin GA
                for generation in range(generation_number-1):
                    # covered_predicates = []
                    improved_trace = None
                    population_spec, population_dive = [], []
                    encoded_testcases_generation = []  # For batch processing
                    next_new_testcases = []
                    if len(new_testcases) < population_size:
                        print('checking the number of test cases')
                    for j in range(len(new_testcases)):
                        testcase_name = '{}_{}'.format(generation + 1, j+1)
                        # deal with each test case
                        while True:
                            msg = await websocket.recv()
                            msg = json.loads(msg)
                            # print(msg['TYPE'])
                            if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                                if msg['DATA']:
                                    logging.info('Running Generation: {}, Individual: {}'.format(generation + 1, j + 1))
                                    send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': new_testcases[j], 'NAME': testcase_name}
                                    await websocket.send(json.dumps(send_msg))  # Begin to test a new scenario
                                    # filename = "G{}-I{}".format(generation + 1, j + 1)
                                    # process = multiprocessing.Process(target=recorder, args=(filename,))
                                    # process.start()
                                    # time.sleep(1)
                                    # process.terminate()
                                else:
                                    asyncio.sleep(3)
                                    init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                                    await websocket.send(init_msg)
                            elif msg['TYPE'] == 'KEEP_SERVER_AND_CLIENT_ALIVE':
                                send_msg = {'CMD': "KEEP_SERVER_AND_CLIENT_ALIVE", 'DATA': None}
                                await websocket.send(json.dumps(send_msg))
                            elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                                # print(msg)
                                print("Try to reconnect.")
                                asyncio.sleep(1)
                                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                                await websocket.send(init_msg)
                            elif msg['TYPE'] == 'TEST_COMPLETED':
                                output_trace = msg['DATA']
                                now = datetime.now()
                                dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                file = directory + '/data/result' + dt_string + '.json'
                                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                                with open(file, 'w') as outfile:
                                    json.dump(output_trace, outfile, indent=2)
                                logging.info(
                                    "The number of states in the trace is {}".format(len(output_trace['trace'])))
                                if not output_trace['destinationReached']:
                                    with open(directory + '/Incompleted.txt', 'a') as f:
                                        json.dump(new_testcases[j], f, indent=2)
                                        f.write('\n')
                                if len(output_trace['trace']) > 1:  # MARK: start processing testcases
                                    encoded_testcase = EncodedTestCase(output_trace, single_spec, testcase_name, cavgraph, map_params_dir, vehicle_params_dir)
                                    encoded_testcases_generation.append(encoded_testcase)  # For batch processing
                                    # del encoded_testcase.trace                       
                                    if 'Accident!' in output_trace["testFailures"]: 
                                        # if encoded_testcase.muti_fitness == {}:
                                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST", 'NAME': testcase_name})
                                        encoded_testcase.compute_muti_fitness()
                                        # Save the accident testcase
                                        with open(directory + '/AccidentTestCase.txt', 'a') as bug_file:
                                            now = datetime.now()
                                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                            string_index = "Time:" + dt_string + "Generation: " + str(generation) + ", Individual: " + str(j+1) +", Bug: " + str(output_trace["testFailures"]) +'\n'
                                            bug_file.write(string_index)
                                            string_index2 = "The detailed fitness values:" + str(encoded_testcase.muti_fitness) + '\n'
                                            bug_file.write(string_index2)
                                            json.dump(output_trace, bug_file, indent=2)
                                            bug_file.write('\n') 
                                        with open(directory + '/AccidentRecordings.txt', 'a') as record_file: 
                                            record_file.write(f'{testcase_name} \n')  
                                    covered = []
                                    if encoded_testcase.fitness <= 0.0:  # Do find a way to violate specifications
                                        if encoded_testcase.muti_fitness == {}:
                                            encoded_testcase.compute_muti_fitness()
                                        logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                        # logging.info("      Diversity Value: {}".format(encoded_testcase.diversity))
                                        monitor = Monitor(output_trace, 0)
                                        for spec in remaining_sub_violations:                                  
                                            fitness0 = monitor.continuous_monitor2(spec)                                                                          
                                            if fitness0 >= 0.0:
                                                covered.append(spec)
                                                # Add it to the spec corpus     
                                                seed_spec[spec] = encoded_testcase
                                                mapping_spec[spec] = fitness0
                                            else:
                                                if spec in mapping_spec:
                                                    if mapping_spec[spec] < fitness0:
                                                        seed_spec[spec] = encoded_testcase
                                                        mapping_spec[spec] = fitness0
                                                else:
                                                    seed_spec[spec] = encoded_testcase
                                                    mapping_spec[spec] = fitness0
                                        for itme in covered:
                                            remaining_sub_violations.remove(itme)
                                            # del seed_spec[itme]
                                            # del mapping_spec[itme]
                                    else: 
                                        logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                        monitor = Monitor(output_trace, 0)
                                        for spec in remaining_sub_violations:                                  
                                            fitness0 = monitor.continuous_monitor2(spec)     
                                            assert fitness0 < 0.0                                                                                                             
                                            if fitness0 < 0.0: 
                                                if mapping_spec[spec] < fitness0:
                                                    seed_spec[spec] = encoded_testcase
                                                    mapping_spec[spec] = fitness0
                                        for itme in covered:
                                            remaining_sub_violations.remove(itme)
                                            # del seed[itme]
                                            # del mapping[itme]
                                    del encoded_testcase.trace 
                                    # MARK: stop processing testcases
                                elif len(output_trace['trace']) == 1:
                                    logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                                        output_trace['destinationReached'], output_trace['minEgoObsDist']))
                                    # testcase = TestCaseRandom(output_trace)
                                    # testcase.testcase_random(1)
                                    # next_new_testcases.append(testcase.cases[-1])
                                else:
                                    # testcase = TestCaseRandom(output_trace)
                                    # testcase.testcase_random(1)
                                    # next_new_testcases.append(testcase.cases[-1])
                                    logging.info("No trace for the test cases!")
                                    with open(directory + '/NoTrace.txt', 'a') as f:
                                        now = datetime.now()
                                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                        f.write("Time: Generation: {}, Individual: {}".format(dt_string, generation + 1, j))
                                        json.dump(new_testcases[j], f, indent=2)
                                        f.write('\n')
                                await websocket.send(init_msg)
                                break
                    
                    # Get candidate parents for next generations
                    coverage_rate = 1- len(remaining_sub_violations) / maximun
                    logging.info("total coverage rate: {}/{} = {}, uncovered predicates: {}\n".format((maximun - len(remaining_sub_violations)), maximun, coverage_rate, remaining_sub_violations))
                    # MARK: batch processing
                    with Pool(processes=10) as pool:
                        results = [pool.apply_async(processing_testcases, args=(et,)) for et in encoded_testcases_generation]
                        batch_results = [result.get() for result in results]
                    for result_individual in batch_results: 
                        components_updated, graph_curr = result_individual[0], result_individual[1]
                        if components_updated: 
                            for new_component in components_updated: 
                                diversity_score = len(components_updated)
                                if new_component in seed_dive: 
                                    if diversity_score >= mapping_dive[new_component]: 
                                        seed_dive[new_component] = encoded_testcase
                                        mapping_dive[new_component] = diversity_score
                                else: 
                                    seed_dive[new_component] = encoded_testcase
                                    mapping_dive[new_component] = diversity_score
                        if graph_curr: 
                            cavgraph.add_graph(graph_curr)
                    # MARK: end batch processing
                    logging.info("total detected components: {}\n".format(len(list(seed_dive.keys()))))
                    cavgraph.show_relations()
                    print()
                    # For specifications
                    mapping_spec = sorted(mapping_spec.items(), key=lambda item: item[1], reverse=True)
                    mapping_spec = dict(mapping_spec)
                    # For diversity
                    mapping_dive = sorted(mapping_dive.items(), reverse=True)
                    mapping_dive = dict(mapping_dive)
                    # print(mapping)
                    for key in mapping_spec:
                        population_spec.append(seed_spec[key])
                        population_spec[-1].fitness = mapping_spec[key]
                    for key in mapping_dive: 
                        population_dive.append(seed_dive[key])
                        population_dive[-1].fitness = mapping_dive[key]
                    new_population_obj = CAVGAGeneration(population_spec, population_dive, crossover_prob=0.8, mutation_prob=0.8)
                    new_population = new_population_obj.one_generation_cav(population_size)  # MARK
                    
                    decoder = DecodedTestCase(new_population)
                    next_new_testcases = decoder.decoding()
                    new_testcases = copy.deepcopy(next_new_testcases)
                    assert len(new_testcases)==population_size
                    # if len(next_new_testcases) < population_size:
                    #     if improved_trace is None:
                    #         improved_trace = output_trace
                    #     testcase = TestCaseRandom(improved_trace)
                    #     testcase.testcase_random(population_size - len(next_new_testcases))
                    #     for i2 in range(len(testcase.cases) - 1):
                    #         next_new_testcases.append(testcase.cases[i2 + 1])
                    # new_testcases = copy.deepcopy(next_new_testcases)
                    with open(directory + '/TestCase.txt', 'a') as outfile:
                        for i in range(len(new_testcases)):
                            try:
                                json.dump(new_testcases[i], outfile, indent=2)
                                outfile.write('\n')
                            except TypeError:
                                logging.info("Check the types of test cases")
                #  The last generation
                # improved_trace = None
                # covered_predicates = []
                
                # The final generation
                generation += 2
                next_new_testcases = []
                for j in range(len(new_testcases)):
                    testcase_name = '{}_{}'.format(generation, j+1)
                    while True:
                        msg = await websocket.recv()
                        msg = json.loads(msg)
                        # print(msg['TYPE'])
                        if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                            if msg['DATA']:
                                logging.info('Running Generation: {}, Individual: {}'.format(generation, j + 1))
                                send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': new_testcases[j], 'NAME': testcase_name}
                                await websocket.send(json.dumps(send_msg))  # Begin to test a new scenario
                                # filename = "G{}-I{}".format(generation, j + 1)
                                # process = multiprocessing.Process(target=recorder, args=(filename,))
                                # process.start()
                                # time.sleep(1)
                                # process.terminate()
                            else:
                                time.sleep(3)
                                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                                await websocket.send(init_msg)
                        elif msg['TYPE'] == 'KEEP_SERVER_AND_CLIENT_ALIVE':
                            send_msg = {'CMD': "KEEP_SERVER_AND_CLIENT_ALIVE", 'DATA': None}
                            await websocket.send(json.dumps(send_msg))
                        elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                            # print(msg)
                            print("Try to reconnect.")
                            time.sleep(1)
                            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                            await websocket.send(init_msg)

                        elif msg['TYPE'] == 'TEST_COMPLETED':
                            output_trace = msg['DATA']
                            now = datetime.now()
                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                            file = directory + '/data/result' + dt_string + '.json'
                            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                            with open(file, 'w') as outfile:
                                json.dump(output_trace, outfile, indent=2)
                            logging.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                            if not output_trace['destinationReached']:
                                with open(directory + '/Incompleted.txt', 'a') as f:
                                    json.dump(new_testcases[j], f, indent=2)
                                    f.write('\n')
                            if len(output_trace['trace']) > 1:  # MARK: start processing testcases
                                encoded_testcase = EncodedTestCase(output_trace, single_spec, testcase_name, cavgraph, map_params_dir, vehicle_params_dir)
                                encoded_testcases_generation.append(encoded_testcase)  # For batch processing
                                # del encoded_testcase.trace                       
                                if 'Accident!' in output_trace["testFailures"]: 
                                    init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST", 'NAME': testcase_name})
                                    encoded_testcase.compute_muti_fitness()  
                                    # Save the accident testcase
                                    with open(directory + '/AccidentTestCase.txt', 'a') as bug_file:
                                        now = datetime.now()
                                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                        string_index = "Time:" + dt_string + "Generation: " + str(generation) + ", Individual: " + str(j + 1) +", Bug: " + str(output_trace["testFailures"]) +'\n'
                                        bug_file.write(string_index)
                                        string_index2 = "The detailed fitness values:" + str(encoded_testcase.muti_fitness) + '\n'
                                        bug_file.write(string_index2)
                                        json.dump(output_trace, bug_file, indent=2)
                                        bug_file.write('\n')  
                                    with open(directory + '/AccidentRecordings.txt', 'a') as record_file: 
                                        record_file.write(f'{testcase_name} \n')
                                covered = []
                                if encoded_testcase.fitness <= 0.0:  # Do find a way to violate specifications
                                    if encoded_testcase.muti_fitness == {}:
                                        encoded_testcase.compute_muti_fitness()
                                    logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                    # logging.info("      Diversity Value: {}".format(encoded_testcase.diversity))
                                    monitor = Monitor(output_trace, 0)
                                    for spec in remaining_sub_violations:                                  
                                        fitness0 = monitor.continuous_monitor2(spec)                                                                       
                                        if fitness0 >= 0.0:
                                            covered.append(spec)
                                            # Add it to the spec corpus
                                            seed_spec[spec] = encoded_testcase
                                            mapping_spec[spec] = fitness0
                                        else:
                                            if spec in mapping_spec:
                                                if mapping_spec[spec] < fitness0:
                                                    seed_spec[spec] = encoded_testcase
                                                    mapping_spec[spec] = fitness0
                                            else:
                                                seed_spec[spec] = encoded_testcase
                                                mapping_spec[spec] = fitness0
                                    for itme in covered:
                                        remaining_sub_violations.remove(itme)
                                        # del seed_spec[itme]
                                        # del mapping_spec[itme]
                                else: 
                                    logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                    monitor = Monitor(output_trace, 0)
                                    for spec in remaining_sub_violations:                                  
                                        fitness0 = monitor.continuous_monitor2(spec)     
                                        assert fitness0 < 0.0                                                                                                             
                                        if fitness0 < 0.0: 
                                            if mapping_spec[spec] < fitness0:
                                                seed_spec[spec] = encoded_testcase
                                                mapping_spec[spec] = fitness0
                                    for itme in covered:
                                        remaining_sub_violations.remove(itme)
                                        # del seed[itme]
                                        # del mapping[itme]
                                del encoded_testcase.trace 
                                # MARK: stop processing testcases
                            elif len(output_trace['trace']) == 1:
                                logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                                    output_trace['destinationReached'], output_trace['minEgoObsDist']))
                                # testcase = TestCaseRandom(output_trace)
                                # testcase.testcase_random(1)
                                # next_new_testcases.append(testcase.cases[-1])
                            else:
                                # testcase = TestCaseRandom(output_trace)
                                # testcase.testcase_random(1)
                                # next_new_testcases.append(testcase.cases[-1])
                                logging.info("No trace for the test cases!")
                                with open(directory + '/NoTrace.txt', 'a') as f:
                                    now = datetime.now()
                                    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                    f.write("Time: Generation: {}, Individual: {}".format(dt_string, generation, j))
                                    json.dump(new_testcases[j], f, indent=2)
                                    f.write('\n')
                            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST", 'NAME': testcase_name})
                            await websocket.send(init_msg)
                            break
                coverage_rate = 1- len(remaining_sub_violations) / maximun
                logging.info("total coverage rate: {}/{} = {}, covered predicates: {}\n".format((maximun - len(remaining_sub_violations)), maximun, coverage_rate, remaining_sub_violations))
                # MARK: batch processing
                with Pool(processes=10) as pool:
                    results = [pool.apply_async(processing_testcases, args=(et,)) for et in encoded_testcases_generation]
                    batch_results = [result.get() for result in results]
                for result_individual in batch_results: 
                    components_updated, graph_curr = result_individual[0], result_individual[1]
                    if components_updated: 
                        for new_component in components_updated: 
                            diversity_score = len(components_updated)
                            if new_component in seed_dive: 
                                if diversity_score >= mapping_dive[new_component]: 
                                    seed_dive[new_component] = encoded_testcase
                                    mapping_dive[new_component] = diversity_score
                            else: 
                                seed_dive[new_component] = encoded_testcase
                                mapping_dive[new_component] = diversity_score
                    if graph_curr: 
                        cavgraph.add_graph(graph_curr)
                # MARK: end batch processing
                logging.info("total detected components: {}\n".format(len(list(seed_dive.keys()))))
                cavgraph.show_relations()
                print()



def spec_scenario(spec, testcase, generations=0, pop_size=1, file_directory=None, ads_pipeline=[], map_params_dir='', vehicle_params_dir=''):
    loop = asyncio.get_event_loop()
    scenario_specification = copy.deepcopy(spec)
    scenario_testcase = copy.deepcopy(testcase)
    msgs = [scenario_testcase]
    loop.run_until_complete(
        asyncio.gather(hello(msgs, scenario_specification, generation_number=generations, population_size=pop_size, directory=file_directory, 
                             ads_pipeline=ads_pipeline, map_params_dir=map_params_dir, vehicle_params_dir=vehicle_params_dir)))



def test_scenario(direct, item, ads_pipeline, map_params_dir, vehicle_params_dir):
    file = direct + item

    log_direct ='The_Results/' + Path(item).stem
    if not os.path.exists(log_direct):
        os.makedirs(log_direct)
    else:
        shutil.rmtree(log_direct)

    if not os.path.exists(log_direct + '/data'):
        os.makedirs(log_direct + '/data')

    logging_file = log_direct + '/test.log'
    file_handler = logging.FileHandler(logging_file, mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.INFO, handlers=[stdout_handler, file_handler],
                        format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logging.info("Current Test Case: {}".format(item))
    isGroundTruth = True
    extracted_data = ExtractAll(file, isGroundTruth)
    origin_case = extracted_data.Get_TestCastINJsonList()
    all_specifications = extracted_data.Get_Specifications()
    maps = extracted_data.Get_AllMaps()

    for i in range(len(origin_case)):
        test_case = origin_case[i]
        scenario_name = test_case['ScenarioName']
        logging.info("Current scenario is {}.\n".format(scenario_name))
        try:
            specifications_in_scenario = all_specifications[scenario_name]
            current_map = maps[scenario_name]
            ego_init_start = test_case['ego']['start']
            map_info = get_map_info(current_map)
            if "lane_position" in ego_init_start.keys():
                lane_position = ego_init_start['lane_position']
                ego_position = map_info.get_position([lane_position['lane'], lane_position['offset']])
            else:
                ego_position = (ego_init_start['position']['x'], ego_init_start['position']['y'], ego_init_start['position']['z'])
            for spec_index in range(len(specifications_in_scenario)):
                first_specification = specifications_in_scenario[spec_index]
                single_specification = SingleAssertion(first_specification, current_map, ego_position)
                logging.info("\n Evaluate Scenario {} with Assertion {}: {} \n ".format(scenario_name, spec_index, single_specification.specification))
                spec_scenario(spec=single_specification, testcase=test_case, generations=20, pop_size=20, file_directory=log_direct,
                              ads_pipeline=ads_pipeline, map_params_dir=map_params_dir, vehicle_params_dir=vehicle_params_dir)
                # spec_scenario(spec=single_specification, testcase=test_case, generations=3, pop_size=4,
                #               file_directory=log_direct,
                #               ads_pipeline=ads_pipeline, map_params_dir=map_params_dir,
                #               vehicle_params_dir=vehicle_params_dir)  # DEBUG
                # print(testcase)
        except KeyError:
            spec_scenario(spec={}, testcase=test_case, ads_pipeline=ads_pipeline, map_params_dir=map_params_dir, vehicle_params_dir=vehicle_params_dir)


if __name__ == "__main__":
    ads_pipeline = ['tags', 'evaluators', 'predictors', 'prediction', 'decisions', 'planning']
    map_params_dir = './map_for_cavgraph/san_francisco.bin'
    vehicle_params_dir = './vehicles/Lincoln2017 MKZ-vehicle_param.pb.txt'
    direct = 'test_cases/'
    arr = ['script-1.txt']
    for item in arr:
        test_scenario(direct, item, ads_pipeline, map_params_dir, vehicle_params_dir)

