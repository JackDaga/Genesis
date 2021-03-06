from asyncpg import Record
from math import ceil, floor
from aiohttp.web import View
from datetime import datetime
from typing import Union, List, Dict
from aiohttp_jinja2 import template as jinja2_template

from utils.auth import get_auth_data, NotAuthenticated
from utils.map import parse_data_key


def view(template: str, *, pass_user: bool = True, encoding: str = 'utf-8', status_code: int = 200):
    def wrapper(func):
        _view_template = template

        if '.' in template:
            _view_template = _view_template.replace('.', '/')

        if template[-5:] != '.html':
            _view_template = _view_template + '.html'

        @jinja2_template(_view_template, encoding=encoding, status=status_code)
        async def _view(_self: View):
            _context = dict()

            if pass_user:
                # We're in a view class
                request = _self.request

                try:
                    user = await get_auth_data(request)
                except NotAuthenticated:
                    user = {}

                _context['user'] = user
                _context.update(await func(_self, user))
            else:
                _context.update(await func(_self))

            return _context

        return _view

    return wrapper


def humanize_datetime(dt: datetime, with_time: bool = True, long: bool = True) -> str:
    args = list(map(lambda x: str(x), (dt.day, parse_data_key(dt.month, 'months'), dt.year)))

    if long:
        datetime_str = '{0} de {1} del {2}'
    else:
        datetime_str = '{0}/{1}/{2}'

    if with_time:
        args.append(dt.strftime("%I:%M %p"))
        datetime_str += ' {3}'

    return datetime_str.format(*args)


def flatten(data: Union[List, Dict, Record], time_config: dict) -> Union[List, Dict]:
    if isinstance(data, (dict, Record)):
        _data = {}

        for k, v in data.items():
            if isinstance(v, datetime):
                _data[k] = humanize_datetime(v, **time_config)
            elif isinstance(v, (Record, dict, list)):
                _data[k] = flatten(v, time_config)
            else:
                _data[k] = v

        return _data
    elif isinstance(data, list):
        _data = []

        for e in data:
            if isinstance(e, datetime):
                _data.append(humanize_datetime(e, **time_config))
            elif isinstance(e, (Record, dict, list)):
                _data.append(flatten(e, time_config))
            else:
                _data.append(e)
    else:
        raise ValueError('Solo se soporta dict y list')

    return _data
