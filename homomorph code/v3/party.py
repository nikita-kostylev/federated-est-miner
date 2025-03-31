import crypten
import crypten.communicator as comm
from communication import Communication

class Party:
    def __init__(self, party_id, port, id_to_port):
        self.party_id = party_id
        self.port = port
        self.id_to_port = id_to_port
        self.comm = Communication(party_id, port, id_to_port)
        crypten.init()
        print(f"Party {self.party_id} initialized CrypTen.")

    def share_data(self, target_id, data):
        self.comm.send_data(target_id, data)

    def share(self, target_id, data):
        # Encrypt data using CrypTen before sending
        
        encrypted_data = crypten.cryptensor(data)
        self.share_data(target_id, encrypted_data)


        #self.share_data(target_id, data)
