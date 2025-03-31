# party.py
import crypten
import crypten.communicator as comm
import torch
import time


def run_party(rank, world_size):
    """
    Function to be run by each party process.
    Initializes CrypTen, sends and receives encrypted data.
    """
    # Initialize CrypTen
    crypten.init()
    comm._init()
    
    print(f"Party {rank} initialized CrypTen.")

    # Example: Party 0 sends data to Party 1 and vice versa
    if rank == 0:
        # Create a tensor to send
        tensor = torch.tensor([1, 2, 3], dtype=torch.float)
        encrypted_tensor = crypten.cryptensor(tensor)
        # Send the encrypted tensor to Party 1
        comm.send(encrypted_tensor, dst=1)
        print(f"Party {rank} sent data to Party 1: {tensor.tolist()}")
    elif rank == 1:
        # Receive the encrypted tensor from Party 0
        received_encrypted = comm.recv(src=0)
        # Decrypt the tensor to get the plain text
        received_tensor = received_encrypted.get_plain_text()
        print(f"Party {rank} received data from Party 0: {received_tensor.tolist()}")

    # Example: Party 1 sends data to Party 0
    if rank == 1:
        # Create a tensor to send
        tensor = torch.tensor([4, 5, 6], dtype=torch.float)
        encrypted_tensor = crypten.cryptensor(tensor)
        # Send the encrypted tensor to Party 0
        comm.send(encrypted_tensor, dst=0)
        print(f"Party {rank} sent data to Party 0: {tensor.tolist()}")
    elif rank == 0:
        # Receive the encrypted tensor from Party 1
        received_encrypted = comm.recv(src=1)
        # Decrypt the tensor to get the plain text
        received_tensor = received_encrypted.get_plain_text()
        print(f"Party {rank} received data from Party 1: {received_tensor.tolist()}")

    # Keep the process alive to maintain communication
    while True:
        time.sleep(10)

