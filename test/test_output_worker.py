# Copyright (C) 2014 SEE AUTHORS FILE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Unittests.
"""

import pika
import mock

from jinja2 import escape

from contextlib import nested

from . import TestCase

from replugin import outputworker


MQ_CONF = {
    'server': '127.0.0.1',
    'port': 5672,
    'vhost': '/',
    'user': 'guest',
    'password': 'guest',
}


class TestSleepWorker(TestCase):

    def setUp(self):
        """
        Set up some reusable mocks.
        """
        TestCase.setUp(self)

        self.channel = mock.MagicMock('pika.spec.Channel')

        self.channel.basic_consume = mock.Mock('basic_consume')
        self.channel.basic_ack = mock.Mock('basic_ack')
        self.channel.basic_publish = mock.Mock('basic_publish')

        self.basic_deliver = mock.MagicMock()
        self.basic_deliver.delivery_tag = 123

        self.properties = mock.MagicMock(
            'pika.spec.BasicProperties',
            correlation_id=123,
            reply_to='me')

        self.logger = mock.MagicMock('logging.Logger').__call__()
        self.app_logger = mock.MagicMock('logging.Logger').__call__()
        self.connection = mock.MagicMock('pika.SelectConnection')

    def tearDown(self):
        """
        After every test.
        """
        TestCase.tearDown(self)
        self.channel.reset_mock()
        self.channel.basic_consume.reset_mock()
        self.channel.basic_ack.reset_mock()
        self.channel.basic_publish.reset_mock()

        self.basic_deliver.reset_mock()
        self.properties.reset_mock()

        self.logger.reset_mock()
        self.app_logger.reset_mock()
        self.connection.reset_mock()

    def test_writing_a_message(self):
        """
        When the OutputWorker gets a message it should write it out to the
        _conf.output_dir + correlation_id.log file.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.outputworker.OutputWorker.notify'),
                mock.patch('replugin.outputworker.OutputWorker.send'),
                mock.patch('replugin.outputworker.open', create=True)) as (
                    _, _, _, mock_open):

            mock_open.return_value = mock.MagicMock(spec=file)
            worker = outputworker.OutputWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            body = {
                'message': 'testing'
            }

            # Execute the call
            worker.process(
                self.channel,
                self.basic_deliver,
                self.properties,
                body,
                self.logger)

            assert self.app_logger.error.call_count == 0
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.write.assert_called_once_with(escape('testing'+'\n'))

    def test_writing_a_message_will_redact_sensitive_output(self):
        """
        When the OutputWorker gets a message with data matching the
        redacted config option it should redact the result.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.outputworker.OutputWorker.notify'),
                mock.patch('replugin.outputworker.OutputWorker.send'),
                mock.patch('replugin.outputworker.open', create=True)) as (
                    _, _, _, mock_open):

            mock_open.return_value = mock.MagicMock(spec=file)
            worker = outputworker.OutputWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            body = {
                'message': 'a password\nanotherline\n'
            }

            # Execute the call
            worker.process(
                self.channel,
                self.basic_deliver,
                self.properties,
                body,
                self.logger)

            assert self.app_logger.error.call_count == 0
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.write.assert_called_once_with(escape(
                '[redacted]\nanotherline\n'))

    def test_writing_a_message_with_html_gets_escaped(self):
        """
        Verify that if HTML makes it into a message it should be escaped.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.outputworker.OutputWorker.notify'),
                mock.patch('replugin.outputworker.OutputWorker.send'),
                mock.patch('replugin.outputworker.open', create=True)) as (
                    _, _, _, mock_open):

            mock_open.return_value = mock.MagicMock(spec=file)

            worker = outputworker.OutputWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            body = {
                'message': '''<blink>testing</blink>

<b>stuff</b><javascript>var a="b";'''
            }

            # Execute the call
            worker.process(
                self.channel,
                self.basic_deliver,
                self.properties,
                body,
                self.logger)

            assert self.app_logger.error.call_count == 0
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.write.assert_called_once_with(escape(body['message']+'\n'))

    def test_executing_without_a_message(self):
        """
        If not message key is passed the worker should discard the message.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.outputworker.OutputWorker.notify'),
                mock.patch('replugin.outputworker.OutputWorker.send')):
            worker = outputworker.OutputWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            body = {}

            # Execute the call
            worker.process(
                self.channel,
                self.basic_deliver,
                self.properties,
                body,
                self.logger)

            assert self.app_logger.error.call_count == 1

    def test_writing_messages_with_newlines(self):
        """
        Escaped \\n characters are translated into actual newlines
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.outputworker.OutputWorker.notify'),
                mock.patch('replugin.outputworker.OutputWorker.send'),
                mock.patch('replugin.outputworker.open', create=True)) as (
                    _, _, _, mock_open):
            # http://www.voidspace.org.uk/python/weblog/arch_d7_2010_10_02.shtml
            #
            # "Mocking 'open'"
            mock_open.return_value = mock.MagicMock(spec=file)
            worker = outputworker.OutputWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            # Send a message with the actual string '\n' in it. This
            # should get translated into an actual newline character
            body = {
                'message': 'line1\\nline2'
            }
            written_msg = """line1
line2
"""
            # Execute the call
            worker.process(
                self.channel,
                self.basic_deliver,
                self.properties,
                body,
                self.logger)

            assert self.app_logger.error.call_count == 0
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.write.assert_called_with(written_msg)
