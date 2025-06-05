#!/usr/bin/env python3

# IBM Confidential
# © Copyright IBM Corp. 2025

"""
Credit Card Fraud Dataset
"""

from collections.abc import Generator
import math
import os
from pathlib import Path
import pickle as pk
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn_pandas import DataFrameMapper
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import FunctionTransformer
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelBinarizer
from sklearn.impute import SimpleImputer


def time_encoder(x: pd.DataFrame) -> pd.DataFrame:
    """
    Encoder for time data.
    """

    x_hm = x['Time'].str.split(':', expand=True)
    x_date = pd.DataFrame({
        'year': x['Year'],
        'month': x['Month'],
        'day': x['Day'],
        'hour': x_hm[0],
        'minute': x_hm[1]})
    d = pd.to_datetime(x_date).astype(np.int64)
    return pd.DataFrame(d)


def amt_encoder(x: pd.Series) -> pd.DataFrame:
    """
    Encoder for decimal data.
    """

    amt = x.apply(lambda amt: amt[1:]).astype(np.float32).map(
        lambda amt: max(1, amt)).map(math.log)
    return pd.DataFrame(amt)


def decimal_encoder(x: np.ndarray[Any, Any], length: int = 5) -> pd.DataFrame:
    """
    Encoder for integer data.
    """

    x_new = pd.DataFrame()
    for i in range(length):
        x_new[i] = np.mod(x, 10)
        x = np.floor_divide(x, 10)
    return x_new


def fraud_encoder(x: pd.Series) -> np.ndarray[np.int64, Any]:
    """
    Encoder for boolean data.
    """

    return np.where(x == 'Yes', 1, 0).astype(np.int64)


def create_test_set(
    df: pd.DataFrame,
    indices: np.ndarray[np.int64, Any],
    seq_length: int
):
    """
    Writes test data and indices to files.
    """

    rows = indices.shape[0]
    index_array = np.zeros((rows, seq_length), dtype=np.int64)
    for i in range(seq_length):
        index_array[:, i] = indices + 1 - seq_length + i
    uniques = np.unique(index_array.flatten())
    df.loc[uniques].to_csv('./test_10k.csv', index_label='Index')
    np.savetxt('./test_10k.indices', indices.astype(np.int64), fmt='%d')


def create_data_sets(csv_path: Path, seq_length: int) \
        -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """
    Reads csv from path and creates training, validation, and test indices.
    """

    x_original = pd.read_csv(csv_path)

    x_original.sort_values(by=['User', 'Card'], inplace=True)
    x_original.reset_index(inplace=True, drop=True)
    x_original.info()

    # Get first of each User-Card combination
    first = x_original[['User', 'Card']].drop_duplicates()
    f = np.array(first.index)
    print(first)

    # Drop the first N transactions
    drop_list = np.concatenate([np.arange(x, x + seq_length - 1) for x in f])
    index_list = np.setdiff1d(x_original.index.values, drop_list)

    # Split into 0.5 train, 0.3 validate, 0.2 test
    tot_length = index_list.shape[0]
    train_length = tot_length // 2
    validate_length = (tot_length - train_length) * 3 // 5
    test_length = tot_length - train_length - validate_length
    print(tot_length, train_length, validate_length, test_length)

    # Generate list of indices for train, validate, test
    np.random.seed(1111)
    train_indices = np.random.choice(index_list, train_length, replace=False)
    tv_list = np.setdiff1d(index_list, train_indices)
    validate_indices = np.random.choice(
        tv_list, validate_length, replace=False)
    test_indices = np.setdiff1d(tv_list, validate_indices)

    # Write test data and indices to file
    create_test_set(x_original, test_indices[:10000], seq_length)

    return (x_original, train_indices, validate_indices, test_indices)


def map_sample(
    df: pd.DataFrame,
    fraud_indices: np.ndarray,
    non_fraud_indices: np.ndarray,
    mapper: DataFrameMapper,
    seq_length: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Maps equal distribution of fraud_indices and non_fraud_indices of df, using
    the provided mapper, and returns as inputs and labels.
    """

    indices = np.concatenate((fraud_indices, np.random.choice(
        non_fraud_indices, fraud_indices.shape[0], replace=False)))
    np.random.shuffle(indices)
    rows = indices.shape[0]
    index_array = np.zeros((rows, seq_length), dtype=np.int64)
    for i in range(seq_length):
        index_array[:, i] = indices + 1 - seq_length + i
    full_df = mapper.transform(df.loc[index_array.flatten()])
    data = full_df.drop(['Is Fraud?'], axis=1).to_numpy().reshape(
        [rows, seq_length, -1]
    )
    targets = full_df['Is Fraud?'].to_numpy().reshape(rows, seq_length, 1)
    # Take the label for the final sample in sequence as the sequence label.
    targets = targets[:, -1, :]

    return (data, targets)


def gen_training_batch(
    df: pd.DataFrame,
    mapper: DataFrameMapper,
    index_list: np.ndarray,
    batch_size: int,
    seq_length: int
) -> Generator[tuple[np.ndarray, np.ndarray]]:
    """
    Generator that generate class balanced batches with the following shape:
        data    = [batch_size, seq_length, -1]
        targets = [batch_size, seq_length, 1]
    """

    np.random.seed(98765)

    train_df = df.loc[index_list]
    fraud_indices = train_df[train_df['Is Fraud?'] == 'Yes'].index.values
    non_fraud_indices = train_df[train_df['Is Fraud?'] == 'No'].index.values
    del train_df

    while True:
        data, targets = map_sample(
            df,
            fraud_indices,
            non_fraud_indices,
            mapper,
            seq_length
        )
        count = 0
        while (count + batch_size) <= data.shape[0]:
            batch_data = data[count:count + batch_size]
            batch_targets = targets[count:count + batch_size]
            count += batch_size
            yield batch_data, batch_targets

def prepare_training_data(batch_size: int, seq_length: int) \
        -> Generator[tuple[np.ndarray, np.ndarray]]:
    """
    Setup to get the inference data.
    Return the inference data and labels.
    """

    # Path to data set inside the container
    csv_path = Path('/data/card_transaction.v1.csv')

    x_original, train_indices, _, _ = create_data_sets(csv_path, seq_length)

    mapper = DataFrameMapper([
        ('Is Fraud?', FunctionTransformer(fraud_encoder)),
        (['Merchant State'], [SimpleImputer(strategy='constant'),
                              FunctionTransformer(np.ravel),
                              LabelEncoder(),
                              FunctionTransformer(decimal_encoder),
                              OneHotEncoder()]),
        (['Zip'], [SimpleImputer(strategy='constant'),
                   FunctionTransformer(np.ravel),
                   FunctionTransformer(decimal_encoder),
                   OneHotEncoder()]),
        ('Merchant Name', [LabelEncoder(),
                           FunctionTransformer(decimal_encoder),
                           OneHotEncoder()]),
        ('Merchant City', [LabelEncoder(),
                           FunctionTransformer(decimal_encoder),
                           OneHotEncoder()]),
        ('MCC', [LabelEncoder(),
                 FunctionTransformer(decimal_encoder),
                 OneHotEncoder()]),
        (['Use Chip'], [SimpleImputer(strategy='constant'), LabelBinarizer()]),
        (['Errors?'], [SimpleImputer(strategy='constant'), LabelBinarizer()]),
        (['Year', 'Month', 'Day', 'Time'], [FunctionTransformer(time_encoder),
                                            MinMaxScaler()]),
        ('Amount', [FunctionTransformer(amt_encoder), MinMaxScaler()])
    ], input_df=True, df_out=True)

    if os.path.exists('./fitted_mapper.pkl'):
        print('Loading saved mapper . . .')
        with open('./fitted_mapper.pkl', 'rb') as f:
            fitted_mapper = joblib.load(f)
    else:
        print('Fitting mapper . . .')
        fitted_mapper = mapper.fit(x_original)

        # Write mapper to file
        with open('./fitted_mapper.pkl', 'wb') as f:
            pk.dump(fitted_mapper, f)

    # Pre-process the inference data
    return gen_training_batch(
        x_original,
        fitted_mapper,
        train_indices,
        batch_size,
        seq_length
    )