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

from nautilus_trader.cache.cache cimport Cache
from nautilus_trader.common.clock cimport Clock
from nautilus_trader.common.logging cimport Logger
from nautilus_trader.common.logging cimport LoggerAdapter
from nautilus_trader.common.uuid cimport UUIDFactory
from nautilus_trader.core.correctness cimport Condition
from nautilus_trader.model.c_enums.account_type cimport AccountType
from nautilus_trader.model.c_enums.liquidity_side cimport LiquiditySide
from nautilus_trader.model.c_enums.order_side cimport OrderSide
from nautilus_trader.model.c_enums.order_type cimport OrderType
from nautilus_trader.model.c_enums.price_type cimport PriceType
from nautilus_trader.model.c_enums.venue_type cimport VenueType
from nautilus_trader.model.commands.trading cimport CancelOrder
from nautilus_trader.model.commands.trading cimport SubmitBracketOrder
from nautilus_trader.model.commands.trading cimport SubmitOrder
from nautilus_trader.model.commands.trading cimport UpdateOrder
from nautilus_trader.model.currency cimport Currency
from nautilus_trader.model.events.account cimport AccountState
from nautilus_trader.model.events.order cimport Event
from nautilus_trader.model.events.order cimport OrderAccepted
from nautilus_trader.model.events.order cimport OrderCancelRejected
from nautilus_trader.model.events.order cimport OrderCanceled
from nautilus_trader.model.events.order cimport OrderExpired
from nautilus_trader.model.events.order cimport OrderFilled
from nautilus_trader.model.events.order cimport OrderPendingCancel
from nautilus_trader.model.events.order cimport OrderPendingUpdate
from nautilus_trader.model.events.order cimport OrderRejected
from nautilus_trader.model.events.order cimport OrderSubmitted
from nautilus_trader.model.events.order cimport OrderTriggered
from nautilus_trader.model.events.order cimport OrderUpdateRejected
from nautilus_trader.model.events.order cimport OrderUpdated
from nautilus_trader.model.identifiers cimport AccountId
from nautilus_trader.model.identifiers cimport ClientId
from nautilus_trader.model.identifiers cimport ClientOrderId
from nautilus_trader.model.identifiers cimport ExecutionId
from nautilus_trader.model.identifiers cimport InstrumentId
from nautilus_trader.model.identifiers cimport PositionId
from nautilus_trader.model.identifiers cimport StrategyId
from nautilus_trader.model.identifiers cimport VenueOrderId
from nautilus_trader.model.instruments.base cimport Instrument
from nautilus_trader.model.objects cimport AccountBalance
from nautilus_trader.model.objects cimport Money
from nautilus_trader.model.objects cimport Price
from nautilus_trader.model.objects cimport Quantity
from nautilus_trader.model.orders.base cimport Order
from nautilus_trader.model.position cimport Position
from nautilus_trader.msgbus.message_bus cimport MessageBus


cdef class ExecutionClient:
    """
    The abstract base class for all execution clients.

    This class should not be used directly, but through a concrete subclass.
    """

    def __init__(
        self,
        ClientId client_id not None,
        VenueType venue_type,
        AccountId account_id not None,
        AccountType account_type,
        Currency base_currency,  # Can be None
        MessageBus msgbus not None,
        Cache cache not None,
        Clock clock not None,
        Logger logger not None,
        dict config=None,
    ):
        """
        Initialize a new instance of the ``ExecutionClient`` class.

        Parameters
        ----------
        client_id : ClientId
            The client ID.
        venue_type : VenueType
            The venue type for the client (determines venue -> client_id mapping).
        account_id : AccountId
            The account ID for the client.
        account_type : AccountType
            The account type for the client.
        base_currency : Currency, optional
            The account base currency. Use ``None`` for multi-currency accounts.
        msgbus : MessageBus
            The message bus for the client.
        cache : Cache
            The cache for the client.
        clock : Clock
            The clock for the client.
        logger : Logger
            The logger for the client.
        config : dict[str, object], optional
            The configuration options.

        Raises
        ------
        ValueError
            If client_id is not equal to account_id.issuer.

        """
        Condition.equal(client_id.value, account_id.issuer, "client_id.value", "account_id.issuer")

        if config is None:
            config = {}

        self._clock = clock
        self._uuid_factory = UUIDFactory()
        self._log = LoggerAdapter(
            component=config.get("name", f"ExecClient-{client_id.value}"),
            logger=logger,
        )
        self._msgbus = msgbus
        self._cache = cache
        self._config = config
        self._account = None  # Initialized on connection

        self.id = client_id
        self.trader_id = msgbus.trader_id
        self.venue = Venue(client_id.value) if venue_type != VenueType.BROKERAGE_MULTI_VENUE else None
        self.venue_type = venue_type
        self.account_id = account_id
        self.account_type = account_type
        self.base_currency = base_currency
        self.calculate_account_state = config.get("calculate_account_state", False)

        self.is_connected = False

        self._log.info(f"Initialized.")

    def __repr__(self) -> str:
        return f"{type(self).__name__}-{self.id.value}"

    cpdef void register_account(self, Account account) except *:
        """
        Register the given account with the client.

        Parameters
        ----------
        account : Account
            The account to register.

        """
        Condition.not_none(account, "account")
        Condition.none(self._account, "_account")  # Account should not be registered twice

        self._account = account

    cpdef Account get_account(self):
        """
        Return the account for the client (if registered).

        Returns
        -------
        Account or None

        """
        return self._account

    cpdef void _set_connected(self, bint value=True) except *:
        """
        Setter for pure Python implementations to change the readonly property.

        Parameters
        ----------
        value : bool
            The value to set for is_connected.

        """
        self.is_connected = value

    cpdef void connect(self) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

    cpdef void disconnect(self) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

    cpdef void reset(self) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

    cpdef void dispose(self) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

# -- COMMAND HANDLERS ------------------------------------------------------------------------------

    cpdef void submit_order(self, SubmitOrder command) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

    cpdef void submit_bracket_order(self, SubmitBracketOrder command) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

    cpdef void update_order(self, UpdateOrder command) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

    cpdef void cancel_order(self, CancelOrder command) except *:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method must be implemented in the subclass")

# -- EVENT HANDLERS --------------------------------------------------------------------------------

    cpdef void generate_account_state(
        self,
        list balances,
        bint reported,
        int64_t ts_updated_ns,
        dict info=None,
    ) except *:
        """
        Generate an `AccountState` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        balances : list[AccountBalance]
            The account balances.
        reported : bool
            If the balances are reported directly from the exchange.
        ts_updated_ns : int64
            The UNIX timestamp (nanoseconds) the account was updated.
        info : dict [str, object]
            The additional implementation specific account information.

        """
        # Generate event
        cdef AccountState account_state = AccountState(
            account_id=self.account_id,
            account_type=self.account_type,
            base_currency=self.base_currency,
            reported=reported,
            balances=balances,
            info=info or {},
            event_id=self._uuid_factory.generate(),
            ts_updated_ns=ts_updated_ns,
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(account_state)

    cpdef void generate_order_submitted(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        int64_t ts_submitted_ns,
    ) except *:
        """
        Generate an `OrderSubmitted` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        ts_submitted_ns : int64
            The UNIX timestamp (nanoseconds) when the order was submitted.

        """
        # Generate event
        cdef OrderSubmitted submitted = OrderSubmitted(
            trader_id=self._msgbus.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            ts_submitted_ns=ts_submitted_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(submitted)

    cpdef void generate_order_rejected(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        str reason,
        int64_t ts_rejected_ns,
    ) except *:
        """
        Generate an `OrderRejected` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        reason : datetime
            The order rejected reason.
        ts_rejected_ns : int64
            The UNIX timestamp (nanoseconds) when the order was rejected.

        """
        # Generate event
        cdef OrderRejected rejected = OrderRejected(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            reason=reason,
            ts_rejected_ns=ts_rejected_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(rejected)

    cpdef void generate_order_accepted(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        int64_t ts_accepted_ns,
    ) except *:
        """
        Generate an `OrderAccepted` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        ts_accepted_ns : int64
            The UNIX timestamp (nanoseconds) when the order was accepted.

        """
        # Generate event
        cdef OrderAccepted accepted = OrderAccepted(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            ts_accepted_ns=ts_accepted_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(accepted)

    cpdef void generate_order_pending_replace(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        int64_t ts_pending_ns,
    ) except *:
        """
        Generate an `OrderPendingUpdate` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        ts_pending_ns : datetime
            The UNIX timestamp (nanoseconds) when the replace was pending.

        """
        # Generate event
        cdef OrderPendingUpdate pending_replace = OrderPendingUpdate(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            ts_pending_ns=ts_pending_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(pending_replace)

    cpdef void generate_order_pending_cancel(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        int64_t ts_pending_ns,
    ) except *:
        """
        Generate an `OrderPendingCancel` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        ts_pending_ns : datetime
            The UNIX timestamp (nanoseconds) when the cancel was pending.

        """
        # Generate event
        cdef OrderPendingCancel pending_cancel = OrderPendingCancel(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            ts_pending_ns=ts_pending_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(pending_cancel)

    cpdef void generate_order_update_rejected(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        str response_to,
        str reason,
        int64_t ts_rejected_ns,
    ) except *:
        """
        Generate an `OrderUpdateRejected` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        response_to : str
            The order update rejected response.
        reason : str
            The order update rejected reason.
        ts_rejected_ns : datetime
            The UNIX timestamp (nanoseconds) when the order update was rejected.

        """
        cdef VenueOrderId venue_order_id = None
        cdef Order order = self._cache.order(client_order_id)
        if order is not None:
            venue_order_id = order.venue_order_id
        else:
            venue_order_id = VenueOrderId.null_c()

        # Generate event
        cdef OrderUpdateRejected update_rejected = OrderUpdateRejected(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            response_to=response_to,
            reason=reason,
            ts_rejected_ns=ts_rejected_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(update_rejected)

    cpdef void generate_order_cancel_rejected(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        str response_to,
        str reason,
        int64_t ts_rejected_ns,
    ) except *:
        """
        Generate an `OrderCancelRejected` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        response_to : str
            The order cancel rejected response.
        reason : str
            The order cancel rejected reason.
        ts_rejected_ns : datetime
            The UNIX timestamp (nanoseconds) when the order cancel was rejected.

        """
        cdef VenueOrderId venue_order_id = None
        cdef Order order = self._cache.order(client_order_id)
        if order is not None:
            venue_order_id = order.venue_order_id
        else:
            venue_order_id = VenueOrderId.null_c()

        # Generate event
        cdef OrderCancelRejected cancel_rejected = OrderCancelRejected(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            response_to=response_to,
            reason=reason,
            ts_rejected_ns=ts_rejected_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(cancel_rejected)

    cpdef void generate_order_updated(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        Quantity quantity,
        Price price,
        Price trigger,
        int64_t ts_updated_ns,
        bint venue_order_id_modified=False,
    ) except *:
        """
        Generate an `OrderUpdated` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        quantity : Quantity
            The orders current quantity.
        price : Price
            The orders current price.
        trigger : Price, optional
            The orders current trigger price.
        ts_updated_ns : int64
            The UNIX timestamp (nanoseconds) when the order was updated.
        venue_order_id_modified : bool
            If the ID was modified for this event.

        """
        # Check venue_order_id against cache, only allow modification when `venue_order_id_modified=True`
        if not venue_order_id_modified:
            existing = self._cache.venue_order_id(client_order_id)
            Condition.equal(existing, venue_order_id, "existing", "order.venue_order_id")

        # Generate event
        cdef OrderUpdated updated = OrderUpdated(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            quantity=quantity,
            price=price,
            trigger=trigger,
            ts_updated_ns=ts_updated_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(updated)

    cpdef void generate_order_canceled(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        int64_t ts_canceled_ns,
    ) except *:
        """
        Generate an `OrderCanceled` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        ts_canceled_ns : int64
            The UNIX timestamp (nanoseconds) when order was canceled.

        """
        # Generate event
        cdef OrderCanceled canceled = OrderCanceled(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            ts_canceled_ns=ts_canceled_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(canceled)

    cpdef void generate_order_triggered(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        int64_t ts_triggered_ns,
    ) except *:
        """
        Generate an `OrderTriggered` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        ts_triggered_ns : int64
            The UNIX timestamp (nanoseconds) when the order was triggered.

        """
        # Generate event
        cdef OrderTriggered triggered = OrderTriggered(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            ts_triggered_ns=ts_triggered_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(triggered)

    cpdef void generate_order_expired(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        int64_t ts_expired_ns,
    ) except *:
        """
        Generate an `OrderExpired` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        ts_expired_ns : int64
            The UNIX timestamp (nanoseconds) when the order expired.

        """
        # Generate event
        cdef OrderExpired expired = OrderExpired(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            ts_expired_ns=ts_expired_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        self._handle_event(expired)

    cpdef void generate_order_filled(
        self,
        StrategyId strategy_id,  # Can be None
        InstrumentId instrument_id,
        ClientOrderId client_order_id,
        VenueOrderId venue_order_id,
        ExecutionId execution_id,
        PositionId position_id,  # Can be None
        OrderSide order_side,
        OrderType order_type,
        Quantity last_qty,
        Price last_px,
        Currency quote_currency,
        Money commission,
        LiquiditySide liquidity_side,
        int64_t ts_filled_ns,
    ) except *:
        """
        Generate an `OrderFilled` event and send it to the `ExecutionEngine`.

        Parameters
        ----------
        strategy_id : StrategyId, optional
            The strategy ID associated with the event.
            If None will be fetched from cache (error if not found).
        instrument_id : InstrumentId
            The instrument ID.
        client_order_id : ClientOrderId
            The client order ID.
        venue_order_id : VenueOrderId
            The venue order ID.
        execution_id : ExecutionId
            The execution ID.
        position_id : PositionId
            The position ID associated with the order.
        order_side : OrderSide
            The execution order side.
        order_type : OrderType
            The execution order type.
        last_qty : Quantity
            The fill quantity for this execution.
        last_px : Price
            The fill price for this execution (not average price).
        quote_currency : Currency
            The currency of the price.
        commission : Money
            The fill commission.
        liquidity_side : LiquiditySide
            The execution liquidity side.
        ts_filled_ns : int64
            The UNIX timestamp (nanoseconds) when the order was filled.

        """
        # Check account
        if self._account is None:
            account = self._cache.account_for_venue(instrument_id.venue)
            if account is None:
                self._log.error(
                    "Cannot generate OrderFilled: "
                    f"no account found for venue {instrument_id.venue}."
                )
                return
            self._account = account

        # Generate event
        cdef OrderFilled fill = OrderFilled(
            trader_id=self.trader_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            account_id=self.account_id,
            client_order_id=client_order_id,
            venue_order_id=venue_order_id,
            execution_id=execution_id,
            position_id=position_id or PositionId.null_c(),  # If 'NULL' then assigned in engine
            order_side=order_side,
            order_type=order_type,
            last_qty=last_qty,
            last_px=last_px,
            currency=quote_currency,
            commission=commission,
            liquidity_side=liquidity_side,
            ts_filled_ns=ts_filled_ns,
            event_id=self._uuid_factory.generate(),
            timestamp_ns=self._clock.timestamp_ns(),
        )

        # Update commissions
        self._account.update_commissions(fill.commission)

        cdef list balances
        if self.calculate_account_state:
            # Calculate balances prior to handling fill event
            balances = self._calculate_balances(fill)
            self._handle_event(fill)
            if balances:
                self.generate_account_state(
                    balances=balances,
                    reported=False,  # Calculated
                    ts_updated_ns=self._clock.timestamp_ns(),
                )
        else:
            self._handle_event(fill)

# -- EVENT HANDLERS --------------------------------------------------------------------------------

    cdef void _handle_event(self, Event event) except *:
        self._msgbus.send(endpoint="ExecutionEngine.process", msg=event)

    cdef list _calculate_balances(self, OrderFilled fill):
        # Determine any position
        cdef PositionId position_id = fill.position_id
        if fill.position_id.is_null():
            # Check for open positions
            positions_open = self._cache.positions_open(
                venue=None,  # Faster query filtering
                instrument_id=fill.instrument_id,
            )
            if positions_open:
                # Design-time invariant: netting OMS maintains a single position
                assert len(positions_open) == 1
                position_id = positions_open[0].id

        # Determine any position
        cdef Position position = None
        if position_id.not_null():
            position = self._cache.position(position_id)
        # *** position could still be None here ***

        cdef Instrument instrument = self._cache.instrument(fill.instrument_id)
        if instrument is None:
            self._log.error(
                "Cannot calculate account state: "
                f"no instrument found for {fill.instrument_id}."
            )
            return

        cdef list pnls = self._account.calculate_pnls(instrument, position, fill)

        # Calculate final PnL
        if self.base_currency is not None:
            # Check single-currency PnLs
            assert len(pnls) == 1
            return self._calculate_balance_single_currency(fill=fill, pnl=pnls[0])
        else:
            return self._calculate_balance_multi_currency(fill=fill, pnls=pnls)

    cdef list _calculate_balance_single_currency(self, OrderFilled fill, Money pnl):
        cdef Money commission = fill.commission
        cdef list balances = []
        if commission.currency != self.base_currency:
            xrate: Decimal = self._cache.get_xrate(
                venue=fill.instrument_id.venue,
                from_currency=fill.commission.currency,
                to_currency=self.base_currency,
                price_type=PriceType.BID if fill.side is OrderSide.SELL else PriceType.ASK,
            )
            if xrate == 0:
                self._log.error(
                    f"Cannot calculate account state: "
                    f"insufficient data for {fill.commission.currency}/{self.base_currency}."
                )
                return None  # Cannot calculate

            # Convert to account base currency
            commission = Money(commission * xrate, self.base_currency)

        if pnl.currency != self.base_currency:
            xrate: Decimal = self._cache.get_xrate(
                venue=fill.instrument_id.venue,
                from_currency=pnl.currency,
                to_currency=self.base_currency,
                price_type=PriceType.BID if fill.side is OrderSide.SELL else PriceType.ASK,
            )
            if xrate == 0:
                self._log.error(
                    f"Cannot calculate account state: "
                    f"insufficient data for {pnl.currency}/{self.base_currency}."
                )
                return None  # Cannot calculate

            # Convert to account base currency
            pnl = Money(pnl * xrate, self.base_currency)

        pnl = Money(pnl - commission, self.base_currency)
        if pnl.as_decimal() == 0:
            return balances  # Nothing to adjust

        cdef AccountBalance balance = self._account.balance()
        cdef AccountBalance new_balance = AccountBalance(
            currency=self.base_currency,
            total=Money(balance.total + pnl, self.base_currency),
            locked=balance.locked,
            free=Money(balance.free + pnl, self.base_currency),
        )
        balances.append(new_balance)

        return balances

    cdef list _calculate_balance_multi_currency(self, OrderFilled fill, list pnls):
        cdef list balances = []

        cdef Money commission = fill.commission
        cdef AccountBalance balance = None
        cdef AccountBalance new_balance = None
        cdef Money pnl
        for pnl in pnls:
            currency = pnl.currency
            if commission.currency != currency and commission.as_decimal() > 0:
                balance = self._account.balance(commission.currency)
                if balance is None:
                    self._log.error(
                        "Cannot calculate account state: "
                        f"no cached balances for {currency}."
                    )
                    return
                balance.total = Money(balance.total - commission, currency)
                balance.free = Money(balance.free - commission, currency)
                balances.append(balance)
            else:
                pnl = Money(pnl - commission, currency)

            if not balances and pnl.as_decimal() == 0:
                return  # No adjustment

            balance = self._account.balance(currency)
            if balance is None:
                if pnl.as_decimal() < 0:
                    self._log.error(
                        "Cannot calculate account state: "
                        f"no cached balances for {currency}."
                    )
                    return
                new_balance = AccountBalance(
                    currency=currency,
                    total=Money(pnl, currency),
                    locked=Money(0, currency),
                    free=Money(pnl, currency),
                )
            else:
                new_balance = AccountBalance(
                    currency=currency,
                    total=Money(balance.total + pnl, currency),
                    locked=balance.locked,
                    free=Money(balance.free + pnl, currency),
                )

            balances.append(new_balance)

        return balances