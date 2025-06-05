#!/usr/bin/env python3

# IBM Confidential
# © Copyright IBM Corp. 2025

"""
Credit Card Fraud Training
"""

import argparse
from collections.abc import Generator
import os

import numpy as np
from sklearn.metrics import confusion_matrix
import torch
import tqdm

import credit_card_fraud_data_utils


class RNNModel(torch.nn.Module):
    """
    RNN model.
    """

    def __init__(self, rnn_type: str = 'lstm'):
        super().__init__()
        if rnn_type == 'lstm':
            rnn_module = torch.nn.LSTM
        else:
            rnn_module = torch.nn.GRU
        self.rnn = rnn_module(220, 200, num_layers=2, batch_first=True)
        self.fc = torch.nn.Linear(200, 1)
        self.sig = torch.nn.Sigmoid()

    def forward(self, x: torch.Tensor):
        """
        Forward pass.
        """

        # Only use the output, ignoring the state.
        out, _ = self.rnn(x)
        # Only use the final sample of each output sequence.
        out = out[:, -1, :]
        return self.sig(self.fc(out))


def f1(conf: np.ndarray) -> float:
    """
    Returns the f1 score of the passed confusion matrix.
    """

    precision = float(conf[1][1]) / (conf[1][1] + conf[0][1])
    recall = float(conf[1][1]) / (conf[1][1] + conf[1][0])
    return 2 * precision * recall / (precision + recall)


def train_model(model: torch.nn.Module, train_generator: Generator):
    """
    Trains the model on the training dataset for 3 epochs.
    Generates 1000 batches of batch_size per-epoch
    """

    optimizer = torch.optim.Adam(model.parameters())
    loss_function = torch.nn.BCELoss()

    epochs = 3
    steps_per_epoch = 1000

    conf = np.zeros([2, 2], dtype=int)
    loss_list = []

    model.train()

    for epoch in range(1, epochs+1):
        # iterate over the training data
        for count in tqdm.tqdm(range(1, steps_per_epoch+1)):
            inputs, labels = next(train_generator)
            inputs = torch.as_tensor(inputs, dtype=torch.float32)
            labels = torch.as_tensor(labels, dtype=torch.float32)

            optimizer.zero_grad()

            with torch.set_grad_enabled(True):
                outputs = model(inputs)
                loss = loss_function(outputs, labels)

                loss.backward()
                optimizer.step()

            prediction = (outputs.detach().numpy() > 0.5).astype(int)
            loss_list.append(loss.item())
            conf += confusion_matrix(labels, prediction)

            if count % 100 == 0:
                print('Epoch:', epoch, 'Iteration:', count, 'f1 score:',
                      f1(conf), 'Mean loss:', np.mean(loss_list), 'Max loss:',
                      np.max(loss_list))
                print(conf)
                loss_list = []
                conf = np.zeros([2, 2], dtype=int)


def main(rnn_type: str = 'lstm', batch_size: int = 100, seq_length: int = 7):
    """
    main
    """

    train_generator = credit_card_fraud_data_utils.prepare_training_data(batch_size, seq_length)

    model = RNNModel(rnn_type)

    print(model)
    for name, param in model.named_parameters():
        print(name, param.size())

    train_model(model, train_generator)

    # Save model to /models directory mount inside the container
    if not os.path.exists('/models'):
        os.makedirs('/models')
    pt_model_path = f'/models/ccfd.pt'
    torch.save(model, pt_model_path)

    # Export model to onnx file.
    input_data, _ = next(train_generator)
    inputs = torch.from_numpy(input_data).float()[:1]
    onnx_model_path = f'/models/ccfd.onnx'
    torch.onnx.export(model, inputs, onnx_model_path, export_params=True)


if __name__ == '__main__':
    # CLI interface
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--rnn-type',
        type=str.lower,
        choices=['lstm', 'gru'],
        default='lstm',
        help='RNN type used within model (default: lstm)',
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for training data (default: 32)',
    )
    parser.add_argument(
        '--seq-length',
        type=int,
        default=7,
        help='Sequence length for training data (default: 7)',
    )
    args = parser.parse_args()

    main(args.rnn_type, args.batch_size, args.seq_length)
