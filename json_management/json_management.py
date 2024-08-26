#!/bin/env python3

__all__= ()

import os
import re
import asyncio
from . import logger
import ujson as json
from typing import (Any,
                    Optional,)

def _json_format(chat_id: int) -> str:
    file_name = str(chat_id)
    if not file_name.endswith('.json'):
        return file_name + '.json'
    return file_name


class JsonManager:
    '''
    :param main_dir: The main directory to write ``json files``.
    :type main_dir: :obj:`str` or :obj:`None`
    :param base_dict: The base dict for ``json files``.
    :type base_dict: :obj:`dict` or :obj:`None`
    :param debug: Pass :obj:`True` to see more information in ``STDOUT``.
    :type debug: :obj:`bool`, optional
    '''
    def __init__(
        self,
        main_dir: Optional[str],
        base_dict: dict[str, Any],
        debug: Optional[bool] = None
    ):
        if not isinstance(main_dir, (str, type(None))):
            raise TypeError(
                "'main_dir' must be str, pass None"
                ' to use the current directory.'
            )
        if main_dir is not None and not os.path.isdir(main_dir):
            raise NotADirectoryError(
                "'main_dir' is not a directory, pass"
                ' None to use the current one.'
            )
        if not isinstance(base_dict, dict):
            raise TypeError(
                "'base_dict' must be dict,"
                f' got {base_dict.__class__.__name__}.'
            )

        if main_dir is None: main_dir = './'
        elif not main_dir.endswith('/'): main_dir += '/'

        self._main_dir = main_dir
        self._updates = {}

        self._base_dict = base_dict

        self._debug = debug

        if debug:
            logger.setLevel(10)

    @property
    def main_dir(self) -> str:
        return self._main_dir

    @property
    def updates(self) -> dict[int, dict[str, Any]]:
        return self._updates

    @property
    def base_dict(self) -> dict[str, Any]:
        return self._base_dict.copy()


    def get(self, chat_id: int, /) -> dict[str, Any]:
        '''
        Method to :meth:`~ujson_manager.JsonManager.get` a dict from the
        ``chat_id.json`` file or from the ``self.updates``.

        Usage:

        .. code-block:: python3

            from ujson_manager import JsonManager
            tracker = JsonManager('<your_usr_dir>', base_dict=None)
            data = tracker.get(0123456789)

        :param chat_id: A `Telegram <https://core.telegram.org/bots/api>`_ chat_id.
        :type chat_id: :obj:`int`
        :rtype: :obj:`dict[str, Any]`
        '''
        if type(chat_id) is not int:
            raise TypeError(
                "'chat_id' must be int in JsonManager.get()"
                f" method, got {chat_id.__class__.__name__}."
            )
        if chat_id in self.updates:
            if self._debug:
                logger.debug(f'Got {chat_id} from updates.')
        else:
            file_name = _json_format(chat_id)
            try:
                with open(self.main_dir + file_name) as r:
                    self.updates[chat_id] = json.loads(r.read())
            except FileNotFoundError:
                raise FileNotFoundError(
                    f'No such file {self.main_dir + file_name!r}.'
                    ' You should use the JsonManager.check() method'
                    ' before to call the JsonManager.get() to ensure the file exists.'
                )
            if self._debug:
                logger.debug(f'Got {chat_id} from file.')

        return self.updates[chat_id]


    def check(self, chat_id: int, /) -> dict[str, Any]:
        '''
        Useful for the :obj:`~aiotgm.Client`, to ensure
        that the json ``keys`` are *ok* in a ``json file``
        before to call the :meth:`~ujson_manager.JsonManager.get`.

        Usage:

        .. code-block:: python3

            from ujson_manager import JsonManager
            tracker = JsonManager('<your_usr_dir>', base_dict=None)
            data = tracker.check(0123456789)

        :param chat_id: A `Telegram <https://core.telegram.org/bots/api>`_ chat_id.
        :type chat_id: :obj:`int`
        :rtype: :obj:`dict[str, Any]`
        '''
        file_name = _json_format(chat_id)

        if (
            chat_id in self.updates
            or os.path.isfile(self.main_dir + file_name)
        ):
            result = {}
            actual_dict = self.get(chat_id)

            for key in self.base_dict:

                if key in actual_dict:
                    val = actual_dict[key]
                else:
                    val = self.base_dict[key]

                result[key] = val
        else:
            result = self.base_dict

        self.updates[chat_id] = result

        return self.updates[chat_id]


    def merge(self) -> dict[int, dict[str, Any]]:
        '''
        Useful for the :obj:`~aiotgm.Client` to merge all the ``json files`` in the
        :obj:`~ujson_manager.JsonManager.updates` dict, ``non-integer`` pattern filenames will be skipped.

        Usage:

        .. code-block:: python3

            from ujson_manager import JsonManager
            tracker = JsonManager('<your_usr_dir>', base_dict=None)
            users = tracker.merge()

        :rtype: :obj:`dict[int, dict[str, Any]]`
        '''
        for file_name in os.listdir(self.main_dir):

            if re.match(r'^(\-|\d){0,1}\d+\.json$', file_name):
                chat_id = file_name.replace('.json', str())
                self.get(int(chat_id))
            else:
                logger.warning(
                    f'Unexpected file {self.main_dir + file_name!r}'
                    ' in the JsonManager.merge() method, it was skipped.'
                )
        return self.updates


    def push_updates(self) -> int:
        '''
        You need to call this method ``explicitly``, to write
        the :obj:`~ujson_manager.JsonManager.updates` to the
        ``json files``. Used in the method :meth:`~ujson_manager.JsonManager.process_updates`.

        :rtype: :obj:`int`
        '''
        ok = 0
        for chat_id in self.updates:
            file_name = _json_format(chat_id)
            if self._debug:
                logger.debug(f'Pushing {chat_id!r} {self.updates[chat_id]!r}')

            with open(self.main_dir + file_name, 'w') as w:
                w.write(json.dumps(self.updates[chat_id], indent = 2))
                ok += 1

        return ok


    async def process_updates(self, delay: float = 15, /) -> None:
        '''
        Coroutine to ``process`` the :obj:`~ujson_manager.JsonManager.updates`
        and ``write`` them to the ``json files`` every *delay* time.

        Usage:

        .. code-block:: python3

            import asyncio
            from ujson_manager import JsonManager
            tracker = JsonManager('<your_usr_dir>', base_dict=None)

            asyncio.run(tracker.process_updates(30))

        :param delay: A time in seconds how often to write the ``json files``.
        :type delay: :obj:`float`
        :rtype: :obj:`None`
        '''
        try:
            while True:
                if self.updates:
                    self.push_updates()
                await asyncio.sleep(delay)
        except:
            pushed = self.push_updates()
            s = str() if pushed == 1 else 's'
            were = 'was' if pushed == 1 else 'were'
            logger.info(
                f'{pushed} json file{s} {were} saved.'
            )
            raise
