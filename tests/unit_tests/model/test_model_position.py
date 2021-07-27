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

from decimal import Decimal

import pytest

from nautilus_trader.common.clock import TestClock
from nautilus_trader.common.factories import OrderFactory
from nautilus_trader.core.uuid import uuid4
from nautilus_trader.model.currencies import BTC
from nautilus_trader.model.currencies import ETH
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.events.order import OrderFilled
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import ExecutionId
from nautilus_trader.model.identifiers import PositionId
from nautilus_trader.model.identifiers import StrategyId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.position import Position
from tests.test_kit.providers import TestInstrumentProvider
from tests.test_kit.stubs import TestStubs


AUDUSD_SIM = TestInstrumentProvider.default_fx_ccy("AUD/USD")
BTCUSDT_BINANCE = TestInstrumentProvider.btcusdt_binance()
ETHUSDT_BINANCE = TestInstrumentProvider.ethusdt_binance()
XBTUSD_BITMEX = TestInstrumentProvider.xbtusd_bitmex()
ETHUSD_BITMEX = TestInstrumentProvider.ethusd_bitmex()


class TestPosition:
    def setup(self):
        # Fixture Setup
        self.trader_id = TestStubs.trader_id()
        self.account_id = TestStubs.account_id()
        self.order_factory = OrderFactory(
            trader_id=TraderId("TESTER-000"),
            strategy_id=StrategyId("S-001"),
            clock=TestClock(),
        )

    def test_side_from_order_side_given_invalid_value_returns_none(self):
        # Arrange
        # Act
        with pytest.raises(ValueError):
            Position.side_from_order_side(0)

    @pytest.mark.parametrize(
        "order_side,expected",
        [
            [OrderSide.BUY, PositionSide.LONG],
            [OrderSide.SELL, PositionSide.SHORT],
        ],
    )
    def test_side_from_order_side_given_valid_sides_returns_expected_side(
        self, order_side, expected
    ):
        # Arrange
        # Act
        position_side = Position.side_from_order_side(order_side)

        # Assert
        assert position_side == expected

    def test_position_hash_str_repr(self):
        # Arrange
        order = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill)

        # Act, Assert
        assert isinstance(hash(position), int)
        assert str(position) == "Position(LONG 100_000 AUD/USD.SIM, id=P-123456)"
        assert repr(position) == "Position(LONG 100_000 AUD/USD.SIM, id=P-123456)"

    def test_position_to_dict(self):
        # Arrange
        order = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill)

        # Act
        result = position.to_dict()

        # Assert
        assert result == {
            "position_id": "P-123456",
            "account_id": "SIM-000",
            "from_order": "O-19700101-000000-000-001-1",
            "strategy_id": "S-001",
            "instrument_id": "AUD/USD.SIM",
            "entry": "BUY",
            "side": "LONG",
            "net_qty": "100000",
            "quantity": "100000",
            "peak_qty": "100000",
            "ts_opened_ns": 0,
            "ts_closed_ns": 0,
            "duration_ns": 0,
            "avg_px_open": "1.00001",
            "avg_px_close": "None",
            "quote_currency": "USD",
            "base_currency": "AUD",
            "cost_currency": "USD",
            "realized_points": "0",
            "realized_return": "0.00000",
            "realized_pnl": "-2.00 USD",
            "commissions": "['2.00 USD']",
        }

    def test_position_filled_with_buy_order_returns_expected_attributes(self):
        # Arrange
        order = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
        )

        last = Price.from_str("1.00050")

        # Act
        position = Position(instrument=AUDUSD_SIM, fill=fill)

        # Assert
        assert position.symbol == AUDUSD_SIM.id.symbol
        assert position.venue == AUDUSD_SIM.id.venue
        assert not position.is_opposite_side(fill.side)
        assert not position != position  # Equality operator test
        assert position.from_order == ClientOrderId("O-19700101-000000-000-001-1")
        assert position.quantity == Quantity.from_int(100000)
        assert position.peak_qty == Quantity.from_int(100000)
        assert position.entry == OrderSide.BUY
        assert position.side == PositionSide.LONG
        assert position.ts_opened_ns == 0
        assert position.duration_ns == 0
        assert position.avg_px_open == Decimal("1.00001")
        assert position.event_count == 1
        assert position.client_order_ids == [order.client_order_id]
        assert position.venue_order_ids == [VenueOrderId("1")]
        assert position.execution_ids == [ExecutionId("E-19700101-000000-000-001-1")]
        assert position.last_execution_id == ExecutionId("E-19700101-000000-000-001-1")
        assert position.id == PositionId("P-123456")
        assert len(position.events) == 1
        assert position.is_long
        assert not position.is_short
        assert position.is_open
        assert not position.is_closed
        assert position.realized_points == 0
        assert position.realized_return == 0
        assert position.realized_pnl == Money(-2.00, USD)
        assert position.unrealized_pnl(last) == Money(49.00, USD)
        assert position.total_pnl(last) == Money(47.00, USD)
        assert position.commissions() == [Money(2.00, USD)]
        assert repr(position) == "Position(LONG 100_000 AUD/USD.SIM, id=P-123456)"

    def test_position_filled_with_sell_order_returns_expected_attributes(self):
        # Arrange
        order = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
        )

        last = Price.from_str("1.00050")

        # Act
        position = Position(instrument=AUDUSD_SIM, fill=fill)

        # Assert
        assert position.quantity == Quantity.from_int(100000)
        assert position.peak_qty == Quantity.from_int(100000)
        assert position.side == PositionSide.SHORT
        assert position.ts_opened_ns == 0
        assert position.avg_px_open == Decimal("1.00001")
        assert position.event_count == 1
        assert position.execution_ids == [ExecutionId("E-19700101-000000-000-001-1")]
        assert position.last_execution_id == ExecutionId("E-19700101-000000-000-001-1")
        assert position.id == PositionId("P-123456")
        assert not position.is_long
        assert position.is_short
        assert position.is_open
        assert not position.is_closed
        assert position.realized_points == 0
        assert position.realized_return == 0
        assert position.realized_pnl == Money(-2.00, USD)
        assert position.unrealized_pnl(last) == Money(-49.00, USD)
        assert position.total_pnl(last) == Money(-51.00, USD)
        assert position.commissions() == [Money(2.00, USD)]
        assert repr(position) == "Position(SHORT 100_000 AUD/USD.SIM, id=P-123456)"

    def test_position_partial_fills_with_buy_order_returns_expected_attributes(self):
        # Arrange
        order = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
            last_qty=Quantity.from_int(50000),
        )

        last = Price.from_str("1.00048")

        position = Position(instrument=AUDUSD_SIM, fill=fill)

        # Act
        # Assert
        assert position.quantity == Quantity.from_int(50000)
        assert position.peak_qty == Quantity.from_int(50000)
        assert position.side == PositionSide.LONG
        assert position.ts_opened_ns == 0
        assert position.avg_px_open == Decimal("1.00001")
        assert position.event_count == 1
        assert position.is_long
        assert not position.is_short
        assert position.is_open
        assert not position.is_closed
        assert position.realized_points == 0
        assert position.realized_return == 0
        assert position.realized_pnl == Money(-2.00, USD)
        assert position.unrealized_pnl(last) == Money(23.50, USD)
        assert position.total_pnl(last) == Money(21.50, USD)
        assert position.commissions() == [Money(2.00, USD)]
        assert repr(position) == "Position(LONG 50_000 AUD/USD.SIM, id=P-123456)"

    def test_position_partial_fills_with_sell_order_returns_expected_attributes(self):
        # Arrange
        order = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        fill1 = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            execution_id=ExecutionId("1"),
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
            last_qty=Quantity.from_int(50000),
        )

        fill2 = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            execution_id=ExecutionId("2"),
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00002"),
            last_qty=Quantity.from_int(50000),
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill1)

        last = Price.from_str("1.00050")

        # Act
        position.apply(fill2)

        # Assert
        assert position.quantity == Quantity.from_int(100000)
        assert position.side == PositionSide.SHORT
        assert position.ts_opened_ns == 0
        assert position.avg_px_open == Decimal("1.000015")
        assert position.event_count == 2
        assert not position.is_long
        assert position.is_short
        assert position.is_open
        assert not position.is_closed
        assert position.realized_points == 0
        assert position.realized_return == 0
        assert position.realized_pnl == Money(-4.00, USD)
        assert position.unrealized_pnl(last) == Money(-48.50, USD)
        assert position.total_pnl(last) == Money(-52.50, USD)
        assert position.commissions() == [Money(4.00, USD)]
        assert repr(position) == "Position(SHORT 100_000 AUD/USD.SIM, id=P-123456)"

    def test_position_filled_with_buy_order_then_sell_order_returns_expected_attributes(
        self,
    ):
        # Arrange
        order = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(150000),
        )

        fill1 = TestStubs.event_order_filled(
            order,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
            ts_filled_ns=1_000_000_000,
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill1)

        fill2 = OrderFilled(
            self.trader_id,
            StrategyId("S-001"),
            order.instrument_id,
            self.account_id,
            order.client_order_id,
            VenueOrderId("2"),
            ExecutionId("E2"),
            PositionId("T123456"),
            OrderSide.SELL,
            OrderType.MARKET,
            order.quantity,
            Price.from_str("1.00011"),
            AUDUSD_SIM.quote_currency,
            Money(0, USD),
            LiquiditySide.TAKER,
            2_000_000_000,
            uuid4(),
            0,
        )

        last = Price.from_str("1.00050")

        # Act
        position.apply(fill2)

        # Assert
        assert position.is_opposite_side(fill2.side)
        assert position.quantity == Quantity.zero()
        assert position.side == PositionSide.FLAT
        assert position.ts_opened_ns == 1_000_000_000
        assert position.duration_ns == 1_000_000_000
        assert position.avg_px_open == Decimal("1.00001")
        assert position.event_count == 2
        assert position.ts_closed_ns == 2_000_000_000
        assert position.avg_px_close == Decimal("1.00011")
        assert not position.is_long
        assert not position.is_short
        assert not position.is_open
        assert position.is_closed
        assert position.realized_points == Decimal("0.00010")
        assert position.realized_return == Decimal("0.00009999900000999990000099999000")
        assert position.realized_pnl == Money(12.00, USD)
        assert position.unrealized_pnl(last) == Money(0, USD)
        assert position.total_pnl(last) == Money(12.00, USD)
        assert position.commissions() == [Money(3.00, USD)]
        assert repr(position) == "Position(FLAT AUD/USD.SIM, id=P-123456)"

    def test_position_filled_with_sell_order_then_buy_order_returns_expected_attributes(
        self,
    ):
        # Arrange
        order1 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        order2 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-19700101-000000-000-001-1"),
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill1)

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            execution_id=ExecutionId("1"),
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
            last_qty=Quantity.from_int(50000),
        )

        fill3 = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            execution_id=ExecutionId("2"),
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00003"),
            last_qty=Quantity.from_int(50000),
        )

        last = Price.from_str("1.00050")

        # Act
        position.apply(fill2)
        position.apply(fill3)

        # Assert
        assert position.quantity == Quantity.zero()
        assert position.side == PositionSide.FLAT
        assert position.ts_opened_ns == 0
        assert position.avg_px_open == Decimal("1.0")
        assert position.event_count == 3
        assert position.client_order_ids == [order1.client_order_id, order2.client_order_id]
        assert position.ts_closed_ns == 0
        assert position.avg_px_close == Decimal("1.00002")
        assert not position.is_long
        assert not position.is_short
        assert not position.is_open
        assert position.is_closed
        assert position.realized_pnl == Money(-8.00, USD)
        assert position.unrealized_pnl(last) == Money(0, USD)
        assert position.total_pnl(last) == Money(-8.000, USD)
        assert position.commissions() == [Money(6.00, USD)]
        assert repr(position) == "Position(FLAT AUD/USD.SIM, id=P-19700101-000000-000-001-1)"

    def test_position_filled_with_no_change_returns_expected_attributes(self):
        # Arrange
        order1 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        order2 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-19700101-000000-000-001-1"),
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill1)

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00000"),
        )

        last = Price.from_str("1.00050")

        # Act
        position.apply(fill2)

        # Assert
        assert position.quantity == Quantity.zero()
        assert position.side == PositionSide.FLAT
        assert position.ts_opened_ns == 0
        assert position.avg_px_open == Decimal("1.0")
        assert position.event_count == 2
        assert position.client_order_ids == [order1.client_order_id, order2.client_order_id]
        assert position.execution_ids == [
            ExecutionId("E-19700101-000000-000-001-1"),
            ExecutionId("E-19700101-000000-000-001-2"),
        ]
        assert position.ts_closed_ns == 0
        assert position.avg_px_close == Decimal("1.0")
        assert not position.is_long
        assert not position.is_short
        assert not position.is_open
        assert position.is_closed
        assert position.realized_points == 0
        assert position.realized_return == 0
        assert position.realized_pnl == Money(-4.00, USD)
        assert position.unrealized_pnl(last) == Money(0, USD)
        assert position.total_pnl(last) == Money(-4.00, USD)
        assert position.commissions() == [Money(4.00, USD)]
        assert repr(position) == "Position(FLAT AUD/USD.SIM, id=P-19700101-000000-000-001-1)"

    def test_position_long_with_multiple_filled_orders_returns_expected_attributes(
        self,
    ):
        # Arrange
        order1 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        order2 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        order3 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(200000),
        )

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
        )

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00001"),
        )

        fill3 = TestStubs.event_order_filled(
            order3,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00010"),
        )

        last = Price.from_str("1.00050")

        # Act
        position = Position(instrument=AUDUSD_SIM, fill=fill1)
        position.apply(fill2)
        position.apply(fill3)

        # Assert
        assert position.quantity == Quantity.zero()
        assert position.side == PositionSide.FLAT
        assert position.ts_opened_ns == 0
        assert position.avg_px_open == Decimal("1.000005")
        assert position.event_count == 3
        assert position.client_order_ids == [
            order1.client_order_id,
            order2.client_order_id,
            order3.client_order_id,
        ]
        assert position.ts_closed_ns == 0
        assert position.avg_px_close == Decimal("1.0001")
        assert not position.is_long
        assert not position.is_short
        assert not position.is_open
        assert position.is_closed
        assert position.realized_pnl == Money(11.00, USD)
        assert position.unrealized_pnl(last) == Money(0, USD)
        assert position.total_pnl(last) == Money(11.00, USD)
        assert position.commissions() == [Money(8.00, USD)]
        assert repr(position) == "Position(FLAT AUD/USD.SIM, id=P-123456)"

    def test_pnl_calculation_from_trading_technologies_example(self):
        # https://www.tradingtechnologies.com/xtrader-help/fix-adapter-reference/pl-calculation-algorithm/understanding-pl-calculations/  # noqa

        # Arrange
        order1 = self.order_factory.market(
            ETHUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_int(12),
        )

        order2 = self.order_factory.market(
            ETHUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_int(17),
        )

        order3 = self.order_factory.market(
            ETHUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_int(9),
        )

        order4 = self.order_factory.market(
            ETHUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_int(4),
        )

        order5 = self.order_factory.market(
            ETHUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_int(3),
        )

        # Act
        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=ETHUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            last_px=Price.from_int(100),
        )

        position = Position(instrument=ETHUSDT_BINANCE, fill=fill1)

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=ETHUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            last_px=Price.from_int(99),
        )

        position.apply(fill2)
        assert position.quantity == Quantity.from_int(29)
        assert position.realized_pnl == Money(-0.28830000, USDT)
        assert position.avg_px_open == Decimal("99.41379310344827586206896552")

        fill3 = TestStubs.event_order_filled(
            order3,
            instrument=ETHUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_int(101),
        )

        position.apply(fill3)
        assert position.quantity == Quantity.from_int(20)
        assert position.realized_pnl == Money(13.89666207, USDT)
        assert position.avg_px_open == Decimal("99.41379310344827586206896552")

        fill4 = TestStubs.event_order_filled(
            order4,
            instrument=ETHUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_int(105),
        )

        position.apply(fill4)
        assert position.quantity == Quantity.from_int(16)
        assert position.realized_pnl == Money(36.19948966, USDT)
        assert position.avg_px_open == Decimal("99.41379310344827586206896552")

        fill5 = TestStubs.event_order_filled(
            order5,
            instrument=ETHUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_int(103),
        )

        position.apply(fill5)
        assert position.quantity == Quantity.from_int(19)
        assert position.realized_pnl == Money(36.16858966, USDT)
        assert position.avg_px_open == Decimal("99.98003629764065335753176042")
        assert (
            repr(position)
            == "Position(LONG 19.00000 ETH/USDT.BINANCE, id=P-19700101-000000-000-001-1)"
        )

    def test_position_realised_pnl_with_interleaved_order_sides(self):
        # Arrange
        order1 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("12.000000"),
        )

        order2 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("17.000000"),
        )

        order3 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_str("9.000000"),
        )

        order4 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("3.000000"),
        )

        order5 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_str("4.000000"),
        )

        # Act
        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            last_px=Price.from_str("10000.00"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill1)

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            last_px=Price.from_str("9999.00"),
        )

        position.apply(fill2)
        assert position.quantity == Quantity.from_str("29.000000")
        assert position.realized_pnl == Money(-289.98300000, USDT)
        assert position.avg_px_open == Decimal("9999.413793103448275862068966")

        fill3 = TestStubs.event_order_filled(
            order3,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10001.00"),
        )

        position.apply(fill3)
        assert position.quantity == Quantity.from_int(20)
        assert position.realized_pnl == Money(-365.71613793, USDT)
        assert position.avg_px_open == Decimal("9999.413793103448275862068966")

        fill4 = TestStubs.event_order_filled(
            order4,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10003.00"),
        )

        position.apply(fill4)
        assert position.quantity == Quantity.from_int(23)
        assert position.realized_pnl == Money(-395.72513793, USDT)
        assert position.avg_px_open == Decimal("9999.881559220389805097451274")

        fill5 = TestStubs.event_order_filled(
            order5,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-19700101-000000-000-001-1"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10005"),
        )

        position.apply(fill5)
        assert position.quantity == Quantity.from_int(19)
        assert position.realized_pnl == Money(-415.27137481, USDT)
        assert position.avg_px_open == Decimal("9999.881559220389805097451274")
        assert (
            repr(position)
            == "Position(LONG 19.000000 BTC/USDT.BINANCE, id=P-19700101-000000-000-001-1)"
        )

    def test_calculate_pnl_when_given_position_side_flat_returns_zero(self):
        # Arrange
        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_int(12),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        # Act
        result = position.calculate_pnl(
            Price.from_str("10500.00"),
            Price.from_str("10500.00"),
            Quantity.from_int(100000),
        )

        # Assert
        assert result == Money(0, USDT)

    def test_calculate_pnl_for_long_position_win(self):
        # Arrange
        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_int(12),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        # Act
        pnl = position.calculate_pnl(
            avg_px_open=Price.from_str("10500.00"),
            avg_px_close=Price.from_str("10510.00"),
            quantity=Quantity.from_int(12),
        )

        # Assert
        assert pnl == Money(120.00000000, USDT)
        assert position.realized_pnl == Money(-126.00000000, USDT)
        assert position.unrealized_pnl(Price.from_str("10510.00")) == Money(120.00000000, USDT)
        assert position.total_pnl(Price.from_str("10510.00")) == Money(-6.00000000, USDT)
        assert position.commissions() == [Money(126.00000000, USDT)]

    def test_calculate_pnl_for_long_position_loss(self):
        # Arrange
        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_int(12),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        # Act
        pnl = position.calculate_pnl(
            avg_px_open=Price.from_str("10500.00"),
            avg_px_close=Price.from_str("10480.50"),
            quantity=Quantity.from_int(10),
        )

        # Assert
        assert pnl == Money(-195.00000000, USDT)
        assert position.realized_pnl == Money(-126.00000000, USDT)
        assert position.unrealized_pnl(Price.from_str("10480.50")) == Money(-234.00000000, USDT)
        assert position.total_pnl(Price.from_str("10480.50")) == Money(-360.00000000, USDT)
        assert position.commissions() == [Money(126.00000000, USDT)]

    def test_calculate_pnl_for_short_position_winning(self):
        # Arrange
        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_str("10.150000"),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        # Act
        pnl = position.calculate_pnl(
            Price.from_str("10500.00"),
            Price.from_str("10390.00"),
            Quantity.from_str("10.150000"),
        )

        # Assert
        assert pnl == Money(1116.50000000, USDT)
        assert position.unrealized_pnl(Price.from_str("10390.00")) == Money(1116.50000000, USDT)
        assert position.realized_pnl == Money(-106.57500000, USDT)
        assert position.commissions() == [Money(106.57500000, USDT)]
        assert position.notional_value(Price.from_str("10390.00")) == Money(105458.50000000, USDT)

    def test_calculate_pnl_for_short_position_loss(self):
        # Arrange
        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_str("10"),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        # Act
        pnl = position.calculate_pnl(
            Price.from_str("10500.00"),
            Price.from_str("10670.50"),
            Quantity.from_str("10.000000"),
        )

        # Assert
        assert pnl == Money(-1705.00000000, USDT)
        assert position.unrealized_pnl(Price.from_str("10670.50")) == Money(-1705.00000000, USDT)
        assert position.realized_pnl == Money(-105.00000000, USDT)
        assert position.commissions() == [Money(105.00000000, USDT)]
        assert position.notional_value(Price.from_str("10670.50")) == Money(106705.00000000, USDT)

    def test_calculate_pnl_for_inverse1(self):
        # Arrange
        order = self.order_factory.market(
            XBTUSD_BITMEX.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=XBTUSD_BITMEX,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10000.00"),
        )

        position = Position(instrument=XBTUSD_BITMEX, fill=fill)

        # Act
        pnl = position.calculate_pnl(
            avg_px_open=Price.from_str("10000.00"),
            avg_px_close=Price.from_str("11000.00"),
            quantity=Quantity.from_int(100000),
        )

        # Assert
        assert pnl == Money(-0.90909091, BTC)
        assert position.unrealized_pnl(Price.from_str("11000.00")) == Money(-0.90909091, BTC)
        assert position.realized_pnl == Money(-0.00750000, BTC)
        assert position.notional_value(Price.from_str("11000.00")) == Money(9.09090909, BTC)

    def test_calculate_pnl_for_inverse2(self):
        # Arrange
        order = self.order_factory.market(
            ETHUSD_BITMEX.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=ETHUSD_BITMEX,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("375.95"),
        )

        position = Position(instrument=ETHUSD_BITMEX, fill=fill)

        # Act, Assert
        assert position.unrealized_pnl(Price.from_str("370.00")) == Money(4.27745208, ETH)
        assert position.notional_value(Price.from_str("370.00")) == Money(270.27027027, ETH)

    def test_calculate_unrealized_pnl_for_long(self):
        # Arrange
        order1 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("2.000000"),
        )

        order2 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("2.000000"),
        )

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill1)
        position.apply(fill2)

        # Act
        pnl = position.unrealized_pnl(Price.from_str("11505.60"))

        # Assert
        assert pnl == Money(4022.40000000, USDT)
        assert position.realized_pnl == Money(-42.00000000, USDT)
        assert position.commissions() == [Money(42.00000000, USDT)]

    def test_calculate_unrealized_pnl_for_short(self):
        # Arrange
        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_str("5.912000"),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10505.60"),
        )

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        pnl = position.unrealized_pnl(Price.from_str("10407.15"))

        # Assert
        assert pnl == Money(582.03640000, USDT)
        assert position.realized_pnl == Money(-62.10910720, USDT)
        assert position.commissions() == [Money(62.10910720, USDT)]

    def test_calculate_unrealized_pnl_for_long_inverse(self):
        # Arrange
        order = self.order_factory.market(
            XBTUSD_BITMEX.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=XBTUSD_BITMEX,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        position = Position(XBTUSD_BITMEX, fill)

        # Act

        pnl = position.unrealized_pnl(Price.from_str("11505.60"))

        # Assert
        assert pnl == Money(0.83238969, BTC)
        assert position.realized_pnl == Money(-0.00714286, BTC)
        assert position.commissions() == [Money(0.00714286, BTC)]

    def test_calculate_unrealized_pnl_for_short_inverse(self):
        # Arrange
        order = self.order_factory.market(
            XBTUSD_BITMEX.id,
            OrderSide.SELL,
            Quantity.from_int(1250000),
        )

        fill = TestStubs.event_order_filled(
            order,
            instrument=XBTUSD_BITMEX,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("15500.00"),
        )

        position = Position(XBTUSD_BITMEX, fill)

        # Act

        pnl = position.unrealized_pnl(Price.from_str("12506.65"))

        # Assert
        assert pnl == Money(19.30166700, BTC)
        assert position.realized_pnl == Money(-0.06048387, BTC)
        assert position.commissions() == [Money(0.06048387, BTC)]