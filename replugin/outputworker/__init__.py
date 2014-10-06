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
import re

from reworker.worker import Worker

from jinja2 import escape


class OutputWorkerError(Exception):
    """
    Base exception class for OutputWorker errors.
    """
    pass


class OutputWorker(Worker):
    """
    Worker which collects output messages and writes them out.
    """

    def __init__(self, *args, **kwargs):
        Worker.__init__(self, *args, **kwargs)
        # There are no redactions by default
        self._redaction_rx = None
        # Attempt to pull redactions from the worker config
        redaction_cfg = self._config.get('redactions', [])
        if redaction_cfg:
            # if redactions exist in the config then build a regex from
            # the config to use for substitution.
            redaction_rx_build = '('
            for redaction in redaction_cfg:
                redaction_str = '.*%s[^\\n]*\\n|' % redaction
                self.app_logger.debug('Adding "%s"' % redaction)
                redaction_rx_build += redaction_str
            # Remove the last | and end the regex
            redaction_rx_build = redaction_rx_build[0:-1] + ')'
            self._redaction_rx = re.compile(redaction_rx_build)
            self.app_logger.info('Redactions are turned on.')
            self.app_logger.debug('Redaction RX: %s' % redaction_rx_build)

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
        # TODO: decide if we need 'start/stop' for these kinds of workers
        # Notify we are starting
        # self.send(
        #    properties.reply_to, corr_id, {'status': 'started'}, exchange='')

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
                message = message.replace('\\n', "\n")
                # escape HTML out
                message = escape(message)
                if self._redaction_rx:
                    message, subbed = self._redaction_rx.subn(
                        '[redacted]\n', message)
                    if subbed:
                        self.app_logger.info(
                            'Redacted a line in corr_id %s' % corr_id)
                # If anyone wants to make things pretty with HTML start here
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


if __name__ == '__main__':  # pragma nocover
    main()
