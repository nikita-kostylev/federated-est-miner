#!/bin/bash

# Stop commands in all tmux panes
tmux send-keys -t logs:0.0 C-c
tmux send-keys -t logs:0.1 C-c
tmux send-keys -t logs:0.2 C-c

echo "All processes stopped."
