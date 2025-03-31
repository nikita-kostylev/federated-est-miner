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
import uuid
#logging.basicConfig(level=logging.DEBUG)


NUMBER_OF_PARTIES = 2
NUMBER_OF_CASES   = 2948

cc = None
pk = None
sk = None

lockk = asyncio.Lock()
comp_lock = asyncio.Lock()

def shutdown_handler(signum, frame):
    print("Received shutdown signal")
    with open("anonym_log_server_red.json", "w", encoding="utf-8") as file:
        json.dump(id_list, file, indent=4)


    sys.exit(0)
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

async def deserialize(obj,keytype):
    try: 
        index = 3
        while True:
            path = os.path.join("../testmest/",str(index)+".json")
            global lockk
            async with lockk:
                with open(path, 'w') as file:
                    file.write(obj["contents"])
                    file.flush()
                try:
                    if keytype=="public_key":
                        key, bool = DeserializePublicKey(path,JSON)
                    if keytype=="private_key":
                        key, bool = DeserializePrivateKey(path,JSON)
                    if keytype=="eval_key":
                        key, bool = DeserializeEvalKey(path,JSON)
                    if keytype=="cc":
                        key, bool = DeserializeCryptoContext(path,JSON)
                    if keytype=="cipher_text":
                        key, bool = DeserializeCiphertext(path,JSON)
                except Exception as e:
                    print(e)
            if bool and key!=None:
                return key
    except Exception as e:
        print(f"An error occurred: {e}")

async def serialize(obj):
    perf_ser = 0.1
    bool = True
    while perf_ser < 10:
        try:
            path = os.path.join("../testmest/","0.json")
            # Use module-level SerializeToFile to save the object
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
            print("Serialize Fail",perf_ser)

async def import_crypto():
    data = None
    global cc,pk,sk
    while not all([cc,pk,sk]):
        with open("./server_crypto.json", "r") as file:
            data = json.load(file)
        if not cc:
            cc = await deserialize(data["cc"],"cc")
        if not sk:
            sk = await deserialize(data["private_key"],"private_key")
        if not pk:
            pk = await deserialize(data["public_key"],"public_key")
        print("cc",str(cc),"sk",str(sk),"pk",str(pk))
    



# Create an async Socket.IO server in ASGI mode.
sio = socketio.AsyncServer(max_http_buffer_size=100 * 1024 * 1024, async_mode="asgi")#, logger=True, engineio_logger=True)
app = Quart(__name__)
app = socketio.ASGIApp(sio,app)#,socketio_path="/socket.io")



#map of session ids in sockets with clientid as keys
client_sid_map = {}
#collection of current submitted timestamps
log_identification = {}
#the shares of all clients of the current decrypt process
decrypt_shares = [None] * (NUMBER_OF_PARTIES+1)
#how many clients have already submitted all of their events for the current trace
non_participants = 0
#the end product containing all ids that are done to identify objects
id_list = [[] for _ in range(NUMBER_OF_CASES)]

trace_finished = [False] * (NUMBER_OF_PARTIES)

comp_finished = [False] * (NUMBER_OF_PARTIES)



@sio.event
async def connect(sid, environ, auth):
    id = auth.get("client_id","unknown")
    client_sid_map[id] = sid
    print(f"Client connected with sid: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected with sid: {sid}")


async def comp_results(level,trace_index,indicies):
    left = 0
    right = 0
    if len(indicies) > 3:
        mid = (len(indicies) + 1) // 2
        left  = await comp_results(level+1,trace_index,indicies[:mid])
        right = await comp_results(level+1,trace_index,indicies[mid:])  
    elif len(indicies) == 1:
        return indicies[0]
    elif len(indicies) == 2:
        left  = indicies[0]
        right = indicies[1]
    else:
        return -1
    left_val   = await deserialize(log_identification[trace_index][1][left]['time'],"cipher_text")
    right_val  = await deserialize(log_identification[trace_index][1][right]['time'],"cipher_text")

    #left_rand  = await deserialize(log_identification[trace_index][1][left]['rand_fac'],"cipher_text")
    #right_rand = await deserialize(log_identification[trace_index][1][right]['rand_fac'],"cipher_text")


    neg_right_val = cc.EvalNegate(right_val)
    values_sum = cc.EvalAdd(left_val,neg_right_val)

    #random_factor = cc.EvalMult(left_rand,right_rand)
    #result = cc.EvalMult(values_sum,random_factor)

    dec_result = await decrypt(values_sum,1)
    result = dec_result.GetPackedValue()
    print("comp result",result[0])
    
    if result[0] < 0:
        return left
    else:
        return right


#@sio.on('submit_row_value')
@sio.event
async def submit_row_value(sid,data):
    finished = data.get('finished')
    client_id = data.get('client_id')
    trace_index = data.get('trace_index')
    global non_participants, trace_finished, comp_finished


    if trace_index not in log_identification:
        log_identification[trace_index] = [[],{}]

    if not any(comp_finished) and "comp_executed" in log_identification[trace_index][1]:
        log_identification[trace_index][1].pop("comp_executed")

    if not finished:
        time = data.get('timestamp')
        #rand_fac = data.get('random_factor')
        log_identification[trace_index][1][client_id] =  {"time":time}
    else:
        non_participants += 1
        if client_id in log_identification[trace_index][1].keys():
            log_identification[trace_index][1].pop(client_id)
    
    if len(log_identification[trace_index][1]) >= NUMBER_OF_PARTIES-non_participants:
            # Use the global comp_lock to ensure only one party enters here.
        async with comp_lock:
            # Check if this trace has already had its computation executed.
            if not log_identification[trace_index][1].get("comp_executed", False):
                log_identification[trace_index][1]["comp_executed"] = True  # Mark that comp_results is running for this trace.
                comp_finished = [True] * NUMBER_OF_PARTIES 
                if non_participants == NUMBER_OF_PARTIES:
                    trace_finished = [True] * NUMBER_OF_PARTIES
                    print("trace finished",trace_index)
                else:
                    non_participants = -NUMBER_OF_PARTIES
                    index = await comp_results(0, trace_index, [x for x in log_identification[trace_index][1].keys() if x != "comp_executed"])
                    winner = await sio.call('comp_result', {"trace_index": trace_index}, to=client_sid_map[index])
                    print("Winner index:", index)
                    id_list[trace_index].append(winner)
                # (Optionally, you can remove the flag here if you want to allow future computations.)
            non_participants = 0
            #print("tf",trace_finished)
            if comp_finished[client_id-1]:
                comp_finished[client_id-1] = False
            if trace_finished[client_id-1]:
                trace_finished[client_id-1] = False
                return "all finished"
            else:
                return "test"
    



        '''print("comp started.",[log_identification[trace_index][1][client]["debug"] for client in log_identification[trace_index][1]])
        #print("how much non participant",non_participants)
        global trace_finished
        if non_participants == NUMBER_OF_PARTIES:
            trace_finished = [True] * NUMBER_OF_PARTIES
        else:
            non_participants = -NUMBER_OF_PARTIES
            index = await comp_results(0,trace_index,list(log_identification[trace_index][1].keys()))
            winner = await sio.call('comp_result',{"trace_index":trace_index},to=client_sid_map[index])
            print("Winner index:",winner)
            id_list[trace_index].append(winner)
        non_participants = 0
        if trace_finished[client_id-1]:
            trace_finished[client_id-1] = False
            return "all finished"
        else: 
            return "test" '''
    else:
        while non_participants < 0:
            await asyncio.sleep(0.5)
        return -1

@sio.on("id_reciever")
async def id_reciever(sid,data):
    id = data.get("id")
    trace_index = data.get("trace_index")
    id_list[trace_index].append(id)



@sio.on('*')
def any_event(event, sid, data):
     print("falscher ort")


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
    return plaintextMultipartyMult






# Main entry point: run the server with Uvicorn
if __name__ == "__main__":
    asyncio.run(import_crypto())
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")