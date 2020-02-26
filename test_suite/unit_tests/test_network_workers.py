# -------------------------------------------------------------------------------------------------
# <copyright file="test_network_workers.py" company="Nautech Systems Pty Ltd">
#  Copyright (C) 2015-2020 Nautech Systems Pty Ltd. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  https://nautechsystems.io
# </copyright>
# -------------------------------------------------------------------------------------------------

import unittest
import time
import zmq

from nautilus_trader.common.guid import LiveGuidFactory
from nautilus_trader.live.logger import LiveLogger
from nautilus_trader.network.workers import DealerWorker, SubscriberWorker
from nautilus_trader.network.compression import CompressorBypass
from nautilus_trader.network.encryption import EncryptionConfig
from nautilus_trader.network.identifiers import ClientId
from nautilus_trader.serialization.serializers import MsgPackRequestSerializer, MsgPackResponseSerializer
from test_kit.mocks import ObjectStorer, MockServer, MockPublisher
from nautilus_trader.common.clock import LiveClock

LOCALHOST = "127.0.0.1"
TEST_PORT = 55557
TEST_ADDRESS = f"tcp://{LOCALHOST}:{TEST_PORT}"


class DealerWorkerTests(unittest.TestCase):

    def setUp(self):
        # Fixture Setup
        clock = LiveClock()
        guid_factory = LiveGuidFactory()
        logger = LiveLogger()
        self.context = zmq.Context()
        self.response_handler = ObjectStorer()

        self.worker = DealerWorker(
            ClientId("Trader-001"),
            LOCALHOST,
            TEST_PORT,
            self.context,
            self.response_handler,
            MsgPackRequestSerializer(),
            MsgPackResponseSerializer(),
            CompressorBypass(),
            EncryptionConfig(),
            clock,
            guid_factory,
            logger)

        self.server = MockServer(self.context, TEST_PORT, logger)

    def tearDown(self):
        # Tear Down
        self.worker.disconnect()
        self.server.stop()

    # TODO
    # def test_send_message_to_wrong_address_times_out(self):
    #     # Arrange
    #     worker = RequestWorker(
    #         "TestRequester",
    #         "TestResponder",
    #         LOCALHOST,
    #         TEST_PORT + 1,
    #         self.context,
    #         CompressorBypass(),
    #         EncryptionConfig(),
    #         self.logger)
    #
    #     worker.connect()
    #
    #     # Act
    #     response = self.worker.send(b'hello')
    #
    #     # Assert
    #     self.assertEqual(b'OK', response)

    def test_can_send_one_message_and_receive_response(self):
        # Arrange
        self.worker.connect()

        # Act
        response = self.worker.send(b'hello')

        # Assert
        self.assertEqual(b'OK', response)

    def test_can_send_multiple_messages_and_receive_correctly_ordered_responses(self):
        # Arrange
        self.worker.connect()

        # Act
        response1 = self.worker.send(b'hello1')
        response2 = self.worker.send(b'hello2')
        response3 = self.worker.send(b'hello3')

        # Assert
        self.assertEqual(b'OK', response1)
        self.assertEqual(b'OK', response2)
        self.assertEqual(b'OK', response3)


class SubscriberWorkerTests(unittest.TestCase):

    def setUp(self):
        # Fixture Setup
        clock = LiveClock()
        guid_factory = LiveGuidFactory()
        logger = LiveLogger()
        self.zmq_context = zmq.Context()
        self.response_handler = ObjectStorer()

        self.worker = SubscriberWorker(
            ClientId("Subscriber-001"),
            'TestPublisher',
            LOCALHOST,
            TEST_PORT,
            self.zmq_context,
            self.response_handler.store_2,
            CompressorBypass(),
            EncryptionConfig(),
            clock,
            guid_factory,
            logger)

        self.publisher = MockPublisher(self.zmq_context, TEST_PORT, logger)

    def tearDown(self):
        # Tear Down
        self.worker.disconnect()
        self.worker.dispose()
        self.publisher.stop()

    def test_can_subscribe_to_topic_and_receive_one_published_message(self):
        # Arrange
        self.worker.connect()
        self.worker.subscribe('test_topic')

        time.sleep(0.1)
        # Act
        self.publisher.publish('test_topic', b'hello subscribers')

        time.sleep(0.1)
        # Assert
        self.assertEqual(('test_topic', b'hello subscribers'), self.response_handler.get_store()[0])

    def test_can_subscribe_to_topic_and_receive_multiple_published_messages_in_correct_order(self):
        # Arrange
        self.worker.connect()
        self.worker.subscribe('test_topic')

        time.sleep(0.1)
        # Act
        self.publisher.publish('test_topic', b'hello1')
        self.publisher.publish('test_topic', b'hello2')
        self.publisher.publish('test_topic', b'hello3')

        time.sleep(0.1)
        # Assert
        self.assertEqual(('test_topic', b'hello1'), self.response_handler.get_store()[0])
        self.assertEqual(('test_topic', b'hello2'), self.response_handler.get_store()[1])
        self.assertEqual(('test_topic', b'hello3'), self.response_handler.get_store()[2])
