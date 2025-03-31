import numpy as np
from openfhe import *
import requests
import threading
import time
import base64
import os
import tempfile
import json
import sys
from pm4py import *
import pm4py
from random import randint
from datetime import datetime
import socketio
import asyncio

PARTIES = 2



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
parameters.SetThresholdNumOfParties(5)
parameters.SetMultiplicationTechnique(HPSPOVERQLEVELED)

cc = GenCryptoContext(parameters)
# Enable features you wish to use
cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)
cc.Enable(ADVANCEDSHE)
cc.Enable(MULTIPARTY)

global_id = 0

finished_cc = cc

final_public_key = ""

global_keypair = ""




def serialize(obj):
    try:
        path = os.path.join("../testmest/",global_id+".json")
        # Use module-level SerializeToFile to save the object
        if not SerializeToFile(path, obj, JSON):
            raise RuntimeError("Serialization failed")
        with open(path, "r") as f:
            return {"contents":f.read()}
    except Exception as e:
        print(f"An error occurred: {e}")

def serialize_auto(cc):
    try:
        path = os.path.join("/home/nikita/GitRepos/eST-MIner Python Master/eST-Python/Python/testmest/",global_id+".json")
        # Use module-level SerializeToFile to save the object
        if not cc.SerializeEvalAutomorphismKey(path, JSON):
            raise RuntimeError("Serialization failed")
        with open(path, "r") as f:
            return {"contents":f.read()}
    except Exception as e:
        print(f"An error occurred: {e}")

def deserialize(obj,keytype):
    try: 
        path = os.path.join("../testmest/",global_id+".json")
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


def client_process(client_num):
    print(f"Client {client_num} starting crypto context generation")
    
    # Register with server
    response = requests.post('http://localhost:5000/keygen/register')
    client_data = response.json()
    client_id = client_data["client_id"]
    global global_id
    global_id = str(client_id)
    print(f"Client {client_num} got ID {client_id}")
    


    
    # Step 1: Send public key
    current_step = client_id
    phase = 1
    while True:
        print(phase)
        if phase == 1:    
            #request whether its ones turn
            response = requests.post(
                f'http://localhost:5000/keygen/step/1/{current_step}',
                json={"client_id": client_id}
            ).json()
            #wait if its not ones turn
            if response["status"] == "wait":
                time.sleep(1)
                continue
            #exec code for if its ones turn
            else:
                print(f"Client ID {client_id} phase 1 start")
                prev_pub_key = deserialize(response["previous_public_key"],"public_key")
                first_evalmult_key = deserialize(response["first_evalmult_key"],"eval_key")
                keypair = cc.MultipartyKeyGen(prev_pub_key)
                global global_keypair
                global_keypair = keypair
                evalmultkey = cc.MultiKeySwitchGen(keypair.secretKey,keypair.secretKey,first_evalmult_key)
                serialized_public_key = serialize(keypair.publicKey)
                #print("SerialiesierterPublikerwer",serialized_public_key)
                serialized_evalmult_key = serialize(evalmultkey)
                response = requests.post(
                    f'http://localhost:5000/keygen/step/1/{current_step}',
                    json={"client_id": client_id, "public_key": serialized_public_key, "evalmult_key":serialized_evalmult_key}
                )
                print(f"Client ID {client_id} phase 1 end")
                phase += 1
        if phase == 2:
            #request whether its ones turn
            response = requests.post(
                f'http://localhost:5000/keygen/step/2/{current_step}',
                json={"client_id": client_id}
            ).json()
            #wait if its not ones turn
            if response["status"] == "wait":
                print("waiting")
                time.sleep(1)
                continue
            #exec code for if its ones turn
            else:
                print(f"Client ID {client_id} phase 2 start")
                evalonehalf = deserialize(response["eval1/2"],"eval_key")
                pk5 = deserialize(response["pk5"],"public_key")
                evalMultFinished = cc.MultiMultEvalKey(keypair.secretKey, evalonehalf, pk5.GetKeyTag())
                serialized_evalmult_key = serialize(evalMultFinished)
                response = requests.post(
                    f'http://localhost:5000/keygen/step/2/{current_step}',
                    json={"client_id": client_id, "eval1/2":serialized_evalmult_key}
                )
                print(f"Client ID {client_id} phase 2 end")
                phase += 1
        if phase == 3:
            #request whether its ones turn
            response = requests.post(
                f'http://localhost:5000/keygen/step/3/{current_step}',
                json={"client_id": client_id}
            ).json()
            #wait if its not ones turn
            if response["status"] == "wait":
                time.sleep(1)
                continue
            #exec code for if its ones turn
            else:
                print(f"Client ID {client_id} phase 3 start")
                if response["status"]=="eval_mult_final_response":
                    evalmultfinal = deserialize(response["evalmult"],"eval_key")
                    cc.InsertEvalMultKey([evalmultfinal])
                    #sk1 = deserialize(response["secret_key1"],"private_key")
                    #deserialize_auto(response["first_slice"],cc)
                    #evalsum1 = cc.GetEvalSumKeyMap(sk1.GetKeyTag())
                    #evalsumslice2 = cc.MultiEvalSumKeyGen(keypair.secretKey, evalsum1, keypair.publicKey.GetKeyTag())
                    #ser_evalsumslice2 = serialize_auto(cc)
                    #keytag = keypair.secretKey.GetKeyTag()
                    secret = serialize(keypair.secretKey)
                    response = requests.post(
                        f'http://localhost:5000/keygen/step/3/{current_step}',
                        #json={"client_id": client_id, "evalsum2":ser_evalsumslice2, "keytag":keytag }
                        json = {"client_id":client_id, "secret":secret}
                    )
                print(f"Client ID {client_id} phase 3 end")
                phase += 1
        if phase == 4:
            response = requests.post(
                f'http://localhost:5000/keygen/step/4/{current_step}',
                json={"client_id": client_id}
            ).json()
            if response["status"] == "wait":
                time.sleep(1)
                continue
            else:
                full_cc = deserialize(response["cc"],"cc")
                publickey = deserialize(response["public_key"],"public_key")
                pp = cc.MakePackedPlaintext([1,1])
                ppp = cc.Encrypt(publickey,pp)
                pppp = cc.EvalMult(ppp,ppp)
                print("Crypto context generation finished")
                response = requests.post(
                    f'http://localhost:5000/signoff/{current_step}',
                    json={"client_id": client_id}
                )
                return full_cc,publickey













finished_cc,final_public_key = client_process(1)

cc.Encrypt(final_public_key,cc.MakePackedPlaintext([1,2,3]))

jsonobj = {"cc":serialize(finished_cc),"private_key":serialize(global_keypair.secretKey),"public_key":serialize(final_public_key)}
with open("client_crypto"+global_id+".json", "w") as f:
    json.dump(jsonobj, f, indent=4)

print("exit finished")
sys.exit(1)