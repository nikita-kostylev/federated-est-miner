import pm4py
import json
from openfhe import * 
import signal
import sys
import argparse
import socketio
import asyncio
import os
import aiohttp
import pm4py.objects
from quart import Quart, request, jsonify


#logging.basicConfig(level=logging.DEBUG)



def shutdown_handler(signum, frame):
    print("Received shutdown signal")
    sys.exit(0)
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# Setup command-line argument parsing for client configuration
parser = argparse.ArgumentParser(description="Async Socket.IO Client")
parser.add_argument("--client_id", type=int, default=1, help="Unique client identifier")
args = parser.parse_args()

global_id = args.client_id

NUMBER_OF_PARTIES = 2
NUMBER_OF_CASES   = 33 # 8 #2948

cc = None
pk = None
sk = None

sio = None

anonym_log = None

orig_log = None

rev_dict = {}

ppei = {}

#Add http server


app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 



def deserialize(obj,keytype):
    try: 
        path = os.path.join("../testmest/",str(global_id)+".json")
        with open(path, 'w') as file:
            file.write(obj["contents"])
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
        if bool:
            return key
    except Exception as e:
        print(f"An error occurred: {e}")

async def serialize(obj):
    perf_ser = 0.1- 0.01 * (global_id**2)
    bool = True
    while perf_ser < 10:
        try:
            path = os.path.join("../testmest/",str(global_id)+".json")
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

def import_crypto():
    data = None
    global cc,pk,sk
    while not all([cc,pk,sk]):
        with open("../homomorph code/client_crypto"+str(global_id)+".json", "r") as file:
            data = json.load(file)
        if not cc:
            cc = deserialize(data["cc"],"cc")
        if not sk:
            sk = deserialize(data["private_key"],"private_key")
        if not pk:
            pk = deserialize(data["public_key"],"public_key")
        print("cc",str(cc),"sk",str(sk),"pk",str(pk))


async def connect():
    print("Connected to async server. -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!")

async def disconnect():
    print("Disconnected from server.")


async def decrypt111(data):
    deser = deserialize(data.get('cipher_text'),"cipher_text")
    val = cc.MultipartyDecryptMain([deser],sk)[0]
    ser_val = await serialize(val)
    await sio.emit('decrypt_reciever',{"client_id":global_id,"share":ser_val})
    return "test"

async def tracestep(data):
    global ppei
    trace_indicies = data.get("trace_indicies")
    event_indicies = data.get("event_indicies")
    current_state  = data.get("current_state")
    placein        = data.get("placein")
    placeout       = data.get("placeout")

    if (placein,placeout) not in ppei:
        ppei[(placein,placeout)] = [0] * NUMBER_OF_CASES


    deser_curr_state = deserialize(current_state,"cipher_text")
    step = [0] * 4
    consumption = False

    for i in range(len(trace_indicies)):
        if anonym_log[trace_indicies[i]][ppei[(placein,placeout)][trace_indicies[i]]] == event_indicies[i]:
            if (orig_log[trace_indicies[i]][ppei[(placein,placeout)][trace_indicies[i]]] & placein)==orig_log[trace_indicies[i]][ppei[(placein,placeout)][trace_indicies[i]]]:#input
                step[i] = +1
            elif (orig_log[trace_indicies[i]][ppei[(placein,placeout)][trace_indicies[i]]] & placeout)==orig_log[trace_indicies[i][ppei[(placein,placeout)][trace_indicies[i]]]]:#output
                step[i] = -1
                consumption = True
            ppei[(placein,placeout)][trace_indicies[i]] += 1

    pp = cc.MakePackedPlaintext(step)
    epp = cc.Encrypt(pk,pp)
    result = cc.EvalAdd(deser_curr_state,epp)
    ser_result = await serialize(result)

    return {"result":ser_result,"consumption":consumption}


# http versions
@app.route("/decrypt", methods = ['POST'])
async def decrypt():
    data = await request.get_json()
    deser = deserialize(data.get('cipher_text'),"cipher_text")
    val = cc.MultipartyDecryptMain([deser],sk)[0]
    ser_val = await serialize(val)
    return {"share":ser_val}

@app.route("/trace_step", methods = ['POST'])
async def trace_step():
    data = await request.get_json()
    global ppei
    trace_indicies = data.get("trace_indicies")
    event_indicies = data.get("event_indicies")
    current_state  = data.get("current_state")
    placein        = data.get("placein")
    placeout       = data.get("placeout")

    if (placein,placeout) not in ppei:
        ppei[(placein,placeout)] = [0] * NUMBER_OF_CASES
        if placein==256 and placeout==128:
            print("Client",global_id,"initiated")


    deser_curr_state = deserialize(current_state,"cipher_text")
    step = [0] * 4
    consumption = False
    contributions = [False] * 4
    doubles = [False] * 4

    for i in range(len(trace_indicies)):
        if len(anonym_log[trace_indicies[i]])==ppei[(placein,placeout)][trace_indicies[i]]:
            continue
        if placein==256 and placeout==128 and trace_indicies[i]==5:
            print("traceindex",trace_indicies[i])
            print("ppei",ppei[(placein,placeout)][trace_indicies[i]])
            print("eventindicex_server",event_indicies[i])
            print("eventindicex_client",anonym_log[trace_indicies[i]][ppei[(placein,placeout)][trace_indicies[i]]])
        if anonym_log[trace_indicies[i]][ppei[(placein,placeout)][trace_indicies[i]]] == event_indicies[i]:
            temp1 = orig_log[trace_indicies[i]]
            half_ppei = ppei[(placein,placeout)][trace_indicies[i]]
            print(half_ppei,trace_indicies[i],global_id,temp1)
            temp = temp1[half_ppei]
            if placein==256 and placeout==128:
                print("temp",rev_dict[temp],"in (X|W)")
            if temp & placein==temp and temp & placeout==temp: 
                doubles[i] = True
                if placein==256 and placeout==128 and trace_indicies[i]==5:
                    print("X|W doub",consumption,contributions,doubles)
            elif (temp & placein)==temp:#input
                step[i] = +1
                if placein==256 and placeout==128 and trace_indicies[i]==5:
                    print("X|W in",consumption,contributions,doubles)
            elif (temp & placeout)==temp:#output
                step[i] = -1
                consumption = True
                if placein==256 and placeout==128 and trace_indicies[i]==5:
                    print("X|W out",consumption,contributions,doubles)
            elif placein==256 and placeout==128 and trace_indicies[i]==5:
                print("Nothing worked")
            ppei[(placein,placeout)][trace_indicies[i]] += 1
            contributions[i] = True

    if placein==256 and placeout==128:
        print("Client",global_id,"submits",step,"to (start|L,Y)",consumption,contributions,doubles)

    pp = cc.MakePackedPlaintext(step)
    epp = cc.Encrypt(pk,pp)
    result = cc.EvalAdd(deser_curr_state,epp)
    ser_result = await serialize(result)

    return {"result":ser_result,"consumption":consumption,"contributions":contributions,"doubles":doubles}
















async def main():

    global sio,anonym_log,orig_log,rev_dict


    with open("./anyonym_log_client_red"+str(global_id)+".json","r") as file:
        anonym_log = json.load(file)

    orig_log = pm4py.objects.log.importer.xes.factory.apply('./reduced_log_sub'+str(global_id)+'.xes')

    #orig_log   = [orig_log[0] , orig_log[1],  orig_log[2], orig_log[50] , orig_log[65] , orig_log[149] , orig_log[205]  , orig_log[491]]

    
    act = ['[start>','Accepted', 'Queued', 'Completed','[end]']#["[start>","B","G","W","X","L","Y","K","[end]"]#["[start>","A","B","C","D","E","F","G","K","L","M","N","W","X","Y","[end]"]
    act_dict = {}


    for i in range(len(act)):
        act_dict[act[i]] = 2**(len(act)-i-1)
        rev_dict[2**(len(act)-i-1)] = act[i]

    print(act_dict)
    print(rev_dict)

    print(pm4py.objects.log.util.log.project_traces(orig_log))

    orig_log = [[act_dict[event['concept:name']] for event in trace]for trace in orig_log]
    print(orig_log)

    #anonym_log = [anonym_log[0] , anonym_log[1],anonym_log[2], anonym_log[50] , anonym_log[65] , anonym_log[149] , anonym_log[205] , anonym_log[491]]

    import_crypto()

    
    ''' Replace asyncio

    class MyClientSession(aiohttp.ClientSession):
        async def ws_connect(self, *args, **kwargs):
            # Set the maximum message size to 100 MB (for example)
            kwargs.setdefault('max_msg_size', 100 * 1024 * 1024)
            return await super().ws_connect(*args, **kwargs)


    session = MyClientSession()
    sio = socketio.AsyncClient(http_session = session,logger=True, engineio_logger=True)
    sio.on("decrypt111",decrypt111)
    sio.on("tracestep",tracestep)
    sio.on("connect",connect)
    sio.on("disconnect",disconnect)

    await asyncio.sleep(1)
    await sio.connect("http://localhost:5000",auth={"client_id":global_id}, transports=["websocket"])
    await asyncio.sleep(1)
    await sio.disconnect()

    '''

    

if __name__ == "__main__":
    asyncio.run(main())
    app.run(host='0.0.0.0', port=(5000+global_id))#,debug=True)
    