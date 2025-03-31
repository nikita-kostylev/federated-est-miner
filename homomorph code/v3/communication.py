import socket
import threading

class Communication:
    def __init__(self, party_id, port, id_to_port):
        self.party_id = party_id
        self.port = port
        self.id_to_port = id_to_port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('localhost', self.port))
        self.server.listen()
        self.connections = {}
        self.start_server()

    def start_server(self):
        thread = threading.Thread(target=self.listen_for_connections, daemon=True)
        thread.start()

    def listen_for_connections(self):
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn,), daemon=True)
            thread.start()

    def handle_client(self, conn):
        with conn:
            data = conn.recv(4096)
            if data:
                print(f"Party {self.party_id} received data: {data.decode()}")

    def send_data(self, target_id, data):
        target_port = self.id_to_port[target_id]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', target_port))
            s.sendall(data.encode())
        print(f"Party {self.party_id} sent data to Party {target_id}: {data}")