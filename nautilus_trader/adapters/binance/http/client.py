# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2021 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  Heavily refactored from MIT licensed github.com/binance/binance-connector-python
#  Original author: Jeremy https://github.com/2pd
# -------------------------------------------------------------------------------------------------

import asyncio
import hashlib
import hmac
from typing import Dict

from aiohttp import ClientResponse
from aiohttp import ClientResponseError

import nautilus_trader
from nautilus_trader.adapters.binance.http.error import BinanceClientError
from nautilus_trader.adapters.binance.http.error import BinanceServerError
from nautilus_trader.adapters.binance.http.parsing import clean_none_value
from nautilus_trader.adapters.binance.http.parsing import encoded_string
from nautilus_trader.common.clock import LiveClock
from nautilus_trader.common.logging import Logger
from nautilus_trader.network.http import HTTPClient


NAUTILUS_VERSION = nautilus_trader.__version__


class BinanceHTTPClient(HTTPClient):
    """
    Provides a `Binance` asynchronous HTTP client
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        clock: LiveClock,
        logger: Logger,
        key=None,
        secret=None,
        base_url=None,
        timeout=None,
        show_limit_usage=False,
    ):
        super().__init__(
            loop=loop,
            logger=logger,
        )
        self._clock = clock
        self._key = key
        self._secret = secret
        self._base_url = base_url
        self._show_limit_usage = show_limit_usage
        self._proxies = None
        self._headers: Dict[str, str] = {
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": "nautilus-trader/" + NAUTILUS_VERSION,
            "X-MBX-APIKEY": key,
        }

        if timeout is not None:
            self._headers["timeout"] = timeout

        # TODO(cs): Implement limit usage

    @property
    def headers(self):
        return self._headers

    async def query(self, url_path, payload=None):
        return await self.send_request("GET", url_path, payload=payload)

    async def limit_request(
        self,
        http_method: str,
        url_path: str,
        payload: Dict[str, str] = None,
    ):
        """
        Limit request is for those endpoints require API key in the header.
        """
        # check_required_parameter(self.key, "apiKey")
        return await self.send_request(http_method, url_path, payload=payload)

    async def sign_request(
        self,
        http_method: str,
        url_path: str,
        payload: Dict[str, str] = None,
    ):
        if payload is None:
            payload = {}
        payload["timestamp"] = self._clock.timestamp() * 1000
        query_string = self._prepare_params(payload)
        signature = self._get_sign(query_string)
        payload["signature"] = signature
        return await self.send_request(http_method, url_path, payload)

    async def limited_encoded_sign_request(
        self,
        http_method: str,
        url_path: str,
        payload: Dict[str, str] = None,
    ) -> bytes:
        """
        Limit encoded sign request.

        This is used for some endpoints has special symbol in the url.
        In some endpoints these symbols should not encoded.
        - @
        - [
        - ]
        so we have to append those parameters in the url.
        """
        if payload is None:
            payload = {}
        payload["timestamp"] = self._clock.timestamp() * 1000
        query_string = self._prepare_params(payload)
        signature = self._get_sign(query_string)
        url_path = url_path + "?" + query_string + "&signature=" + signature
        return await self.send_request(http_method, url_path)

    async def send_request(
        self,
        http_method: str,
        url_path: str,
        payload: Dict[str, str] = None,
    ) -> bytes:
        print(f"\nRequest: {http_method}, {url_path}, {self._headers}, {payload}")
        if payload is None:
            payload = {}
        try:
            resp: ClientResponse = await self.request(
                method=http_method,
                url=self._base_url + url_path,
                headers=self._headers,
                params=self._prepare_params(payload),
            )
        except ClientResponseError as ex:
            await self._handle_exception(ex)

        if self._show_limit_usage:
            limit_usage = {}
            for key in resp.headers.keys():
                key = key.lower()
                if (
                    key.startswith("x-mbx-used-weight")
                    or key.startswith("x-mbx-order-count")
                    or key.startswith("x-sapi-used")
                ):
                    limit_usage[key] = resp.headers[key]

        return resp.data

    def _prepare_params(self, params) -> str:
        return encoded_string(clean_none_value(params))

    def _get_sign(self, data):
        m = hmac.new(self.secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256)
        return m.hexdigest()

    async def _handle_exception(self, error: ClientResponseError):
        if error.status < 400:
            return
        elif 400 <= error.status < 500:
            raise BinanceClientError(
                status=error.status,
                message=error.message,
                headers=error.headers,
            )
        else:
            raise BinanceServerError(
                status=error.status,
                message=error.message,
                headers=error.headers,
            )