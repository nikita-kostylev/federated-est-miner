import asyncio
from quart import Quart, jsonify, request  # Quart is an async framework similar to Flask.
import socketio
import uvicorn
import sys
import signal
import os
from openfhe import *
import json
import time
import logging
import copy
import uuid
import multiprocessing
import requests
import aiohttp
import datetime
import tempfile
import random
from multidict import CIMultiDictProxy


from pm4py.visualization.petrinet.factory import apply, view, save


from pm4py.objects.petri.exporter import pnml as pnml_exporter



import pm4py

print(pm4py.__file__)

from pm4py.algo.discovery.est_miner.hooks.pre_processing_strategy import NoPreProcessingStrategy
from pm4py.algo.discovery.est_miner.hooks.order_calculation_strategy import LexicographicalOrderStrategy
from pm4py.algo.discovery.est_miner.hooks.pre_pruning_strategy import PrePruneUselessPlacesStrategy
from pm4py.algo.discovery.est_miner.hooks.search_strategy import SearchStrategy
from pm4py.algo.discovery.est_miner.hooks.post_processing_strategy import RemoveImplicitPlacesPostProcessingStrategy

from pm4py.algo.discovery.est_miner.utils.place_fitness import PlaceFitness,PlaceFitnessEvaluator
from pm4py.algo.discovery.est_miner.utils.place import Place
from pm4py.algo.discovery.est_miner.utils.activity_order import max_element
from pm4py.algo.discovery.est_miner.utils.constants import ParameterNames

from pm4py.algo.discovery.est_miner.builder import EstMinerDirector,EstMinerBuilder















#logging.basicConfig(level=logging.DEBUG)


NUMBER_OF_PARTIES = 2
NUMBER_OF_CASES   = 33 #8 #2948

cc = None
pk = None
sk = None

lockk = asyncio.Lock()

act_len = 0

debug_log = None


def shutdown_handler(signum, frame):
    print("Received shutdown signal")


    sys.exit(0)
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

async def deserialize(obj, keytype):
    try:
        # Create a temporary file; suffix .json is used to mimic original file naming
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=True) as tmp:
            # Write the provided contents into the temporary file
            tmp.write(obj["contents"])
            tmp.flush()  # Ensure data is written to disk
            
            try:
                # Depending on the key type, deserialize using the temporary file's name.
                if keytype == "public_key":
                    key, valid = DeserializePublicKey(tmp.name, JSON)
                elif keytype == "private_key":
                    key, valid = DeserializePrivateKey(tmp.name, JSON)
                elif keytype == "eval_key":
                    key, valid = DeserializeEvalKey(tmp.name, JSON)
                elif keytype == "cc":
                    key, valid = DeserializeCryptoContext(tmp.name, JSON)
                elif keytype == "cipher_text":
                    key, valid = DeserializeCiphertext(tmp.name, JSON)
                else:
                    raise ValueError("Invalid key type provided")
            except Exception as e:
                print(e)
                return None
            
            # If the key was deserialized successfully, return it.
            if valid and key is not None:
                return key
    except Exception as e:
        print(f"An error occurred: {e}")

async def serialize(obj):
    perf_ser = 0.1
    bool = True
    while perf_ser < 10:
        try:
            path = os.path.join("../testmest/",str(os.getpid())+".json")
            if not os.path.exists(path): open(path, 'w').close()            # Use module-level SerializeToFile to save the object
            bool = SerializeToFile(path, obj, JSON)
            with open(path, "r") as f:
                result = {"contents":f.read()}
            json.loads(result["contents"])
            perf_ser = 10
            return result
        except Exception as e:
            if bool:
                perf_ser *= 2
                await asyncio.sleep(perf_ser)
            print("Serialize Fail",perf_ser,e)

async def import_crypto():
    data = None
    global cc,pk,sk
    while not all([cc,pk,sk]):
        with open("../homomorph code/server_crypto.json", "r") as file:
            data = json.load(file)
        if not cc:
            cc = await deserialize(data["cc"],"cc")
        if not sk:
            sk = await deserialize(data["private_key"],"private_key")
        if not pk:
            pk = await deserialize(data["public_key"],"public_key")
        print("cc",str(cc),"sk",str(sk),"pk",str(pk))

''' ignore async websocket implementation
 
# Create an async Socket.IO server in ASGI mode.
sio = socketio.AsyncServer(max_http_buffer_size=100 * 1024 * 1024, async_mode="asgi", ping_intervall= 100, ping_timeout = 180, logger=True, engineio_logger=True)
app = Quart(__name__)
app = socketio.ASGIApp(sio,app)#,socketio_path="/socket.io")

client_sid_map = {}

@sio.event
async def connect(sid, environ, auth):
    id = auth.get("client_id","unknown")
    client_sid_map[id] = sid
    print(f"Client connected with sid: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected with sid: {sid}")

@sio.on("decrypt_reciever")
async def decrypt_reciever(sid,data):
    deser = await deserialize(data.get('share'),'cipher_text')
    decrypt_shares[data.get('client_id')] = deser

async def decrypt(enc,length):
    global decrypt_shares
    decrypt_shares = [None] * (NUMBER_OF_PARTIES+1)
    ser_enc = await serialize(enc)
    decrypt_shares[0] = cc.MultipartyDecryptLead([enc],sk)[0]
    for client in client_sid_map.keys():
        temp_val = await sio.call('decrypt111',{"cipher_text":ser_enc},to=client_sid_map[client])
    plaintextMultipartyMult = cc.MultipartyDecryptFusion(decrypt_shares)
    plaintextMultipartyMult.SetLength(length)
    return plaintextMultipartyMult.GetPackedValue()

'''

#http decrypt copy
async def decrypt(enc,length):
    global decrypt_shares
    decrypt_shares = [None] * (NUMBER_OF_PARTIES+1)
    ser_enc = await serialize(enc)
    decrypt_shares[0] = cc.MultipartyDecryptLead([enc],sk)[0]
    for client in range(NUMBER_OF_PARTIES):
        response = requests.post(f'http://localhost:{5001+client}/decrypt', json={"cipher_text":ser_enc}).json()
        decrypt_shares[client+1] = await deserialize(response["share"],"cipher_text")
    plaintextMultipartyMult = cc.MultipartyDecryptFusion(decrypt_shares)
    plaintextMultipartyMult.SetLength(length)
    return plaintextMultipartyMult.GetPackedValue()




class FederatedEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'FederatedEstMiner'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = LexicographicalOrderStrategy()

    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategyDistributed(restricted_edge_type='red',maxdepth=2)
    
    def build_post_processing_strategy(self):
        #self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategyModified()
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()   #USE OTHER VERSION TEMPORARY
        #self.est_miner.post_processing_strategy = NoPostProcessingStrategy()



class TreeDfsStrategyDistributed(SearchStrategy):
    class RootExtractor:

        @classmethod
        def get_roots(cls, activities, pre_pruning_strategy, heuristic_parameters=None):
            roots = set()
            for a1 in activities:
                for a2 in activities:
                    p = Place(a1, a2, 1, 1)
                    if not pre_pruning_strategy.execute(p, parameters=heuristic_parameters):
                        roots.add(p)
            return roots
    
    def __init__(self, restricted_edge_type, maxdepth):
        assert(restricted_edge_type == 'red' or restricted_edge_type == 'blue')
        self._restricted_edge_type = restricted_edge_type
        self._max_depth = maxdepth
    
    async def execute(
        self, 
        log, 
        tau, 
        pre_pruning_strategy, 
        in_order, 
        out_order, 
        activities, 
        heuristic_parameters=None, 
        logger=None, 
        stat_logger=None
    ):
        if (logger is not None):
            logger.info('Starting Search')
        roots = self.RootExtractor.get_roots(activities, pre_pruning_strategy, heuristic_parameters=heuristic_parameters)
        return await self.traverse_roots(
            roots,
            log,
            tau,
            in_order,
            out_order,
            pre_pruning_strategy,
            activities,
            heuristic_parameters=heuristic_parameters,
            logger=logger,
            stat_logger=stat_logger
        )
    
    async def process_in_batches(self,roots, batch_size,log,tau,inorder,outorder,preprune,activities,heuristicparams):
        results = []
        rootsss = list(roots)
        for i in range(0, len(rootsss), batch_size):
            batch = rootsss[i:i + batch_size]
            tasks = [
                asyncio.to_thread(self._traverse_place(log, tau, 0, root, inorder, outorder,preprune, activities, heuristicparams))
                for root in batch
            ]
            # Wait for the current batch to complete before moving on
            print("batch",i,"started")
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        return results
    

    def traverse_place_sync(self,log, tau, root, inorder, outorder, preprune, activities, heuristicparams):
        # Run the async function using an event loop in a blocking manner

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try: 
            result = loop.run_until_complete(self._traverse_place(log, tau, 0, root, inorder, outorder, preprune, activities, heuristicparams))
        finally:
            loop.close()

        if isinstance(result, CIMultiDictProxy):
            result = dict(result)

        return result

    async def processs_in_batches(self,roots, batch_size,log,tau,inorder,outorder,preprune,activities,heuristicparams):

        pool = multiprocessing.Pool(processes=batch_size)  # 2 separate processes for 2 instances

        # Run tasks concurrently in separate processes
        tasks = [
            pool.apply_async(self.traverse_place_sync,(log, tau, list(roots)[root], inorder, outorder,preprune, activities, heuristicparams))  # Process 1
            for root in range(len(list(roots))) 
        ]

        # Wait for the results of both processes
        results = [task.get() for task in tasks]

        print("Finished all tasks.")
        for result in results:
            print(result)

        pool.close()
        pool.join()  
        return results

    async def traverse_roots(
        self,
        roots,
        log,
        tau,
        in_order,
        out_order,
        pre_pruning_strategy,
        activities,
        heuristic_parameters=None,
        logger=None,
        stat_logger=None
    ):
        fitting_places = list()
        args = list()
        print('Number of roots:',len(roots))

        fitting_places = await self.processs_in_batches(roots,8,log,tau,in_order,out_order,pre_pruning_strategy,activities,heuristic_parameters)
        #for root in roots:
            #fitting_places.extend(await self._traverse_place(log, tau, 0, root, in_order, out_order, pre_pruning_strategy, activities, heuristic_parameters=heuristic_parameters))#, logger=logger, stat_logger=stat_logger))
            ##args.append( (log, tau, 0 ,root, in_order, out_order, pre_pruning_strategy, activities, heuristic_parameters) )

            

        #temporary removed due to not being sure, how multiprocessing and client server play together.    
        ##with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        ##    fitting_places = pool.starmap(await self._traverse_place, args)


        
        flat_result = [p for fitting in fitting_places for p in fitting]
        return flat_result
        #return fitting_places
    
    async def _traverse_place(
        self,
        log,
        tau,
        depth,
        place,
        in_order,
        out_order,
        pre_pruning_strategy,
        activities,
        heuristic_parameters=None,
        logger=None,
        stat_logger=None
    ):
        if logger is not None:
            logger.info('Checking node ' + place.name)
        
        if pre_pruning_strategy.execute(place, parameters=heuristic_parameters):
            if logger is not None:
                logger.info('    Pre-pruning the node.')
            return list()
        
        fitting_places = list()
        place_fitness_states = await place_fitness(log,place,tau)

        child_places = list()
        if PlaceFitness.FITTING in place_fitness_states:
            if logger is not None:
                logger.info('    Place is fitting.')
            fitting = True 
            ''''for important_trace in heuristic_parameters[ParameterNames.IMPORTANT_TRACES]:
                involved, fitness_states = PlaceFitnessEvaluator.trace_fitness(important_trace, place)
                if involved and not PlaceFitness.FITTING in fitness_states:
                    fitting = False                This is for delta variant'''
            if fitting:
                fitting_places.append(place)
        
        if (
            PlaceFitness.OVERFED not in place_fitness_states 
            or (self._restricted_edge_type == 'red' 
            and self._cant_prune_red_subtrees(place, out_order, activities))
        ): # nodes attached by red edge
            child_places.extend(self._get_red_child_places(place, in_order, activities))
        elif stat_logger is not None:
            stat_logger.pruned_red_subtree(place)
        if (
            PlaceFitness.UNDERFED not in place_fitness_states
            or (self._restricted_edge_type == 'blue'
            and self._cant_prune_blue_subtrees(place, in_order, activities))
        ): # nodes attached by blue edge
            child_places.extend(self._get_blue_child_places(place, out_order, activities))
        elif stat_logger is not None:
            stat_logger.pruned_blue_subtree(place)
        
        if logger is not None:
            if PlaceFitness.OVERFED in place_fitness_states:
                logger.info('    Place is overfed.')
            if PlaceFitness.UNDERFED in place_fitness_states:
                logger.info('    Place is underfed.')
            logger.info('    ' + str(len(child_places)) + ' child places.')
            for p in child_places:
                logger.info('    Child Place: ' + p.name)
        if(depth<self._max_depth):
            for p in child_places:
                fitting_places.extend(await self._traverse_place( 
                    log,
                    tau,
                    depth+1,
                    p,
                    in_order,
                    out_order,
                    pre_pruning_strategy,
                    activities,
                    heuristic_parameters=heuristic_parameters,
                    logger=logger,
                    stat_logger=stat_logger
                ))
        if depth==0: print(place.name)
        return fitting_places
        
    def _cant_prune_red_subtrees(self, place, out_order, activities):
        max_output_activity = max_element(activities, place.output_trans, out_order)
        return len(out_order.is_larger_relations[max_output_activity]) > 0
    
    def _cant_prune_blue_subtrees(self, place, in_order, activities):
        max_input_activity = max_element(place.input_trans, in_order, activities)
        return len(in_order.is_larger_relations[max_input_activity]) > 0
    
    def _get_red_child_places(self, place, in_order, activities):
        if (self._restricted_edge_type == 'red'):
            if (place.num_output_trans > 1):
                return list()
        
        child_places = list()
        max_input_activity = max_element(activities, place.input_trans, in_order)
        higher_ordered_activities = in_order.is_larger_relations[max_input_activity]
        for a in higher_ordered_activities:
            new_input_trans = copy.copy(place.input_trans)
            new_input_trans = new_input_trans | a
            num_input_trans = copy.copy(place.num_input_trans) + 1
            child_places.append(Place(new_input_trans, copy.copy(place.output_trans), num_input_trans, copy.copy(place.num_output_trans)))
        return child_places
    
    def _get_blue_child_places(self, place, out_order, activities):
        if (self._restricted_edge_type == 'blue'):
            if (place.num_input_trans > 1):
                return list()
        
        child_places = list()
        max_output_activity = max_element(activities, place.output_trans, out_order)
        higher_ordered_activities = out_order.is_larger_relations[max_output_activity]
        for a in higher_ordered_activities:
            new_output_trans = copy.copy(place.output_trans)
            new_output_trans = new_output_trans | a
            num_output_trans = copy.copy(place.num_output_trans) + 1
            child_places.append(Place(copy.copy(place.input_trans), new_output_trans, copy.copy(place.num_input_trans), num_output_trans))
        return child_places




async def run_miner(tau):
    anonym_log = 0

    #while not len(client_sid_map)==NUMBER_OF_PARTIES:
    #    await asyncio.sleep(1)
    global debug_log

    with open("./anonym_log_server_red.json","r") as file:
        anonym_log = json.load(file)

    #debug_log = pm4py.objects.log.importer.xes.factory.apply('./.xes')

    #debug_log =  [debug_log[0] , debug_log[1] , debug_log[2] , debug_log[50],  debug_log[65],  debug_log[149],  debug_log[205],  debug_log[491]]


    act = ['Accepted', 'Queued', 'Completed', 'Unmatched']#["[start>","B","G","W","X","L","Y","K","[end]"]#["[start>","A","B","C","D","E","F","G","K","L","M","N","W","X","Y","[end]"]
    act_dict = {}

    for i in range(len(act)):
        act_dict[act[i]] = 2**(len(act)-i-1)


    #debug_log = [[act_dict[event['concept:name']] for event in trace]for trace in debug_log]







    #anonym_log = [anonym_log[0], anonym_log[1], anonym_log[2], anonym_log[50], anonym_log[65], anonym_log[149], anonym_log[205], anonym_log[491]]

    est_director = EstMinerDirector()
    est_builder = FederatedEstMinerBuilder()
    est_director.construct(est_builder)
    est_miner = est_builder.est_miner

    parameters = {}
    parameters["tau"] = tau

    await asyncio.sleep(2)

    act = ['[start>','Accepted', 'Queued', 'Completed', '[end]']#["[start>","B","G","W","X","L","Y","K","[end]"]#["[start>","A","B","C","D","E","F","G","K","L","M","N","W","X","Y","[end]"]

    global act_len 

    act_len = len(act)-1

    net,im,fm,logger = await est_miner.asyncapply(anonym_log,act,parameters)
    


    try: 
        pnml_exporter.export_net(net,im,os.path.join("../homomorph code/homo_test_"+str(parameters["tau"])+"_bpi13.pnml"),fm)
    except Exception as e:
        print("file",e) 






async def place_fitness(log,place,tau):
    print("start place",place.name)
    input = int(place.name.split("|")[0][1:])
    output = int(place.name.split("|")[1][:-1])
    trace_indicies = [0,1,2,3]
    event_indicies = [log[0][1],log[1][1],log[2][1],log[3][1]]
    event_indicies_indicies = [1,1,1,1]
    if input & 2**act_len == 2**act_len:
        current_state = [1,1,1,1]
    else:
        current_state = [0,0,0,0]
    current_state = cc.MakePackedPlaintext(current_state)
    current_state = cc.Encrypt(pk,current_state)
    current_state = await serialize(current_state)
    finished_traces = [False] * NUMBER_OF_CASES
    next_party = 1
    metric = [0,0,0] # overfed, perfectly fitting, underfed
    

    infinte_loop = 0
    while not all(finished_traces):
        #result = await sio.call("tracestep",data={"trace_indicies":trace_indicies,"event_indicies":event_indicies,"current_state":current_state,"placein":input,"placeout":output},to=client_sid_map[next_party],timeout=69)
        #result = requests.post(f'http://localhost:{5001+next_party}/trace_step', json={"trace_indicies":trace_indicies,"event_indicies":event_indicies,"current_state":current_state,"placein":input,"placeout":output}).json()
        #print("tr",trace_indicies,"at",place.name,finished_traces)
        async with aiohttp.ClientSession() as session:
            if place.name =="(256 | 1281)":
                print("before send",trace_indicies,event_indicies,finished_traces)
            async with session.post(f'http://localhost:{5001+next_party}/trace_step', json={"trace_indicies":trace_indicies,"event_indicies":event_indicies,"current_state":current_state,"placein":input,"placeout":output}) as response:
                tempres = response
                result = await tempres.json()
        current_state = await deserialize(result["result"],"cipher_text")
        new_trace_setting = [False] * 4
        doubles = [False] * 4
        end_activity = [0] * 4
        if result["consumption"] or any(result["doubles"]):
            decrypted = await decrypt(current_state,4)
            for i in range(len(decrypted)):
                if decrypted[i] == -1:
                    new_trace_setting[i] = True
                elif decrypted[i] == 0 and result["doubles"][i]:
                    new_trace_setting[i] = True
                    doubles[i] = True
            if place.name =="(256 | 1281)":
                print("underfed at",new_trace_setting)

        for i in range(4):
            if place.name =="(256 | 1281)":
                print("eii",event_indicies_indicies)
            if finished_traces[trace_indicies[i]]:
                continue
            elif len(log[trace_indicies[i]])-1==event_indicies_indicies[i]:
                if place.name =="(256 | 1281)": 
                    print("end activity")
                    print(event_indicies_indicies[i],len(log[trace_indicies[i]]))
                if output & 1 == 1:
                    end_activity[i] = 1
                new_trace_setting[i] = True
            elif result["contributions"][i]:
                event_indicies[i] = log[trace_indicies[i]][event_indicies_indicies[i]+1]
                event_indicies_indicies[i] +=1
        new_state = [None] * 4
        if any(new_trace_setting):
            decrypted = await decrypt(current_state,4)
            for i in range(4):
                if new_trace_setting[i] and not finished_traces[trace_indicies[i]]:
                    if place.name == "(256 | 1281)":
                        print("trace",trace_indicies[i],"finished")
                    finished_traces[trace_indicies[i]] = True
                    if decrypted[i]-end_activity[i] == 0:
                        if doubles[i]:
                            metric[2] += 1
                            if False and trace_fitness_debug(place,trace_indicies[i],tau) != 2:
                                print("trace",trace_indicies[i],"classified as underfed, while its not for",place.name)
                        else:
                            metric[1] += 1
                            if False and trace_fitness_debug(place,trace_indicies[i],tau) != 1:
                                print("trace",trace_indicies[i],"classified as fitting, while its not for",place.name)
                    elif decrypted[i]-end_activity[i] > 0:
                        metric[0] += 1
                        if False and trace_fitness_debug(place,trace_indicies[i],tau) != 0:
                            print("trace",trace_indicies[i],"classified as overfed, while its not for",place.name)
                    elif decrypted[i]-end_activity[i] < 0:
                        metric[2] += 1
                        if False and trace_fitness_debug(place,trace_indicies[i],tau) != 2:
                            print("trace",trace_indicies[i],"classified as underfed, while its not for",place.name)
                    if len(finished_traces)-sum(finished_traces)<4:
                        new_trace_setting[i] = False
                        new_state[i] = decrypted[i]
                        continue
                    start = 0
                    for _ in range(4):
                        start = finished_traces.index(False,start+1)
                    trace_indicies[i] = start
                    event_indicies_indicies[i] = 1
                    event_indicies[i] = log[trace_indicies[i]][event_indicies_indicies[i]]
                    new_trace_setting[i] = False
                    if input & 2**act_len == 2**act_len:# 32768 == 32768:
                        new_state[i] = 1
                    else:
                        new_state[i] = 0
                else:
                    new_state[i] = decrypted[i]
            mppnewstate = cc.MakePackedPlaintext(new_state)
            current_state = cc.Encrypt(pk,mppnewstate)
            infinte_loop = 0
        else:
            infinte_loop += 1 
        current_state = await serialize(current_state)
        if next_party==NUMBER_OF_PARTIES-1:
            next_party = 0
        else:
            next_party += 1
        if infinte_loop ==35:
            start = finished_traces.index(False)
            trace_indicies[0] = start
            event_indicies_indicies[0] = 1
            event_indicies[0] = log[trace_indicies[0]][event_indicies_indicies[0]]
            new_trace_setting[0] = False
            if input & 2**act_len == 2**act_len: 
                new_state[0] = 1
            else:
                new_state[0] = 0
            infinte_loop = 0
            for i in range(1,4):
                new_state[i] = 0
            mppnewstate = cc.MakePackedPlaintext(new_state)
            current_state = cc.Encrypt(pk,mppnewstate)
            current_state = await serialize(current_state)
            print("loop runs infinitely",input,output)
            #print(finished_traces,new_trace_setting,event_indicies,event_indicies_indicies,trace_indicies)
        

    #if sum(metric) != NUMBER_OF_CASES:
    #    print("Metric amount incorrect. Metrics:",metric,sum(metric))



    if place.name == "(256 | 128)":
        print("metric",metric)
        for i in range(8):
            print("trace",i,trace_fitness_debug(place,i,tau))

    states = set()

    if metric[0]/NUMBER_OF_CASES > 1-tau: states.add(PlaceFitness.OVERFED)
    if metric[2]/NUMBER_OF_CASES > 1-tau: states.add(PlaceFitness.UNDERFED)
    if metric[1]/NUMBER_OF_CASES >=   tau: states.add(PlaceFitness.FITTING)
    else:                                 states.add(PlaceFitness.UNFITTING) 


    """if place.name in correct_places and PlaceFitness.FITTING in states:
        correct_places.remove(place.name)
    elif place.name not in correct_places and PlaceFitness.FITTING not in states:
        states = states
    else:
        print("Incorrect identified",place.name)"""
    return states
                


        

''' removed due to http implementation
async def start_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=5000, log_level="debug")
    server = uvicorn.Server(config)
    await server.serve()  # This is an async coroutine
'''

def trace_fitness_debug(place,trace_index,tau):
    placein = int(place.name.split("|")[0][1:])
    placeout = int(place.name.split("|")[1][:-1])

    sim = 0
    underfed = False
    traace = [256]+debug_log[trace_index]+[1]
    for event in traace:
        if event & placein == event and event & placeout == event:
            if sim == 0:
                underfed = True
        elif event & placein == event:
            sim += 1
        elif event & placeout == event:
            if sim == 0:
                underfed = True
            else:
                sim -= 1
    if sim<0 or underfed:
        return 2
    elif sim==0:
        return 1
    elif sim>0:
        return 0

async def main():
    print("started 1.0 at:",datetime.datetime.now())
    await import_crypto()
    await run_miner(1.0)
    current_time = datetime.datetime.now()
    print("Finished 1.0 at:",current_time)





# Main entry point: run the server with Uvicorn
if __name__ == "__main__":
    asyncio.run(main())








