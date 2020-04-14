# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from copy import deepcopy
import numpy as np

from .utils import torch_installed, lightgbm_installed, xgboost_installed
from ._topology import convert_topology
from ._parse import parse_sklearn_api_model

# Invoke the registration of all our converters.
from . import operator_converters  # noqa


def convert_sklearn(model, test_input=None, device=None, extra_config={}):
    """
    This function produces, given a scikit-learn model, an equivalent model in the selected backend.
    The supported operators and backends be found at :func:`supported_converters <hummingbird._supported_opeartors>`.

    For pipeline conversion, user needs to make sure each component
    is one of our supported items.

    This function converts the specified *scikit-learn* model into its *PyTorch* counterpart.

    :param model: A scikit-learn model
    :param test_input: some input data used to trace the model execution
    :param device: Which device to translate the model to. CPU by defauls
    :param extra_config: Extra configurations to be used by the individual operator converters
    :return: A model implemented in PyTorch, which is equivalent to the input scikit-learn model
    """
    assert torch_installed(), "To use Hummingbird you need to instal torch."

    # Parse scikit-learn model as our internal data structure (i.e., Topology)
    # We modify the scikit learn model during optimizations.
    model = deepcopy(model)
    topology = parse_sklearn_api_model(model)

    # Convert our Topology object into PyTorch.
    hb_model = convert_topology(topology, device, extra_config)
    return hb_model


def convert_lightgbm(model, test_input=None, device=None, extra_config={}):
    """
    This function is used to generate a PyTorch model from a given LighGBM model
    :param model: A LightGBM model (trained using the scikit-learn API)
    :param test_input: some input data used to trace the model execution
    :param backend: Which backend to translate the model to. PyTorch by default
    :param device: Which device to translate the model to. CPU by defauls
    :param extra_config: Extra configurations to be used by the individual operator converters
    :return: A backend model which is equivalent to the input LightGBM model
    """
    assert lightgbm_installed(), "To convert LightGBM models you need to instal LightGBM."

    return convert_sklearn(model, test_input, device, extra_config)


def convert_xgboost(model, test_input, device=None, extra_config={}):
    """
    This function is used to generate a PyTorch model from a given XGBoost model
    :param model: A XGBoost model (trained using the scikit-learn API)
    :param test_input: some input data used to trace the model execution
    :param device: Which device to translate the model to. CPU by defauls
    :param extra_config: Extra configurations to be used by the individual operator converters
    :return: A PyTorch model which is equivalent to the input XGBoost model
    """
    assert xgboost_installed(), "To convert XGboost models you need to instal XGBoost."

    # For XGBoostRegressor and Classifier have different API for extracting the number of features.
    # In the former case we need to infer them from the test_input.
    if "_features_count" in dir(model):
        extra_config["n_features"] = model._features_count
    elif test_input is not None:
        if type(test_input) is np.ndarray and len(test_input.shape) == 2:
            extra_config["n_features"] = test_input.shape[1]
        else:
            raise RuntimeError(
                "XGBoost converter is not able to infer the number of input features.\
                    Apparently test_input is not an ndarray. \
                    Please fill an issue on https://github.com/microsoft/hummingbird/"
            )
    else:
        raise RuntimeError(
            "XGBoost converter is not able to infer the number of input features.\
                Please pass some test_input to the converter."
        )
    return convert_sklearn(model, test_input, device, extra_config)
