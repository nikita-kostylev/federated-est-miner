from openfhe import *
from math import log2
import json
import os
import copy

#Test my functions on code

def serialize(obj):
    try:
        path = os.path.join("/home/nikita/GitRepos/eST-MIner Python Master/eST-Python/Python/testmest/","1.json")
        # Use module-level SerializeToFile to save the object
        if not SerializeToFile(path, obj, JSON):
            raise RuntimeError("Serialization failed")
        with open(path, "r") as f:
            return {"contents":f.read()}
    except Exception as e:
        print(f"An error occurred: {e}")

def deserialize(obj,keytype):
    try: 
        path = os.path.join("/home/nikita/GitRepos/eST-MIner Python Master/eST-Python/Python/testmest/","2.json")
        with open(path, 'w') as file:
            file.write(obj["contents"])
        if keytype=="public_key":
            key, bool = DeserializePublicKey(path,JSON)
        elif keytype=="eval_key":
            key, bool = DeserializeEvalKey(path,JSON)
        if bool:
            return key
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    print("\n=================RUNNING FOR BFVrns======================\n")
    RunBFVrns()

def RunBFVrns():
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


    ##########################################################
    # Set-up of parameters
    ##########################################################

    # Output the generated parameters
    print(f"p = {cc.GetPlaintextModulus()}")
    print(f"n = {cc.GetCyclotomicOrder() / 2}")
    print(f"log2 q = {log2(cc.GetModulus())}")

    ############################################################
    ## Perform Key Generation Operation
    ############################################################

    print("Running key generation (used for source data)...")

    # Round 1 (party A)




    print("Round 1 (party A) started.")

    kp1 = cc.KeyGen()
    kp2 = cc.MultipartyKeyGen(kp1.publicKey)
    kp3 = cc.MultipartyKeyGen(kp2.publicKey)

    evalMultKey = cc.KeySwitchGen(kp1.secretKey, kp1.secretKey)
    evalMultKey2 = cc.MultiKeySwitchGen(kp2.secretKey, kp2.secretKey, evalMultKey)
    evalMultKey3 = cc.MultiKeySwitchGen(kp3.secretKey, kp3.secretKey, evalMultKey)

    evalMultAB = cc.MultiAddEvalKeys(evalMultKey, evalMultKey2, kp2.publicKey.GetKeyTag())
    evalMultABC = cc.MultiAddEvalKeys(evalMultAB, evalMultKey3, kp3.publicKey.GetKeyTag())
    
    evalMultCABC = cc.MultiMultEvalKey(kp3.secretKey, evalMultABC, kp3.publicKey.GetKeyTag())
    evalMultBABC = cc.MultiMultEvalKey(kp2.secretKey, evalMultABC, kp3.publicKey.GetKeyTag())
    evalMultAABC = cc.MultiMultEvalKey(kp1.secretKey, evalMultABC, kp3.publicKey.GetKeyTag())

    evalMultBCABC = cc.MultiAddEvalMultKeys(evalMultBABC, evalMultCABC, evalMultBABC.GetKeyTag())

    evalMultFinal = cc.MultiAddEvalMultKeys(evalMultAABC, evalMultBCABC, kp3.publicKey.GetKeyTag())
    cc.InsertEvalMultKey([evalMultFinal])


    print("Round 1 of key generation completed.")

    ############################################################
    ## EvalSum Key Generation
    ############################################################

    print("Running evalsum key generation (used for source data)...")

    # Generate evalsum key part for A
    cc.EvalSumKeyGen(kp1.secretKey)
    evalSumKeys = cc.GetEvalSumKeyMap(kp1.secretKey.GetKeyTag())



    evalSumKeysB = cc.MultiEvalSumKeyGen(kp2.secretKey, evalSumKeys, kp2.publicKey.GetKeyTag())
    evalSumKeysC = cc.MultiEvalSumKeyGen(kp3.secretKey, evalSumKeys, kp3.publicKey.GetKeyTag())

    evalSumKeysAB = cc.MultiAddEvalSumKeys(evalSumKeys, evalSumKeysB, kp2.publicKey.GetKeyTag())
    evalSumKeysABC = cc.MultiAddEvalSumKeys(evalSumKeysC, evalSumKeysAB, kp3.publicKey.GetKeyTag())

    cc.InsertEvalSumKey(evalSumKeysABC)

    print("Evalsum key generation completed.")


    cc = serialize(cc)
    pk = serialize(kp3.publicKey)

    ssk = serialize(kp1.secretKey)
    sjsonobj = {"cc":cc,"private_key":ssk,"public_key":pk}
    with open("server_crypto.json", "w") as f:
        json.dump(sjsonobj, f, indent=4)


    c1sk = serialize(kp2.secretKey)
    c1jsonobj = {"cc":cc,"private_key":c1sk,"public_key":pk}
    with open("client_crypto1.json", "w") as f:
        json.dump(c1jsonobj, f, indent=4)


    c2sk = serialize(kp3.secretKey)
    c2jsonobj = {"cc":cc,"private_key":c2sk,"public_key":pk}
    with open("client_crypto2.json", "w") as f:
        json.dump(c2jsonobj, f, indent=4)



    


if __name__ == "__main__":
    main()