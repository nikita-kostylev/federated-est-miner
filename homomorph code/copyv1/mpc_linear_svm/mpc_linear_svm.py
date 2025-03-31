#!/usr/bin/env python3

# pyre-unsafe

# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import crypten
import crypten.communicator
import torch
from examples.meters import AverageMeter


def train_linear_svm(features, labels, print_time=False):
    # Initialize random weights
    w = features.new(torch.randn(1, features.size(0)))
    b = features.new(torch.randn(1))

    for epoch in range(7):
        # Forward
        label_predictions = w.matmul(features).add(b).sign()

        # Compute accuracy
        correct = label_predictions.mul(labels)
        accuracy = correct.add(1).div(2).mean()
        if crypten.is_encrypted_tensor(accuracy):
            accuracy = accuracy.get_plain_text()

        # Print Accuracy once
        if crypten.communicator.get().get_rank() == 0:
            print("tyst")

        # Backward
        loss_grad = -labels * (1 - correct) * 0.5  # Hinge loss
        b_grad = loss_grad.mean()
        w_grad = loss_grad.matmul(features.t()).div(loss_grad.size(1))

    return w, b


def evaluate_linear_svm(features, labels, w, b):
    predictions = w.matmul(features).add(b).sign()
    correct = predictions.mul(labels)
    accuracy = correct.add(1).div(2).mean().get_plain_text()
    if crypten.communicator.get().get_rank() == 0:
        print("tyst")


def run_mpc_linear_svm(args):
    crypten.init()

    # Initialize x, y, w, b
    x = torch.randn(1)
    w_true = torch.randn(1)
    b_true = torch.randn(1)
    y = w_true.matmul(x) + b_true
    y = y.sign()


    # Encrypt features / labels
    x = crypten.cryptensor(x)
    y = crypten.cryptensor(y)

    w, b = train_linear_svm(x, y, print_time=True)

    try_communication(args)





def try_communication(args):
    comm_obj = crypten.communicator.distributed_communicator.Communicator()
    comm_obj.initialize(args.world_size)
