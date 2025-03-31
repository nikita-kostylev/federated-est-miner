#!/bin/bash

tmux send-keys -t logs:0.0 "python3 server3.py" C-m && tmux send-keys -t logs:0.1 "python3 client3.py --client_id 1" C-m && tmux send-keys -t logs:0.2 "python3 client3.py --client_id 2" C-m