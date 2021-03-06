# Copyright 2017 ZTE Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def ignore_case_get(args, key, def_val=""):
    if not key:
        return def_val
    if key in args:
        return args[key]
    for old_key in args:
        if old_key.upper() == key.upper():
            return args[old_key]
    return def_val


def set_opt_val(param, key, val):
    if val or val is False:
        param[key] = val


def get_none(val, def_val=""):
    return val if val else def_val


def get_boolean(val, def_val=0):
    return 1 if val else 0


def get_integer(val, def_val=0):
    return val if val else 0
