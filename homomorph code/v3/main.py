import multiprocessing
from party import Party
import time
import socket


def get_available_ports(num_ports, start_port=5000):
    ports = []
    port = start_port
    while len(ports) < num_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                ports.append(port)
            except socket.error:
                pass
            port += 1
    return ports


def run_party(party_id, port, id_to_port):
    party = Party(party_id, port, id_to_port)
    time.sleep(1)  # Wait for all parties to initialize
    # Example: Party 0 sends data to Party 1
    if party_id == 0:
        party.share(1, 1234)
    elif party_id == 1:
        party.share(0, 5678)
    # Add more sharing logic as needed
    while True:
        time.sleep(10)  # Keep the process alive

if __name__ == "__main__":
    num_parties = 2  # Adjustable parameter
    ports = get_available_ports(num_parties)
    id_to_port = {i: port for i, port in enumerate(ports)}

    processes = []
    for party_id in range(num_parties):
        p = multiprocessing.Process(target=run_party, args=(party_id, ports[party_id], id_to_port))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()