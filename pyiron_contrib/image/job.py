from __future__ import print_function
# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from pyiron.base.job.generic import GenericJob
import numpy as np
import skimage as ski
from skimage import io, filters, exposure
import matplotlib.pyplot as plt
import inspect
from pyiron_contrib.image.utils import ModuleScraper

"""
Store and process image data within the pyiron framework. Functionality of the `skimage` library is automatically 
scraped, along with some convenience decorators to switch their function-based library to a class-method-based library.
"""

__author__ = "Liam Huber"
__copyright__ = "Copyright 2019, Max-Planck-Institut für Eisenforschung GmbH " \
                "- Computational Materials Design (CM) Department"
__version__ = "0.0"
__maintainer__ = "Liam Huber"
__email__ = "huber@mpie.de"
__status__ = "development"
__date__ = "Jan 30, 2020"

# Some decorators look at the signature of skimage methods to see if they take an image
# (presumed to be in numpy.ndarray format).
# This is done by searching the signature for the variable name below:
_IMAGE_VARIABLE = 'image'


class Images(GenericJob):
    pass


def pass_image_data(image):
    """
    Decorator to see if the signature of the function starts with a particular variable (`_IMAGE_VARIABLE`). If so,
    automatically passes an attribute of the argument (`image.data`) as the first argument.

    Args:
        image (Image): The image whose data to use.

    Returns:
        (fnc): Decorated function.
    """
    def decorator(function):
        takes_image_data = list(inspect.signature(function).parameters.keys())[0] == _IMAGE_VARIABLE

        def wrapper(*args, **kwargs):
            if takes_image_data:
                return function(image.data, *args, **kwargs)
            else:
                return function(*args, **kwargs)

        wrapper.__doc__ = ""
        if takes_image_data:
            wrapper.__doc__ += "This function has been wrapped to automatically supply the image argument. \n" \
                               "Remaining arguments can be passed as normal.\n"
        wrapper.__doc__ += "The original docstring follows:\n\n"
        wrapper.__doc__ += function.__doc__ or ""
        return wrapper

    return decorator


def set_image_data(image):
    """
    Decorator which checks the returned value of the function. If that value is of type `numpy.ndarray`, uses it to set
    an attribute of the argument (`image.data`) instead of returning it.

    Args:
        image (Image): The image whose data to set.

    Returns:
        (fnc): Decorated function.
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            output = function(*args, **kwargs)
            if isinstance(output, np.ndarray):
                image._data = output
            else:
                return output

        wrapper.__doc__ = "This function has been wrapped; if it outputs a numpy array, it will be " \
                          "automatically passed to the image's data field.\n" + function.__doc__
        return wrapper

    return decorator


def pass_and_set_image_data(image):
    """
    Decorator which connects function input and output to `image.data`.

    Args:
        image (Image): The image whose data to set.

    Returns:
        (fnc): Decorated function.
    """
    def decorator(function):
        return set_image_data(image)(pass_image_data(image)(function))
    return decorator


class Image:
    """
    A base class for storing image data in the form of numpy arrays. Functionality of the skimage library can be
    leveraged using the sub-module name and an `activate` method.
    """

    def __init__(self, source=None, metadata=None, as_grey=False):
        # Set data
        self._source = source
        self._data = None
        self.as_grey = as_grey

        # Set metadata
        self.metadata = metadata  # TODO

        # Apply wrappers
        # TODO:
        #  Set up some sort of metaclass so that the scraping and wrapping is done at import. It will be too expensive
        #  to do this every time we instantiate...
        for module_name in [
            'filters',
            'exposure'
        ]:
            # setattr(
            #     self,
            #     module_name,
            #     self._ModuleScraper(self, getattr(ski, module_name))
            # )
            setattr(
                self,
                module_name,
                ModuleScraper(
                    'skimage.' + module_name,
                    decorator=pass_and_set_image_data,
                    decorator_args=(self,)
                )
            )

    @property
    def source(self):
        return self._source

    def overwrite_source(self, new_source, new_metadata=None, as_grey=False):
        self._source = new_source
        self._data = None
        self.as_grey = as_grey
        self.metadata = new_metadata

    @property
    def data(self):
        if self._data is None:
            self._load_data_from_source()
        return self._data

    def _load_data_from_source(self):
        if isinstance(self.source, np.ndarray):
            self._data = self.source.copy()
        elif isinstance(self.source, str):
            self._data = ski.io.imread(self.source, as_grey=self.as_grey)
        else:
            raise ValueError("Data source not understood, should be numpy.ndarray or string pointing to image file.")

    def reload_data(self):
        """
        Reverts the `data` attribute to the source, i.e. the most recently read file (if set by reading data), or the
        originally assigned array (if set by direct array assignment).
        """
        self._load_data_from_source()

    def convert_to_greyscale(self):
        if self._data is not None:
            if len(self.data.shape) == 3 and self.data.shape[-1] == 3:
                self._data = np.mean(self._data, axis=-1)
                self.as_grey = True
            else:
                raise ValueError("Can only convert data with shape NxMx3 to greyscale")
        else:
            self.as_grey = True

    def imshow(self, subplots_kwargs=None, ax_kwargs=None):
        subplots_kwargs = subplots_kwargs or {}
        ax_kwargs = ax_kwargs or {}
        fig, ax = plt.subplots(**subplots_kwargs)
        ax.imshow(self.data, **ax_kwargs)
        return fig, ax


class Metadata:
    def __init__(self, data=None, note=None):
        self._data = data
        self.note = note

    @property
    def shape(self):
        return self._data.shape