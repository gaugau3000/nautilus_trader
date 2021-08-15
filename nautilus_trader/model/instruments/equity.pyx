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
# -------------------------------------------------------------------------------------------------

from libc.stdint cimport int64_t

from decimal import Decimal

from nautilus_trader.model.c_enums.asset_class cimport AssetClass
from nautilus_trader.model.c_enums.asset_type cimport AssetType
from nautilus_trader.model.currency cimport Currency
from nautilus_trader.model.identifiers cimport InstrumentId
from nautilus_trader.model.instruments.base cimport Instrument
from nautilus_trader.model.objects cimport Price
from nautilus_trader.model.objects cimport Quantity


cdef class Equity(Instrument):
    """
    Represents an Equity instrument.
    """

    def __init__(
        self,
        InstrumentId instrument_id not None,
        Currency currency not None,
        int price_precision,
        Price price_increment not None,
        Quantity multiplier,
        Quantity lot_size not None,
        int contract_id,
        str local_symbol not None,
        str trading_class not None,
        str market_name not None,
        str long_name not None,
        str time_zone_id not None,
        str trading_hours not None,
        str last_trade_time not None,
        int64_t ts_event,
        int64_t ts_init,
    ):
        """
        Initialize a new instance of the ``Equity`` class.

        Parameters
        ----------
        instrument_id : InstrumentId
            The instrument ID.
        currency : Currency
            The futures contract currency.
        price_precision : int
            The price decimal precision.
        price_increment : Decimal
            The minimum price increment (tick size).
        multiplier : Decimal
            The contract value multiplier (determines tick value).
        lot_size : Quantity
            The rounded lot unit size (standard/board).
        ts_event: int64
            The UNIX timestamp (nanoseconds) when the instrument update occurred.
        ts_init: int64
            The UNIX timestamp (nanoseconds) when the instrument object was initialized.

        Raises
        ------
        ValueError
            If multiplier is not positive (> 0).
        ValueError
            If price_precision is negative (< 0).
        ValueError
            If tick_size is not positive (> 0).
        ValueError
            If lot size is not positive (> 0).

        """
        super().__init__(
            instrument_id=instrument_id,
            asset_class=AssetClass.EQUITY,
            asset_type=AssetType.SPOT,
            quote_currency=currency,
            is_inverse=False,
            price_precision=price_precision,
            size_precision=0,  # No fractional units
            price_increment=price_increment,
            size_increment=Quantity.from_int_c(1),
            multiplier=multiplier,
            lot_size=lot_size,
            max_quantity=None,
            min_quantity=Quantity.from_int_c(1),
            max_notional=None,
            min_notional=None,
            max_price=None,
            min_price=None,
            margin_initial=Decimal(),
            margin_maint=Decimal(),
            maker_fee=Decimal(),
            taker_fee=Decimal(),
            ts_event=ts_event,
            ts_init=ts_init,
            info={},
        )

        self.contract_id = contract_id
        self.local_symbol = local_symbol
        self.trading_class = trading_class
        self.market_name = market_name
        self.long_name = long_name
        self.time_zone_id = time_zone_id
        self.trading_hours = trading_hours
        self.last_trade_time = last_trade_time

    @staticmethod
    def from_dict(dict values) -> Instrument:
        """
        Return an instrument from the given initialization values.

        Parameters
        ----------
        values : dict[str, object]
            The values to initialize the instrument with.

        Returns
        -------
        Instrument

        """
        return Instrument.from_dict_c(values)

    @staticmethod
    def to_dict(Instrument obj):
        """
        Return a dictionary representation of this object.

        Returns
        -------
        dict[str, object]

        """
        return Instrument.to_dict_c(obj)