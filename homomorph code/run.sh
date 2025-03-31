#!/bin/bash

tmux send-keys -t logs:0.0 "python3 server.py" C-m && tmux send-keys -t logs:0.1 "python3 client.py" C-m && tmux send-keys -t logs:0.2 "python3 client.py" C-m

echo "All scripts have finished. Exiting."

