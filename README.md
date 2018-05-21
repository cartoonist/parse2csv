parse2csv
=========
parse2csv is a command-line tool to parse multiple files for named patterns in
order to extract structured data from each file and then write the values in CSV
format. For each input file, there would be a row in the generated CSV file
containing the field values extracted from that file. The CSV header would be
the names specified for each pattern.


The main motivation for writing this script is parsing the output of other tools
and extract required information and put them in a CSV file for further analysis.

Installation
------------
Using `pip`:

    pip install parse2csv

Using setup script:

    python setup.py install

Usage
-----
The first step is preparing a configuration file. The config file should be in
YAML format specifying the patterns for which the input files should be searched.

The patterns can be specified in the config file under `patterns` entry as a
list. parse2csv uses [parse](https://github.com/r1chardj0n3s/parse) package to
extract data. Therefore, all patterns should comply with its format syntax (see
[format syntax](https://github.com/r1chardj0n3s/parse#format-syntax)). Since the
output file is in CSV format, all fields in the patterns should be **named**;
otherwise it cannot be determined which parsed value belongs to which column in
the CSV file.

Apart from patterns, the order of the fields by which they should appear in the
CSV file should also be specified in the config file under `fields` entry. All
field names must be the same as the name used in the patterns. The `fields`
entry does not require to include all named fields in the patterns list.

The entry `missing_value` in the config file indicates the value to be used in
the output CSV in case a field cannot be found in the context. The default value
is 'NA' in case it is not provided in the config file.

Here, is a sample config file:

```yaml
---
missing_value: '-'
fields:
  - 'date'
  - 'first'
  - 'last'
  - 'address'
  - 'age'
patterns:
  - 'Date: {date:tg}'
  - 'Age: {age:d}'
  - 'Name: {first:w}{:s}{last:w}'
  - 'Name: {last:w},{:s}{first:w}'
  - 'Address: "{address}"'
...
```

Assume, there are two files:

    $ cat file1
    Date: 1/2/2011 11:00 PM
    Name: Sherlock Holmes
    Age: 38
    Address: "221B Baker Street"

    $ cat file2
    Date: 6/1/2018 12:00 AM
    Age: 42
    Name: Watson, John

The output CSV file would be:

    date,first,last,age
    2011-02-01 23:00:00,Sherlock,Holmes,221B Baker Street,38
    2018-01-06 12:00:00,John,Watson,-,42

In some cases, a field can be occurred multiple times in the context. These
values can be reduced to one by specifying the reduce function in the config
file under `reduce` entry as a mapping between field name and reduce function:

    reduce:
      income: 'avg'
      children: 'count'

The above example maps the `avg` and `count` functions to 'income' and 'children'
fields, respectively. In case, the income occurs more than once in the context,
the average of them will be reported and for 'children' the number of the
occurrences will be put in the generated CSV file.

The reduce functions can be one of these:
- `'first'`: use the first value.
- `'last'`: use the last value.
- `'avg'`: use the average of values (the values should be numerical).
- `'avg_tp'`: the same as `'avg'` but preserves the original type (the values
              should be numerical).
- `'count'`: use the count of occurrences.
- `'min'`: use the minimum value.
- `'max'`: use the maximum value.
- `'sum'`: use the sum of values.
- `'concat'`: use the concatenation of the values (field should be `str`).

Once the configuration file is ready, using parse2csv is quite straightforward
by providing the input and configuration files:

    parse2csv -c config.yaml -o output.csv file1 file2...

The flag `--help` reveals more details about program usage:

    $ python parse2csv.py --help
    Usage: parse2csv.py [OPTIONS] [INPUTS]...

      Parse the input files for named patterns and dump their values to a file
      in CSV format.

    Options:
      -o, --output FILENAME           Write to this file instead of stdout.
      -c, --configfile FILENAME       Use this configuration file.  [required]
      -d, --dialect [unix|excel|excel-tab]
                                      Use this CSV dialect.  [default: unix]
      --help                          Show this message and exit.
