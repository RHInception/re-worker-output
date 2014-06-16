# -*- coding: utf-8 -*-
# Copyright © 2014 SEE AUTHORS FILE
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
Output worker.
"""
import os

from reworker.worker import Worker


class OutputWorkerError(Exception):
    """
    Base exception class for OutputWorker errors.
    """
    pass


class OutputWorker(Worker):
    """
    Worker which collects output messages and writes them out.
    """

    def process(self, channel, basic_deliver, properties, body, output):
        """
        Writes out output messages from the bus.

        .. note::
           Since this is an output worker it does not send messages to be
           consumed by notification or output workers.

        *Keys Requires*:
            * message: the message to write out.
        """
        # Ack the original message
        self.ack(basic_deliver)
        corr_id = str(properties.correlation_id)
        # Notify we are starting
        self.send(
            properties.reply_to, corr_id, {'status': 'started'}, exchange='')

        try:
            try:
                message = str(body['message'])
            except KeyError:
                raise OutputWorkerError('No message given. Nothing to do!')

            # Write out the message
            file_path = os.path.sep.join([
                self._config['output_dir'], ('%s.log' % corr_id)])
            with open(file_path, 'a') as output_file:
                if not message.endswith('\n'):
                    message = message + '\n'
                output_file.write(message)

            # Send out responses
            self.app_logger.info('Wrote output for correlation_id %s' % (
                corr_id))

        except OutputWorkerError, fwe:
            # If a OutputWorkerError happens send a failure log it.
            self.app_logger.error('Failure: %s' % fwe)


def main():  # pragma: no cover
    from reworker.worker import runner
    runner(OutputWorker)
