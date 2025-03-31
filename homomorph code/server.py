import numpy as np
from base64 import decodebytes
from flask import Flask, request
from threading import Lock
from openfhe import *  
import os 
import json
import time
from flask_socketio import SocketIO, emit
import sys


app = Flask(__name__)
socketio = SocketIO(app)



NUMBER_OF_PARTIES = 2

NUMBER_OF_CASES = 2948


#Generate homomorphic Context
plaintextModulus = 26017793
sigma = 3.2
securityLevel = SecurityLevel.HEStd_128_classic

batchSize = 4
multDepth = 4
digitSize = 30
dcrtBits = 60

parameters = CCParamsBFVRNS() 
parameters.SetPlaintextModulus(plaintextModulus)
parameters.SetSecurityLevel(securityLevel)
parameters.SetStandardDeviation(sigma)
parameters.SetSecretKeyDist(UNIFORM_TERNARY)
parameters.SetMultiplicativeDepth(multDepth)
parameters.SetBatchSize(batchSize)
parameters.SetDigitSize(digitSize)
parameters.SetScalingModSize(dcrtBits)
parameters.SetThresholdNumOfParties(NUMBER_OF_PARTIES)
parameters.SetMultiplicationTechnique(HPSPOVERQLEVELED)

cc = GenCryptoContext(parameters)
# Enable features you wish to use
cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)
cc.Enable(ADVANCEDSHE)
cc.Enable(MULTIPARTY)

server_state = {
    "clients": {0:
                {
            "step": 0,
            "public_key": None,
            "secret_key": None,
            "shared_secret": None
            }
            },
    "current_step": 0,
    "current_phase":1,
    "lock": Lock(),
    "max_clients": NUMBER_OF_PARTIES,
    "eval_sum1":0,
    "eval_mult":0
}

#(De)Serialization of openfhe objects
def serialize(obj):
    try:
        path = os.path.join("../testmest/","0.json")
        # Use module-level SerializeToFile to save the object
        if not SerializeToFile(path, obj, JSON):
            raise RuntimeError("Serialization failed")
        with open(path, "r") as f:
            return {"contents":f.read()}
    except Exception as e:
        print(f"An error occurred: {e}")

def deserialize(obj,keytype):
    try: 
        bool = False
        path = os.path.join("../testmest/","2.json")
        with open(path, 'w') as file:
            file.write(obj["contents"])
        if keytype=="public_key":
            key, bool = DeserializePublicKey(path,JSON)
        if keytype=="eval_key":
            key, bool = DeserializeEvalKey(path,JSON)
        if keytype=="private_key":
            key, bool = DeserializePrivateKey(path,JSON)
        if keytype=="cc":
            key, bool = DeserializeCryptoContext(path,JSON)
        if bool:
            return key
    except Exception as e:
        print(f"An error occurred: {e}")

#Creation of openfhe crypto context
@app.route('/keygen/register', methods=['POST'])
def register_client():
    with server_state["lock"]:
        
        client_id = len(server_state["clients"])
        server_state["clients"][client_id] = {
            "step": 0,
            "public_key": None,
            "shared_secret": None
        }
        
        print(f"Client {client_id} registered")
        
        if len(server_state["clients"]) == server_state["max_clients"]:
            print("All clients registered. Starting key exchange...")

        
        return {"status": "success", "client_id": client_id}

@app.route('/keygen/step/<int:phase>/<int:step>', methods=['POST'])
def handle_step(phase,step):
    data = request.json
    client_id = data["client_id"]
    print(server_state["current_step"],server_state["current_phase"],step,phase)
    with server_state["lock"]:
        if server_state["current_step"]>server_state["max_clients"]:
            print("phase changed")
            server_state["current_phase"] += 1
            server_state["current_step"] = 0
        if phase != server_state["current_phase"]:
            return {"status":"wait","timer":5}
        if phase == 1:
            #Wait until its ones turn
            if step != server_state["current_step"]:
                if server_state["current_step"]==0:
                    keypair = cc.KeyGen()
                    server_state["clients"][0]["public_key"] = keypair.publicKey
                    server_state["clients"][0]["secret_key"] = keypair.secretKey
                    evalmultkey = cc.KeySwitchGen(keypair.secretKey,keypair.secretKey)
                    server_state["clients"][0]["evalmult_key"] = evalmultkey
                    server_state["clients"][0]["collective_evalmult_key"] = evalmultkey
                    server_state["current_step"] += 1
                return {"status": "wait"}
            print(f"Client ID {client_id} phase 1 start")
            client = server_state["clients"][client_id]
            #send previous key information
            if not 'public_key' in data:
                fek = serialize(server_state["clients"][client_id-1]["evalmult_key"])            
                ppk = serialize(server_state["clients"][client_id-1]["public_key"])
                return{
                    "status":"key_response",
                    "previous_public_key":ppk,
                    "first_evalmult_key":fek           
                    }
            #store recieved key information
            elif 'public_key' in data:
                client["public_key"]   = deserialize(data["public_key"],"public_key")
                client["evalmult_key"] = deserialize(data["evalmult_key"],"eval_key")
                client["collective_evalmult_key"] = cc.MultiAddEvalKeys(server_state["clients"][client_id-1]["collective_evalmult_key"],client["evalmult_key"],client["public_key"].GetKeyTag())
                server_state["current_step"] += 1
                print(f"Client ID {client_id} phase 1 end")
                return {"status": "proceed"}
        if phase == 2:
             #Wait until its ones turn
            if step != server_state["current_step"]:
                if server_state["current_step"]==0:
                    server_state["clients"][0]["collective_evalmult_key"] = cc.MultiMultEvalKey(server_state["clients"][0]["secret_key"], server_state["clients"][NUMBER_OF_PARTIES]["collective_evalmult_key"], server_state["clients"][0]["secret_key"].GetKeyTag())
                    server_state["current_step"] += 1
                return {"status": "wait"}
            print(f"Client ID {client_id} phase 2 start")
            client = server_state["clients"][client_id]
            #send previous key information
            if not 'eval1/2' in data:
                evalonehalf = serialize(server_state["clients"][server_state["max_clients"]-1]["evalmult_key"])            
                return{
                    "status":"key_response",
                    "eval1/2":evalonehalf,
                    "pk5":serialize(server_state["clients"][NUMBER_OF_PARTIES]["public_key"])
                    }
            #store recieved key information
            elif 'eval1/2' in data:
                client["eval1/2"]   = deserialize(data["eval1/2"],"eval_key")
                print(f"Client ID {client_id} phase 2 end")
                server_state["current_step"] += 1 
                return {"status":"eval_mult_key_finished"}
        if phase == 3:
             #Wait until its ones turn
            if step != server_state["current_step"]:
                if server_state["current_step"] == 0:
                    temp = server_state["clients"][NUMBER_OF_PARTIES]["eval1/2"]
                    for g in range(NUMBER_OF_PARTIES-1,0,-1):
                        adding = server_state["clients"][g]["eval1/2"]
                        temp = cc.MultiAddEvalMultKeys(adding,temp,adding.GetKeyTag())
                    final = cc.MultiAddEvalMultKeys(server_state["clients"][0]["collective_evalmult_key"],temp,server_state["clients"][NUMBER_OF_PARTIES]["public_key"].GetKeyTag())
                    cc.InsertEvalMultKey([final])
                    cc.EvalSumKeyGen(server_state["clients"][0]["secret_key"])
                    server_state["eval_sum1"] = cc.GetEvalSumKeyMap(server_state["clients"][0]["secret_key"].GetKeyTag())
                    server_state["clients"][0]["collective_evalsum_key"] = server_state["eval_sum1"]
                    server_state["current_step"] += 1
                    server_state["eval_mult"] = final
                return {"status": "wait"}
            print(f"Client ID {client_id} start phase 3")
            client = server_state["clients"][client_id]
            #send previous key information
            evalmult = serialize(server_state["eval_mult"])
            fs = serialize_auto(cc)
            sk1 = serialize(server_state["clients"][0]["secret_key"])
            if not "secret" in data:
                return{
                    "status":"eval_mult_final_response",
                    "evalmult":evalmult,
                    "first_slice":fs,
                    "secret_key1":sk1
                }
            elif "secret" in data:
                evalsum1 = server_state["eval_sum1"]
                secret = deserialize(data["secret"],"private_key")
                share = cc.MultiEvalSumKeyGen(secret,evalsum1,server_state["clients"][step]["public_key"].GetKeyTag())
                keygen = cc.MultiAddEvalSumKeys(share,server_state["clients"][step-1]["collective_evalsum_key"],client["public_key"].GetKeyTag())
                client["collective_evalsum_key"] = keygen
                server_state["current_step"] += 1
            print(f"Client ID {client_id} end phase 3")
            return{
                "status":"key_response"
            }
        if phase == 4:
            if step != server_state["current_step"]:
                if server_state["current_step"] == 0:
                    cc.InsertEvalSumKey(server_state["clients"][NUMBER_OF_PARTIES]["collective_evalsum_key"])
                    server_state["current_step"] += 1
                return {"status": "wait"}
            ser_cc = serialize(cc)
            pub_key = serialize(server_state["clients"][NUMBER_OF_PARTIES]["public_key"])
            server_state["public_key_final"] = pub_key
            server_state["current_step"] += 1
            return{
                 "status":"cc_response",
                 "cc":ser_cc,
                 "public_key":pub_key
            }


@app.route('/signoff/<int:client_id>',methods=['POST'])
def signoff(client_id):
    server_state["clients"].pop(client_id)
    print("client removed")
    if len(server_state["clients"])==1:
        print(server_state["clients"])
        scc = serialize(cc)
        ssk = serialize(server_state['clients'][0]['secret_key'])
        spk =  server_state['public_key_final']
        jsonobj = {"cc":scc,"private_key":ssk,"public_key":spk}
        with open("server_crypto.json", "w") as f:
            json.dump(jsonobj, f, indent=4)
    return{
        "status":"finished"
    }
        






socketio.run(app, host='0.0.0.0', port=5000)