# -*- coding: utf-8 -*-

import os.path
from collections.abc import Iterable, Sequence
from numbers import Number

import regex as re
import yaml

#####################
# Config Management #
#####################

DEFAULT_PROFILE = 'default'

class Config:
    """Manages YAML config information, features include:
      - Loading from multiple config files
      - Caching of aggregated config file parameters
      - Named "profiles" to override 'default' profile parameters

    Config file structure:
    ---
    default:
      my_section:
        my_param: value

    alt_profile:
      my_section:
        my_param: alt_value  # overwrites value from 'default' profile
    """
    config_dir:   str | None
    filepaths:    list[str]        # list of file pathnames loaded
    profile_data: dict[str, dict]  # config indexed by profile (including 'default')

    def __init__(self, files: str | Iterable[str], config_dir: str = None):
        """Note that `files` can be specified as an iterable, or a comma-separated
        list of file names (no spaces)
        """
        if isinstance(files, str):
            load_files = files.split(',')
        else:
            if not isinstance(files, Iterable):
                raise RuntimeError("Bad argument, 'files' not iterable")
            load_files = list(files)

        self.config_dir = config_dir
        self.filepaths = []
        self.profile_data = {}
        for file in load_files:
            self.load(file)

    def load(self, file: str) -> bool:
        """Load a config file, overwriting existing parameter entries at the section
        level (i.e. direct children within a section).  Deeper merging within these
        top-level parameters is not supported.  Note that additional config files
        can be loaded at any time.  A config file that has already been loaded will
        be politely skipped, with a `False` return value being the only rebuke.
        """
        path = os.path.join(self.config_dir, file) if self.config_dir else os.path.realpath(file)
        if path in self.filepaths:
            return False

        with open(path, 'r') as f:
            cfg = yaml.safe_load(f)
            if not cfg:  # could be bad YAML or empty config
                raise RuntimeError(f"Could not load from '{file}'")

        for profile in cfg:
            if profile not in self.profile_data:
                self.profile_data[profile] = {}
            for section in cfg[profile]:
                if section not in self.profile_data[profile]:
                    self.profile_data[profile][section] = {}
                self.profile_data[profile][section].update(cfg[profile][section])

        self.filepaths.append(path)
        return True

    def config(self, section: str, profile: str = None) -> dict:
        """Get parameters for configuration section (empty dict is returned if
        section is not found).  If `profile` is specified, the parameter values
        for that profile override values from the 'default' profile (which must
        exist).
        """
        if DEFAULT_PROFILE not in self.profile_data:
            raise RuntimeError(f"Default profile ('{DEFAULT_PROFILE}') never loaded")
        default_data = self.profile_data[DEFAULT_PROFILE]
        ret_params  = default_data.get(section, {})
        if profile:
            if profile not in self.profile_data:
                raise RuntimeError(f"Profile '{profile}' never loaded")
            profile_data = self.profile_data[profile]
            profile_params = profile_data.get(section, {})
            ret_params.update(profile_params)
        return ret_params

########
# Misc #
########

def rankdata(a: Sequence[Number], method: str = 'average', reverse: bool = True) -> list[Number]:
    """Standalone implementation of scipy.stats.rankdata, adapted from
    https://stackoverflow.com/a/3071441, with the following added:
      - `method` arg, with support for 'average' (default) and 'min'
      - `reverse` flag, with `True` (default) signifying descending sort order
        (i.e. the highest value in `a` has a rank of 1, as opposed to `len(a)`)
    Note that return rankings with be type `float` for method='average' and
    `int` for method='min'.
    """
    def rank_simple(vector):
        return sorted(range(len(vector)), key=vector.__getitem__, reverse=reverse)

    use_min  = method == 'min'
    n        = len(a)
    ivec     = rank_simple(a)
    svec     = [a[rank] for rank in ivec]
    sumranks = 0
    dupcount = 0
    minrank  = 0
    newarray = [0] * n
    for i in range(n):
        sumranks += i
        dupcount += 1
        minrank = minrank or i + 1
        if i == n - 1 or svec[i] != svec[i + 1]:
            averank = sumranks / float(dupcount) + 1
            for j in range(i - dupcount + 1, i + 1):
                newarray[ivec[j]] = minrank if use_min else averank
            sumranks = 0
            dupcount = 0
            minrank  = 0
    return newarray

def parse_argv(argv: list[str]) -> tuple[list, dict]:
    """Takes a list of arguments (typically a slice of `sys.argv`), which may be a
    combination of bare agruments or kwargs-style constructions (e.g. "key=value"),
    and returns a tuple of `args` and `kwargs`.  For both `args` and `kwargs`, we
    attempt to cast the value to the proper type (e.g. int, float, bool, or None).
    """
    def typecast(val: str) -> str | Number | bool | None:
        if val.isdecimal():
            return int(val)
        if val.isnumeric():
            return float(val)
        if val.lower() in ['false', 'f', 'no', 'n']:
            return False
        if val.lower() in ['true', 't', 'yes', 'y']:
            return True
        if val.lower() in ['null', 'none', 'nil']:
            return None
        return val if len(val) > 0 else None

    args = []
    kwargs = {}
    args_done = False
    for arg in argv:
        if not args_done:
            if '=' not in arg:
                args.append(typecast(arg))
                continue
            else:
                args_done = True
        kw, val = arg.split('=', 1)
        kwargs[kw] = typecast(val)

    return args, kwargs

def replace_tokens(fmt: str, **kwargs) -> str:
    """Replace tokens in format string with values passed in as keyword args.

    Tokens in format string are represented by "<TOKEN_STR>" (all uppercase), and
    are replaced in output string with corresponding lowercase entries in `kwargs`.

    :param fmt: format string with one or more tokens
    :param kwargs: possible token replacement values
    :return: string with token replacements
    """
    new_str = fmt
    tokens = re.findall(r'(\<[\p{Lu}\d_]+\>)', fmt)
    for token in tokens:
        token_var = token[1:-1].lower()
        value = kwargs.get(token_var)
        if not value:
            raise RuntimeError(f"Token '{token_var}' not found in {kwargs}")
        new_str = new_str.replace(token, value)
    return new_str
