# -*- coding: utf-8 -*-
# Copyright (C) 2018-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Iterable, Union, Optional, Dict
from pathlib import Path
import warnings

import numpy as np

from openvino._pyopenvino import Model as ModelBase
from openvino._pyopenvino import Core as CoreBase
from openvino._pyopenvino import CompiledModel as CompiledModelBase
from openvino._pyopenvino import AsyncInferQueue as AsyncInferQueueBase
from openvino._pyopenvino import Tensor
from openvino._pyopenvino import Node

from openvino.runtime.utils.data_helpers import (
    OVDict,
    _InferRequestWrapper,
    _data_dispatch,
    tensor_from_file,
)


def _deprecated_memory_arg(shared_memory: bool, share_inputs: bool) -> bool:
    if shared_memory is not None:
        warnings.warn(
            "`shared_memory` is deprecated and will be removed in 2024.0. "
            "Value of `shared_memory` is going to override `share_inputs` value. "
            "Please use only `share_inputs` explicitly.",
            FutureWarning,
            stacklevel=3,
        )
        return shared_memory
    return share_inputs


class Model(ModelBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args and not kwargs:
            if isinstance(args[0], ModelBase):
                super().__init__(args[0])
            elif isinstance(args[0], Node):
                super().__init__(*args)
            else:
                super().__init__(*args)
        if args and kwargs:
            super().__init__(*args, **kwargs)
        if kwargs and not args:
            super().__init__(**kwargs)

    def clone(self) -> "Model":
        return Model(super().clone())

    def __deepcopy__(self, memo: Dict) -> "Model":
        """Returns a deepcopy of Model.

        :return: A copy of Model.
        :rtype: openvino.runtime.Model
        """
        return Model(super().clone())


class InferRequest(_InferRequestWrapper):
    """InferRequest class represents infer request which can be run in asynchronous or synchronous manners."""

    def infer(
        self,
        inputs: Any = None,
        share_inputs: bool = False,
        share_outputs: bool = False,
        *,
        shared_memory: Any = None,
    ) -> OVDict:
        """Infers specified input(s) in synchronous mode.

        Blocks all methods of InferRequest while request is running.
        Calling any method will lead to throwing exceptions.

        The allowed types of keys in the `inputs` dictionary are:

        (1) `int`
        (2) `str`
        (3) `openvino.runtime.ConstOutput`

        The allowed types of values in the `inputs` are:

        (1) `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
        (2) `openvino.runtime.Tensor`

        Can be called with only one `openvino.runtime.Tensor` or `numpy.ndarray`,
        it will work only with one-input models. When model has more inputs,
        function throws error.

        :param inputs: Data to be set on input tensors.
        :type inputs: Any, optional
        :param share_inputs: Enables `share_inputs` mode. Controls memory usage on inference's inputs.

                              If set to `False` inputs the data dispatcher will safely copy data
                              to existing Tensors (including up- or down-casting according to data type,
                              resizing of the input Tensor). Keeps Tensor inputs "as-is".

                              If set to `True` the data dispatcher tries to provide "zero-copy"
                              Tensors for every input in form of:
                              * `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
                              Data that is going to be copied:
                              * `numpy.ndarray` which are not C contiguous and/or not writable (WRITEABLE flag is set to False)
                              * inputs which data types are mismatched from Infer Request's inputs
                              * inputs that should be in `BF16` data type
                              * scalar inputs (i.e. `np.float_`/`int`/`float`)
                              Keeps Tensor inputs "as-is".

                              Note: Use with extra care, shared data can be modified during runtime!
                              Note: Using `share_inputs` may result in extra memory overhead.

                              Default value: False
        :type share_inputs: bool, optional
        :param share_outputs: Enables `share_outputs` mode. Controls memory usage on inference's outputs.

                              If set to `False` outputs will safely copy data to numpy arrays.

                              If set to `True` the data will be returned in form of views of output Tensors.
                              This mode still returns the data in format of numpy arrays but lifetime of the data
                              is connected to OpenVINO objects.

                              Note: Use with extra care, shared data can be modified or lost during runtime!

                              Default value: False
        :type share_outputs: bool, optional
        :param shared_memory: Deprecated. Works like `share_inputs` mode.

                              If not specified, function uses `share_inputs` value.

                              Note: Will be removed in 2024.0 release!
                              Note: This is keyword-only argument.

                              Default value: None
        :type shared_memory: bool, optional
        :return: Dictionary of results from output tensors with port/int/str keys.
        :rtype: OVDict
        """
        return OVDict(super().infer(_data_dispatch(
            self,
            inputs,
            is_shared=_deprecated_memory_arg(shared_memory, share_inputs),
        ), share_outputs=share_outputs))

    def start_async(
        self,
        inputs: Any = None,
        userdata: Any = None,
        share_inputs: bool = False,
        *,
        shared_memory: Any = None,
    ) -> None:
        """Starts inference of specified input(s) in asynchronous mode.

        Returns immediately. Inference starts also immediately.
        Calling any method on the `InferRequest` object while the request is running
        will lead to throwing exceptions.

        The allowed types of keys in the `inputs` dictionary are:

        (1) `int`
        (2) `str`
        (3) `openvino.runtime.ConstOutput`

        The allowed types of values in the `inputs` are:

        (1) `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
        (2) `openvino.runtime.Tensor`

        Can be called with only one `openvino.runtime.Tensor` or `numpy.ndarray`,
        it will work only with one-input models. When model has more inputs,
        function throws error.

        :param inputs: Data to be set on input tensors.
        :type inputs: Any, optional
        :param userdata: Any data that will be passed inside the callback.
        :type userdata: Any
        :param share_inputs: Enables `share_inputs` mode. Controls memory usage on inference's inputs.

                              If set to `False` inputs the data dispatcher will safely copy data
                              to existing Tensors (including up- or down-casting according to data type,
                              resizing of the input Tensor). Keeps Tensor inputs "as-is".

                              If set to `True` the data dispatcher tries to provide "zero-copy"
                              Tensors for every input in form of:
                              * `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
                              Data that is going to be copied:
                              * `numpy.ndarray` which are not C contiguous and/or not writable (WRITEABLE flag is set to False)
                              * inputs which data types are mismatched from Infer Request's inputs
                              * inputs that should be in `BF16` data type
                              * scalar inputs (i.e. `np.float_`/`int`/`float`)
                              Keeps Tensor inputs "as-is".

                              Note: Use with extra care, shared data can be modified during runtime!
                              Note: Using `share_inputs` may result in extra memory overhead.

                              Default value: False
        :type share_inputs: bool, optional
        :param shared_memory: Deprecated. Works like `share_inputs` mode.

                              If not specified, function uses `share_inputs` value.

                              Note: Will be removed in 2024.0 release!
                              Note: This is keyword-only argument.

                              Default value: None
        :type shared_memory: bool, optional
        """
        super().start_async(
            _data_dispatch(
                self,
                inputs,
                is_shared=_deprecated_memory_arg(shared_memory, share_inputs),
            ),
            userdata,
        )

    def get_compiled_model(self) -> "CompiledModel":
        """Gets the compiled model this InferRequest is using.

        :return: a CompiledModel object
        :rtype: openvino.runtime.ie_api.CompiledModel
        """
        return CompiledModel(super().get_compiled_model())

    @property
    def results(self) -> OVDict:
        """Gets all outputs tensors of this InferRequest.

        :return: Dictionary of results from output tensors with ports as keys.
        :rtype: Dict[openvino.runtime.ConstOutput, numpy.array]
        """
        return OVDict(super().results)


class CompiledModel(CompiledModelBase):
    """CompiledModel class.

    CompiledModel represents Model that is compiled for a specific device by applying
    multiple optimization transformations, then mapping to compute kernels.
    """

    def __init__(self, other: CompiledModelBase) -> None:
        # Private memeber to store already created InferRequest
        self._infer_request: Optional[InferRequest] = None
        super().__init__(other)

    def get_runtime_model(self) -> Model:
        return Model(super().get_runtime_model())

    def create_infer_request(self) -> InferRequest:
        """Creates an inference request object used to infer the compiled model.

        The created request has allocated input and output tensors.

        :return: New InferRequest object.
        :rtype: openvino.runtime.InferRequest
        """
        return InferRequest(super().create_infer_request())

    def infer_new_request(self, inputs: Union[dict, list, tuple, Tensor, np.ndarray] = None) -> OVDict:
        """Infers specified input(s) in synchronous mode.

        Blocks all methods of CompiledModel while request is running.

        Method creates new temporary InferRequest and run inference on it.
        It is advised to use a dedicated InferRequest class for performance,
        optimizing workflows, and creating advanced pipelines.

        The allowed types of keys in the `inputs` dictionary are:

        (1) `int`
        (2) `str`
        (3) `openvino.runtime.ConstOutput`

        The allowed types of values in the `inputs` are:

        (1) `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
        (2) `openvino.runtime.Tensor`

        Can be called with only one `openvino.runtime.Tensor` or `numpy.ndarray`,
        it will work only with one-input models. When model has more inputs,
        function throws error.

        :param inputs: Data to be set on input tensors.
        :type inputs: Union[Dict[keys, values], List[values], Tuple[values], Tensor, numpy.ndarray], optional
        :return: Dictionary of results from output tensors with port/int/str keys.
        :rtype: OVDict
        """
        # It returns wrapped python InferReqeust and then call upon
        # overloaded functions of InferRequest class
        return self.create_infer_request().infer(inputs)

    def __call__(
        self,
        inputs: Union[dict, list, tuple, Tensor, np.ndarray] = None,
        share_inputs: bool = True,
        share_outputs: bool = False,
        *,
        shared_memory: Any = None,
    ) -> OVDict:
        """Callable infer wrapper for CompiledModel.

        Infers specified input(s) in synchronous mode.

        Blocks all methods of CompiledModel while request is running.

        Method creates new temporary InferRequest and run inference on it.
        It is advised to use a dedicated InferRequest class for performance,
        optimizing workflows, and creating advanced pipelines.

        This method stores created `InferRequest` inside `CompiledModel` object,
        which can be later reused in consecutive calls.

        The allowed types of keys in the `inputs` dictionary are:

        (1) `int`
        (2) `str`
        (3) `openvino.runtime.ConstOutput`

        The allowed types of values in the `inputs` are:

        (1) `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
        (2) `openvino.runtime.Tensor`

        Can be called with only one `openvino.runtime.Tensor` or `numpy.ndarray`,
        it will work only with one-input models. When model has more inputs,
        function throws error.

        :param inputs: Data to be set on input tensors.
        :type inputs: Union[Dict[keys, values], List[values], Tuple[values], Tensor, numpy.ndarray], optional
        :param share_inputs: Enables `share_inputs` mode. Controls memory usage on inference's inputs.

                              If set to `False` inputs the data dispatcher will safely copy data
                              to existing Tensors (including up- or down-casting according to data type,
                              resizing of the input Tensor). Keeps Tensor inputs "as-is".

                              If set to `True` the data dispatcher tries to provide "zero-copy"
                              Tensors for every input in form of:
                              * `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
                              Data that is going to be copied:
                              * `numpy.ndarray` which are not C contiguous and/or not writable (WRITEABLE flag is set to False)
                              * inputs which data types are mismatched from Infer Request's inputs
                              * inputs that should be in `BF16` data type
                              * scalar inputs (i.e. `np.float_`/`int`/`float`)
                              Keeps Tensor inputs "as-is".

                              Note: Use with extra care, shared data can be modified during runtime!
                              Note: Using `share_inputs` may result in extra memory overhead.

                              Default value: True
        :type share_inputs: bool, optional
        :param share_outputs: Enables `share_outputs` mode. Controls memory usage on inference's outputs.

                              If set to `False` outputs will safely copy data to numpy arrays.

                              If set to `True` the data will be returned in form of views of output Tensors.
                              This mode still returns the data in format of numpy arrays but lifetime of the data
                              is connected to OpenVINO objects.

                              Note: Use with extra care, shared data can be modified or lost during runtime!

                              Default value: False
        :type share_outputs: bool, optional
        :param shared_memory: Deprecated. Works like `share_inputs` mode.

                              If not specified, function uses `share_inputs` value.

                              Note: Will be removed in 2024.0 release!
                              Note: This is keyword-only argument.

                              Default value: None
        :type shared_memory: bool, optional
        :return: Dictionary of results from output tensors with port/int/str as keys.
        :rtype: OVDict
        """
        if self._infer_request is None:
            self._infer_request = self.create_infer_request()

        return self._infer_request.infer(
            inputs,
            share_inputs=_deprecated_memory_arg(shared_memory, share_inputs),
            share_outputs=share_outputs,
        )


class AsyncInferQueue(AsyncInferQueueBase):
    """AsyncInferQueue with a pool of asynchronous requests.

    AsyncInferQueue represents a helper that creates a pool of asynchronous
    InferRequests and provides synchronization functions to control flow of
    a simple pipeline.
    """

    def __iter__(self) -> Iterable[InferRequest]:
        """Allows to iterate over AsyncInferQueue.

        Resulting objects are guaranteed to work with read-only methods like getting tensors.
        Any mutating methods (e.g. start_async, set_callback) of a single request
        will put the parent AsyncInferQueue object in an invalid state.

        :return: a generator that yields InferRequests.
        :rtype: Iterable[openvino.runtime.InferRequest]
        """
        return (InferRequest(x) for x in super().__iter__())

    def __getitem__(self, i: int) -> InferRequest:
        """Gets InferRequest from the pool with given i id.

        Resulting object is guaranteed to work with read-only methods like getting tensors.
        Any mutating methods (e.g. start_async, set_callback) of a request
        will put the parent AsyncInferQueue object in an invalid state.

        :param i:  InferRequest id.
        :type i: int
        :return: InferRequests from the pool with given id.
        :rtype: openvino.runtime.InferRequest
        """
        return InferRequest(super().__getitem__(i))

    def start_async(
        self,
        inputs: Any = None,
        userdata: Any = None,
        share_inputs: bool = False,
        *,
        shared_memory: Any = None,
    ) -> None:
        """Run asynchronous inference using the next available InferRequest from the pool.

        The allowed types of keys in the `inputs` dictionary are:

        (1) `int`
        (2) `str`
        (3) `openvino.runtime.ConstOutput`

        The allowed types of values in the `inputs` are:

        (1) `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
        (2) `openvino.runtime.Tensor`

        Can be called with only one `openvino.runtime.Tensor` or `numpy.ndarray`,
        it will work only with one-input models. When model has more inputs,
        function throws error.

        :param inputs: Data to be set on input tensors of the next available InferRequest.
        :type inputs: Any, optional
        :param userdata: Any data that will be passed to a callback.
        :type userdata: Any, optional
        :param share_inputs: Enables `share_inputs` mode. Controls memory usage on inference's inputs.

                              If set to `False` inputs the data dispatcher will safely copy data
                              to existing Tensors (including up- or down-casting according to data type,
                              resizing of the input Tensor). Keeps Tensor inputs "as-is".

                              If set to `True` the data dispatcher tries to provide "zero-copy"
                              Tensors for every input in form of:
                              * `numpy.ndarray` and all the types that are castable to it, e.g. `torch.Tensor`
                              Data that is going to be copied:
                              * `numpy.ndarray` which are not C contiguous and/or not writable (WRITEABLE flag is set to False)
                              * inputs which data types are mismatched from Infer Request's inputs
                              * inputs that should be in `BF16` data type
                              * scalar inputs (i.e. `np.float_`/`int`/`float`)
                              Keeps Tensor inputs "as-is".

                              Note: Use with extra care, shared data can be modified during runtime!
                              Note: Using `share_inputs` may result in extra memory overhead.

                              Default value: False
        :type share_inputs: bool, optional
        :param shared_memory: Deprecated. Works like `share_inputs` mode.

                              If not specified, function uses `share_inputs` value.

                              Note: Will be removed in 2024.0 release!
                              Note: This is keyword-only argument.

                              Default value: None
        :type shared_memory: bool, optional
        """
        super().start_async(
            _data_dispatch(
                self[self.get_idle_request_id()],
                inputs,
                is_shared=_deprecated_memory_arg(shared_memory, share_inputs),
            ),
            userdata,
        )


class Core(CoreBase):
    """Core class represents OpenVINO runtime Core entity.

    User applications can create several Core class instances, but in this
    case, the underlying plugins are created multiple times and not shared
    between several Core instances. The recommended way is to have a single
    Core instance per application.
    """
    def read_model(self, model: Union[str, bytes, object], weights: Union[object, str, bytes, Tensor] = None) -> Model:
        if weights is not None:
            return Model(super().read_model(model, weights))
        else:
            return Model(super().read_model(model))

    def compile_model(
        self,
        model: Union[Model, str, Path],
        device_name: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> CompiledModel:
        """Creates a compiled model.

        Creates a compiled model from a source Model object or
        reads model and creates a compiled model from IR / ONNX / PDPD / TF and TFLite file.
        This can be more efficient than using read_model + compile_model(model_in_memory_object) flow,
        especially for cases when caching is enabled and cached model is available.
        If device_name is not specified, the default OpenVINO device will be selected by AUTO plugin.
        Users can create as many compiled models as they need, and use them simultaneously
        (up to the limitation of the hardware resources).

        :param model: Model acquired from read_model function or a path to a model in IR / ONNX / PDPD /
                      TF and TFLite format.
        :type model: Union[openvino.runtime.Model, str, pathlib.Path]
        :param device_name: Optional. Name of the device to load the model to. If not specified,
                            the default OpenVINO device will be selected by AUTO plugin.
        :type device_name: str
        :param config: Optional dict of pairs:
                       (property name, property value) relevant only for this load operation.
        :type config: dict, optional
        :return: A compiled model.
        :rtype: openvino.runtime.CompiledModel
        """
        if device_name is None:
            return CompiledModel(
                super().compile_model(model, {} if config is None else config),
            )

        return CompiledModel(
            super().compile_model(model, device_name, {} if config is None else config),
        )

    def import_model(
        self,
        model_stream: bytes,
        device_name: str,
        config: Optional[dict] = None,
    ) -> CompiledModel:
        """Imports a compiled model from a previously exported one.

        :param model_stream: Input stream, containing a model previously exported, using export_model method.
        :type model_stream: bytes
        :param device_name: Name of device to which compiled model is imported.
                            Note: if device_name is not used to compile the original model,
                            an exception is thrown.
        :type device_name: str
        :param config: Optional dict of pairs:
                       (property name, property value) relevant only for this load operation.
        :type config: dict, optional
        :return: A compiled model.
        :rtype: openvino.runtime.CompiledModel

        :Example:

        .. code-block:: python

            user_stream = compiled.export_model()

            with open('./my_model', 'wb') as f:
                f.write(user_stream)

            # ...

            new_compiled = core.import_model(user_stream, "CPU")

        .. code-block:: python

            user_stream = io.BytesIO()
            compiled.export_model(user_stream)

            with open('./my_model', 'wb') as f:
                f.write(user_stream.getvalue()) # or read() if seek(0) was applied before

            # ...

            new_compiled = core.import_model(user_stream, "CPU")
        """
        return CompiledModel(
            super().import_model(
                model_stream,
                device_name,
                {} if config is None else config,
            ),
        )


def compile_model(model_path: Union[str, Path]) -> CompiledModel:
    """Compact method to compile model with AUTO plugin.

    :param model_path: Path to file with model.
    :type model_path: str, pathlib.Path
    :return: A compiled model
    :rtype: openvino.runtime.CompiledModel

    """
    core = Core()
    return core.compile_model(model_path, "AUTO")
