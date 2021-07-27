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

from nautilus_trader.common.clock cimport Clock
from nautilus_trader.common.logging cimport LoggerAdapter
from nautilus_trader.model.identifiers cimport TraderId
from nautilus_trader.msgbus.subscription cimport Subscription


cdef class MessageBus:
    cdef Clock _clock
    cdef LoggerAdapter _log
    cdef dict _subscriptions
    cdef dict _patterns
    cdef dict _endpoints

    cdef readonly TraderId trader_id
    """The trader ID associated with the bus.\n\n:returns: `TraderId`"""
    cdef readonly int processed_count
    """The count of messages process by the bus.\n\n:returns: `int32`"""

    cpdef list endpoints(self)
    cpdef list topics(self)
    cpdef list subscriptions(self, str topic=*)
    cpdef bint has_subscribers(self, str topic=*)

    cpdef void register(self, str endpoint, handler) except *
    cpdef void deregister(self, str endpoint, handler) except *
    cpdef void send(self, str endpoint, msg) except *
    cpdef void subscribe(self, str topic, handler, int priority=*) except *
    cpdef void unsubscribe(self, str topic, handler) except *
    cpdef void publish(self, str topic, msg) except *
    cdef void publish_c(self, str topic, msg) except *
    cdef Subscription[:] _resolve_subscriptions(self, str topic)