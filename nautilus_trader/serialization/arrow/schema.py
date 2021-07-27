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

import pyarrow as pa

from nautilus_trader.model.data.tick import QuoteTick
from nautilus_trader.model.data.tick import TradeTick
from nautilus_trader.model.data.venue import InstrumentStatusUpdate
from nautilus_trader.model.events.account import AccountState
from nautilus_trader.model.events.order import OrderAccepted
from nautilus_trader.model.events.order import OrderCancelRejected
from nautilus_trader.model.events.order import OrderCanceled
from nautilus_trader.model.events.order import OrderDenied
from nautilus_trader.model.events.order import OrderExpired
from nautilus_trader.model.events.order import OrderFilled
from nautilus_trader.model.events.order import OrderInitialized
from nautilus_trader.model.events.order import OrderPendingCancel
from nautilus_trader.model.events.order import OrderPendingUpdate
from nautilus_trader.model.events.order import OrderRejected
from nautilus_trader.model.events.order import OrderSubmitted
from nautilus_trader.model.events.order import OrderTriggered
from nautilus_trader.model.events.order import OrderUpdateRejected
from nautilus_trader.model.events.order import OrderUpdated
from nautilus_trader.model.events.position import PositionChanged
from nautilus_trader.model.events.position import PositionClosed
from nautilus_trader.model.events.position import PositionOpened
from nautilus_trader.model.instruments.betting import BettingInstrument
from nautilus_trader.model.orderbook.data import OrderBookData


NAUTILUS_PARQUET_SCHEMA = {
    TradeTick: pa.schema(
        {
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "price": pa.string(),
            "size": pa.string(),
            "aggressor_side": pa.dictionary(pa.int8(), pa.string()),
            "match_id": pa.string(),
            "ts_event_ns": pa.int64(),
            "ts_recv_ns": pa.int64(),
        },
        metadata={"type": "TradeTick"},
    ),
    QuoteTick: pa.schema(
        {
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "bid": pa.string(),
            "bid_size": pa.string(),
            "ask": pa.string(),
            "ask_size": pa.string(),
            "ts_event_ns": pa.int64(),
            "ts_recv_ns": pa.int64(),
        },
        metadata={"type": "QuoteTick"},
    ),
    BettingInstrument: pa.schema(
        {
            "venue_name": pa.string(),
            "currency": pa.string(),
            "instrument_id": pa.string(),
            "event_type_id": pa.string(),
            "event_type_name": pa.string(),
            "competition_id": pa.string(),
            "competition_name": pa.string(),
            "event_id": pa.string(),
            "event_name": pa.string(),
            "event_country_code": pa.string(),
            "event_open_date": pa.string(),
            "betting_type": pa.string(),
            "market_id": pa.string(),
            "market_name": pa.string(),
            "market_start_time": pa.string(),
            "market_type": pa.string(),
            "selection_id": pa.string(),
            "selection_name": pa.string(),
            "selection_handicap": pa.string(),
            "ts_recv_ns": pa.int64(),
            "ts_event_ns": pa.int64(),
        },
        metadata={"type": "BettingInstrument"},
    ),
    OrderBookData: pa.schema(
        {
            "instrument_id": pa.string(),
            "ts_event_ns": pa.int64(),
            "ts_recv_ns": pa.int64(),
            "delta_type": pa.string(),
            "order_side": pa.string(),
            "order_price": pa.float64(),
            "order_size": pa.float64(),
            "order_id": pa.string(),
            "level": pa.string(),
            # Track grouped OrderBookDeltas
            "_type": pa.dictionary(pa.int8(), pa.string()),
            "_last": pa.bool_(),
        },
        metadata={"type": "OrderBookDelta"},
    ),
    AccountState: pa.schema(
        {
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "account_type": pa.dictionary(pa.int8(), pa.string()),
            "base_currency": pa.dictionary(pa.int8(), pa.string()),
            "balance_currency": pa.dictionary(pa.int8(), pa.string()),
            "balance_total": pa.float64(),
            "balance_locked": pa.float64(),
            "balance_free": pa.float64(),
            "reported": pa.bool_(),
            "info": pa.string(),
            "event_id": pa.string(),
            "ts_updated_ns": pa.int64(),
            "timestamp_ns": pa.int64(),
        }
    ),
    InstrumentStatusUpdate: pa.schema(
        {
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "status": pa.dictionary(pa.int8(), pa.string()),
            "ts_event_ns": pa.int64(),
            "ts_recv_ns": pa.int64(),
        }
    ),
    OrderInitialized: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "order_side": pa.dictionary(pa.int8(), pa.string()),
            "order_type": pa.dictionary(pa.int8(), pa.string()),
            "quantity": pa.float64(),
            "time_in_force": pa.dictionary(pa.int8(), pa.string()),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
            # Options fields
            # "options": pa.string(),
            "post_only": pa.bool_(),
            "reduce_only": pa.bool_(),
            "hidden": pa.bool_(),
            "price": pa.float64(),
            "trigger": pa.bool_(),
        }
    ),
    OrderDenied: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "reason": pa.dictionary(pa.int8(), pa.string()),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderSubmitted: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "ts_submitted_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderAccepted: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "ts_accepted_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderRejected: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "reason": pa.dictionary(pa.int8(), pa.string()),
            "ts_rejected_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderPendingCancel: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "ts_pending_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderCanceled: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "ts_canceled_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderCancelRejected: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "response_to": pa.string(),
            "reason": pa.string(),
            "ts_rejected_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderExpired: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "ts_expired_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderTriggered: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "ts_triggered_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderPendingUpdate: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "ts_pending_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderUpdateRejected: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "response_to": pa.dictionary(pa.int8(), pa.string()),
            "reason": pa.dictionary(pa.int8(), pa.string()),
            "ts_rejected_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderUpdated: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "price": pa.float64(),
            "trigger": pa.float64(),
            "ts_updated_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    OrderFilled: pa.schema(
        {
            "trader_id": pa.dictionary(pa.int8(), pa.string()),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "account_id": pa.dictionary(pa.int8(), pa.string()),
            "client_order_id": pa.string(),
            "venue_order_id": pa.string(),
            "execution_id": pa.string(),
            "position_id": pa.string(),
            "order_side": pa.dictionary(pa.int8(), pa.string()),
            "last_qty": pa.float64(),
            "last_px": pa.float64(),
            "currency": pa.string(),
            "commission": pa.string(),
            "liquidity_side": pa.string(),
            "ts_filled_ns": pa.int64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
            "info": pa.string(),
        }
    ),
    PositionOpened: pa.schema(
        {
            "position_id": pa.string(),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "entry": pa.string(),
            "side": pa.string(),
            "net_qty": pa.float64(),
            "quantity": pa.float64(),
            "peak_qty": pa.float64(),
            "ts_opened_ns": pa.int64(),
            "avg_px_open": pa.float64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    PositionChanged: pa.schema(
        {
            "position_id": pa.string(),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "entry": pa.string(),
            "side": pa.string(),
            "net_qty": pa.float64(),
            "quantity": pa.float64(),
            "peak_qty": pa.float64(),
            "ts_opened_ns": pa.int64(),
            "avg_px_open": pa.float64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
    PositionClosed: pa.schema(
        {
            "position_id": pa.string(),
            "strategy_id": pa.dictionary(pa.int8(), pa.string()),
            "instrument_id": pa.dictionary(pa.int8(), pa.string()),
            "entry": pa.string(),
            "side": pa.string(),
            "net_qty": pa.float64(),
            "quantity": pa.float64(),
            "peak_qty": pa.float64(),
            "ts_opened_ns": pa.int64(),
            "avg_px_open": pa.float64(),
            "avg_px_close": pa.float64(),
            "realized_pnl": pa.float64(),
            "event_id": pa.string(),
            "timestamp_ns": pa.int64(),
        }
    ),
}

# SCHEMA_TO_TYPE = {v.metadata[b"type"]: k for k, v in TYPE_TO_SCHEMA.items()}