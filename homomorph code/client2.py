import asyncio
import argparse
import socketio
import time
from random import randint
import pm4py
import os
from openfhe import * 
import json
import signal
import sys
import logging
import aiohttp
import uuid

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

cc = None
pk = None
sk = None

sio = None


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
        with open("../client_crypto"+str(global_id)+".json", "r") as file:
            data = json.load(file)
        if not cc:
            cc = deserialize(data["cc"],"cc")
        if not sk:
            sk = deserialize(data["private_key"],"private_key")
        if not pk:
            pk = deserialize(data["public_key"],"public_key")
        print("cc",str(cc),"sk",str(sk),"pk",str(pk))
    

#@sio.event
async def connect():
    print("Connected to async server. --------------------------------")

#@sio.event
async def disconnect():
    print("Disconnected from server.")



is_own_event = False
event_id = -1



#@sio.on('comp_result')
async def on_row_result(data):
    global is_own_event,event_id
    is_own_event = True
    event_id = str(uuid.uuid4())
    return event_id





#@sio.on('decrypt111')
async def decrypt111(data):
    deser = deserialize(data.get('cipher_text'),"cipher_text")
    val = cc.MultipartyDecryptMain([deser],sk)[0]
    ser_val = await serialize(val)
    await sio.emit('decrypt_reciever',{"client_id":global_id,"share":ser_val})
    return "test"







async def log_combination(log):
    print("log combination start")
    global is_own_event,event_id
    log_list = [trace for trace in log]
    id_list = [[] for _ in range(len(log_list))]
    for trace in range(len(log_list)):
        trace_list = [event for event in log_list[trace]]
        i = 0
        j = 0
        while(i<len(trace_list)+1):
            testit = ""
            if i<len(trace_list):
                time_in_seconds = (int(trace_list[i]["time:timestamp"].timestamp())-1344945316)
                print(time_in_seconds)
                random_factor = randint(0,52)

                enc_tis = cc.MakePackedPlaintext([time_in_seconds])
                enc_rf  = cc.MakePackedPlaintext([random_factor])
                encenc_tis = cc.Encrypt(pk,enc_tis)
                encenc_rf  = cc.Encrypt(pk,enc_rf)
                ser_tis = await serialize(encenc_tis) 
                ser_rf = await serialize(encenc_rf)
                while not is_own_event:
                    testit = await sio.call('submit_row_value', {'client_id': global_id,'finished':False,'trace_index':trace, 'timestamp':ser_tis,"random_factor":ser_rf},timeout=20)
                print("logged id, step: ",i)
                id_list[trace].append(event_id)
                print(event_id)
                is_own_event = False
                i += 1
            else:
                while not testit=="all finished":
                    testit = await sio.call('submit_row_value',{'client_id':global_id,'finished':True,'trace_index':trace})
                    await asyncio.sleep(0.6)
                print("no values left")
                break

    with open("anyonym_log_client_red"+str(global_id)+".json", "w", encoding="utf-8") as file:
        json.dump(id_list, file, indent=4)

    while True:
        await asyncio.sleep(10)

            
        






async def main():
    log = pm4py.objects.log.importer.xes.factory.apply('./reduced_log_sub'+str(global_id)+'.xes')
    
    import_crypto()

    global sio


    class MyClientSession(aiohttp.ClientSession):
        async def ws_connect(self, *args, **kwargs):
            # Set the maximum message size to 100 MB (for example)
            kwargs.setdefault('max_msg_size', 100 * 1024 * 1024)
            return await super().ws_connect(*args, **kwargs)


    session = MyClientSession()

    sio = socketio.AsyncClient(http_session = session)#logger=True, engineio_logger=True,http_session=session)


    sio.on("decrypt111",decrypt111)
    sio.on("comp_result",on_row_result)
    sio.on("connect",connect)
    sio.on("disconnect",disconnect)


    await asyncio.sleep(1)

    await sio.connect("http://localhost:5000",auth={"client_id":global_id}, transports=["websocket"])
    
    await asyncio.sleep(1)

    await log_combination(log)

    await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())