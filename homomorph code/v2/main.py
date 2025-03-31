# main.py
import torch.multiprocessing as mp
from party import run_party

def main():
    world_size = 2  # Adjustable parameter for the number of parties

    # Spawn processes for each party
    mp.spawn(run_party,
             args=(world_size,),
             nprocs=world_size,
             join=True)

if __name__ == "__main__":
    main()