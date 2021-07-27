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

from nautilus_trader.analysis.reports import ReportProvider
from nautilus_trader.common.clock import TestClock
from nautilus_trader.common.factories import OrderFactory
from nautilus_trader.core.uuid import uuid4
from nautilus_trader.model.currencies import BTC
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.events.account import AccountState
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import PositionId
from nautilus_trader.model.identifiers import StrategyId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.position import Position
from nautilus_trader.trading.account import Account
from tests.test_kit.providers import TestInstrumentProvider
from tests.test_kit.stubs import TestStubs
from tests.test_kit.stubs import UNIX_EPOCH


SIM = Venue("SIM")
AUDUSD_SIM = TestInstrumentProvider.default_fx_ccy("AUD/USD")
GBPUSD_SIM = TestInstrumentProvider.default_fx_ccy("GBP/USD")


class TestReportProvider:
    def setup(self):
        # Fixture Setup
        self.account_id = TestStubs.account_id()
        self.order_factory = OrderFactory(
            trader_id=TraderId("TESTER-000"),
            strategy_id=StrategyId("S-001"),
            clock=TestClock(),
        )

    def test_generate_accounts_report_with_initial_account_state_returns_expected(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BITMEX", "1513111"),
            account_type=AccountType.MARGIN,
            base_currency=BTC,
            reported=True,
            balances=[
                AccountBalance(
                    currency=BTC,
                    total=Money(10.00000000, BTC),
                    free=Money(10.00000000, BTC),
                    locked=Money(0.00000000, BTC),
                )
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        account = Account(state)

        report_provider = ReportProvider()

        # Act
        report = report_provider.generate_account_report(account)

        # Assert
        assert len(report) == 1

    def test_generate_orders_report_with_no_order_returns_emtpy_dataframe(self):
        # Arrange
        report_provider = ReportProvider()

        # Act
        report = report_provider.generate_orders_report([])

        # Assert
        assert report.empty

    def test_generate_orders_fills_report_with_no_order_returns_emtpy_dataframe(self):
        # Arrange
        report_provider = ReportProvider()

        # Act
        report = report_provider.generate_order_fills_report([])

        # Assert
        assert report.empty

    def test_generate_positions_report_with_no_positions_returns_emtpy_dataframe(self):
        # Arrange
        report_provider = ReportProvider()

        # Act
        report = report_provider.generate_positions_report([])

        # Assert
        assert report.empty

    def test_generate_orders_report(self):
        # Arrange
        report_provider = ReportProvider()

        order1 = self.order_factory.limit(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(1500000),
            Price.from_str("0.80010"),
        )

        order1.apply(TestStubs.event_order_submitted(order1))
        order1.apply(TestStubs.event_order_accepted(order1))

        order2 = self.order_factory.limit(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(1500000),
            Price.from_str("0.80000"),
        )

        order2.apply(TestStubs.event_order_submitted(order2))
        order2.apply(TestStubs.event_order_accepted(order2))

        event = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-1"),
            last_px=Price.from_str("0.80011"),
        )

        order1.apply(event)

        orders = [order1, order2]

        # Act
        report = report_provider.generate_orders_report(orders)

        # Assert
        assert len(report) == 2
        assert report.index.name == "client_order_id"
        assert report.index[0] == order1.client_order_id.value
        assert report.iloc[0]["instrument_id"] == "AUD/USD.SIM"
        assert report.iloc[0]["side"] == "BUY"
        assert report.iloc[0]["type"] == "LIMIT"
        assert report.iloc[0]["quantity"] == "1500000"
        assert report.iloc[0]["avg_px"] == "0.80011"
        assert report.iloc[0]["slippage"] == "0.00001"
        assert report.iloc[1]["avg_px"] is None

    def test_generate_order_fills_report(self):
        # Arrange
        report_provider = ReportProvider()

        order1 = self.order_factory.limit(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(1500000),
            Price.from_str("0.80010"),
        )

        order1.apply(TestStubs.event_order_submitted(order1))
        order1.apply(TestStubs.event_order_accepted(order1))

        order2 = self.order_factory.limit(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(1500000),
            Price.from_str("0.80000"),
        )

        order2.apply(TestStubs.event_order_submitted(order2))
        order2.apply(TestStubs.event_order_accepted(order2))

        filled = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-1"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("0.80011"),
        )

        order1.apply(filled)

        orders = [order1, order2]

        # Act
        report = report_provider.generate_order_fills_report(orders)

        # Assert
        assert len(report) == 1
        assert report.index.name == "client_order_id"
        assert report.index[0] == order1.client_order_id.value
        assert report.iloc[0]["instrument_id"] == "AUD/USD.SIM"
        assert report.iloc[0]["side"] == "BUY"
        assert report.iloc[0]["type"] == "LIMIT"
        assert report.iloc[0]["quantity"] == "1500000"
        assert report.iloc[0]["avg_px"] == "0.80011"
        assert report.iloc[0]["slippage"] == "0.00001"

    def test_generate_positions_report(self):
        # Arrange
        report_provider = ReportProvider()

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
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00010"),
        )

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123457"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("1.00010"),
        )

        position1 = Position(instrument=AUDUSD_SIM, fill=fill1)
        position1.apply(fill2)

        position2 = Position(instrument=AUDUSD_SIM, fill=fill1)
        position2.apply(fill2)

        positions = [position1, position2]

        # Act
        report = report_provider.generate_positions_report(positions)

        # Assert
        assert len(report) == 2
        assert report.index.name == "position_id"
        assert report.index[0] == position1.id.value
        assert report.iloc[0]["instrument_id"] == "AUD/USD.SIM"
        assert report.iloc[0]["entry"] == "BUY"
        assert report.iloc[0]["side"] == "FLAT"
        assert report.iloc[0]["peak_qty"] == "100000"
        assert report.iloc[0]["avg_px_open"] == "1.00010"
        assert report.iloc[0]["avg_px_close"] == "1.00010"
        assert report.iloc[0]["ts_opened"] == UNIX_EPOCH
        assert report.iloc[0]["ts_closed"] == UNIX_EPOCH
        assert report.iloc[0]["realized_points"] == "0.00000"
        assert report.iloc[0]["realized_return"] == "0.00000"