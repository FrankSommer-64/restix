#!/usr/bin/python3

import base64
import binascii
import json
import os
import shutil
import sys
from typing import NoReturn


def error_exit(reason: str) -> NoReturn:
    _result = { 'error': {'reason': reason}, 'status': 'FAILED'}
    print(base64.b64encode(json.dumps(_result).encode('utf-8')))
    sys.exit(2)


def parse_argument(command_line_arg: str) -> dict:
    # noinspection PyBroadException
    try:
        _arg = json.loads(base64.b64decode(command_line_arg))
        if not isinstance(_arg, dict):
            error_exit('run_restix_cli_test requires dictionary as argument')
        print(_arg)
        return _arg
    except Exception:
        error_exit('run_restix_cli_test could not decode argument')

if len(sys.argv) != 2:
    error_exit('run_restix_cli_test needs exactly one argument')
parse_argument(sys.argv[1])