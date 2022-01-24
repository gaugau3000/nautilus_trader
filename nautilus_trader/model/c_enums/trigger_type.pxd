# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2022 Nautech Systems Pty Ltd. All rights reserved.
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


cpdef enum TriggerType:
    DEFAULT = 0
    LAST = 1
    BID_ASK = 2
    DOUBLE_LAST = 3
    DOUBLE_BID_ASK = 4
    LAST_OR_BID_ASK = 5
    MID_POINT = 6
    MARK = 7
    INDEX = 8



cdef class TriggerTypeParser:

    @staticmethod
    cdef str to_str(int value)

    @staticmethod
    cdef TriggerType from_str(str value) except *