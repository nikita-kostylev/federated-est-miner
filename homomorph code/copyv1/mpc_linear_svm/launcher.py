#!/usr/bin/env python3

# pyre-unsafe

# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import argparse

from examples.multiprocess_launcher import (
    MultiProcessLauncher,
)

from mpc_linear_svm import run_mpc_linear_svm  # @manual

parser = argparse.ArgumentParser(description="CrypTen Linear SVM Training")
parser.add_argument(
    "--world_size",
    type=int,
    default=2,
    help="The number of parties to launch. Each party acts as its own process",
)


def main():
    args = parser.parse_args()
    launcher = MultiProcessLauncher(args.world_size, run_mpc_linear_svm(args), args)
    launcher.start()
    launcher.join()
    launcher.terminate()


if __name__ == "__main__":
    main()
