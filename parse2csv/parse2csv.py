# coding=utf-8

"""
    parse2csv.parse2csv
    ~~~~~~~~~~~~~~~~~~~

    The main module.

    :copyright: (c) 2018 by Ali Ghaffaari.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import division
from collections import defaultdict
import os
import glob
import csv
import re

import yaml
import parse


class Reduce(object):
    """Supported reduce functions."""
    @staticmethod
    def call(signiture, values):
        """Call the reduce function specified by its signiture on `values`.

        Args:
            signiture : list or str
                Function signiture (usually the entry associated with the field
                under 'reduce' entry in the config file) is a string determining
                the name of the function or a list in which the first element is
                string (mandatory) indicating the function name and the other
                elements are optional specifying the reduce function arguments.
            values : list
                The list of values to be reduced.
        """
        func_name = ''
        args = list()
        if isinstance(signiture, list):
            func_name = signiture[0]
            args = signiture[1:]
        elif isinstance(signiture, str):
            func_name = signiture
        else:
            raise RuntimeError("unknown reduce function signiture")
        func = getattr(Reduce, func_name)
        return func(values, *args)

    @staticmethod
    def first(values):
        """Get the first value."""
        return values[0]

    @staticmethod
    def last(values):
        """Get the last value."""
        return values[-1]

    @staticmethod
    def avg(values):
        """Get average of the values."""
        return sum(values) / len(values)

    @staticmethod
    def avg_tp(values):
        """Get average of the values by preserving its original type."""
        return type(values[0])(sum(values) / len(values))

    @staticmethod
    def count(values):
        """Get the number of values."""
        return len(values)

    @staticmethod
    def min(values):
        """Get the minimum value."""
        return min(values)

    @staticmethod
    def max(values):
        """Get the maximum value."""
        return max(values)

    @staticmethod
    def sum(values):
        """Get the sum of values."""
        return sum(values)

    @staticmethod
    def concat(values):
        """Get concatenation of the values."""
        return ''.join(values)

    @staticmethod
    def filesize(values):
        """Get the file size in bytes."""
        fpath = os.path.realpath(values[0])
        return os.stat(fpath).st_size

    @staticmethod
    def filesize_glob(values):
        """Get cumulative size of the files prefixed by `prefix` in bytes."""
        prefix = values[0] + "*"
        retval = 0
        for fpath in glob.glob(prefix):
            retval += Reduce.filesize([fpath])
        return retval

    @staticmethod
    def parse(values, pattern):
        """Parse concatenation of the values and get the concatenation of the
        matched groups by input regex `pattern`.
        """
        text = ''.join(values)
        return ''.join(re.match(pattern, text).groups())


def process(data, funcs):
    """Process multi-value fields by applying specified reduce function.

    Args:
        data : dict
            The data to be processed.
        funcs : dict
            A dictionary specifying the reduce function for each multi-value
            field. In case that it is not specified for a particular field it
            is assumed to be `Reduce.first` function.
    """
    reducts = defaultdict(lambda: 'first')
    reducts.update(funcs)
    proc_data = dict()
    for key, values in data.items():
        proc_data[key] = Reduce.call(reducts[key], values)
    return proc_data


def parse_all(content, patterns):
    """Extract the fields from the content.

    Args:
        content : str
            The content to be parsed.
        patterns : list of str
            The list of patterns to find.
    """
    data = defaultdict(list)
    for pat in patterns:
        for match in parse.findall(pat, content):
            for key, value in match.named.items():
                data[key].append(value)
    return data


def list_dialects():
    """Get list of supported CSV dialects."""
    return csv.list_dialects()


def default_dialect():
    """Get default CSV dialects."""
    return 'unix'


def generate(output, inputs, configfile, dialect='unix'):
    """Generate CSV file.

    Args:
        output : file-like object
            Output file.
        inputs : list of file-like objects
            Input files to be processed.
        configfile : file-like object
            Input configuration file.
        dialect : str
            This string specifies the dialect of the output CSV file.
    """
    config = yaml.load(configfile)
    writer = csv.DictWriter(output,
                            fieldnames=config['fields'],
                            restval=config.get('missing_value', 'NA'),
                            extrasaction='ignore',
                            dialect=dialect,
                            quoting=csv.QUOTE_NONE)
    writer.writeheader()
    for inp in inputs:
        data = parse_all(inp.read(), config['patterns'])
        proc_data = process(data, config.get('reduce', {}))
        writer.writerow(proc_data)
