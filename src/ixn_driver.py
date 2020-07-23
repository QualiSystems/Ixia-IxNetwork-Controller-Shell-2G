
from cloudshell.traffic.tg import TgControllerDriver, write_to_reservation_out

from ixn_handler import IxnHandler


class IxNetworkController2GDriver(TgControllerDriver):

    def __init__(self):
        self.handler = IxnHandler()

    def load_config(self, context, config_file_location):
        """ Load configuration and reserve ports. """
        return super().load_config(context, config_file_location)

    def send_arp(self, context):
        """ Send ARP/ND for all interfaces (NA for Linux servers that supports only ngpf). """
        return super().send_arp(context)

    def start_protocols(self, context):
        """ Start all protocols (classic and ngpf) on all ports. """
        return super().start_protocols(context)

    def stop_protocols(self, context):
        """ Stop all protocols (classic and ngpf) on all ports. """
        return super().stop_protocols(context)

    def start_traffic(self, context, blocking):
        """ Start traffic on all ports.

        :param blocking: True - return after traffic finish to run, False - return immediately.
        """
        return super().start_traffic(context, blocking)

    def stop_traffic(self, context):
        """ Stop traffic on all ports. """
        return super().stop_traffic(context)

    def get_statistics(self, context, view_name, output_type):
        """ Get view statistics.

        :param view_name: port, traffic item, flow group etc.
        :param output_type: CSV or JSON.
        """
        return super().get_statistics(context, view_name, output_type)

    def run_quick_test(self, context, test):
        """ Run quick test in blocking mode.

        :param test: name of quick test to run
        """
        return self.handler.run_quick_test(context, test)

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super().initialize(context)

    def cleanup(self):
        super().cleanup()

    def keep_alive(self, context, cancellation_context):
        super().keep_alive(context, cancellation_context)

    #
    # Hidden commands for developers only.
    #

    def get_session_id(self, context):
        """ API only command to get REST session ID.

        return: session ID
        """
        return self.handler.get_session_id()

    def get_children(self, context, obj_ref, child_type):
        """ API only command to get list of children.

        :param str obj_ref: valid object reference
        :param str child_type: requested children type. If None returns all children
        :return: list(object references of children)
        """
        return self.handler.get_children(obj_ref, child_type)

    def get_attributes(self, context, obj_ref):
        """ API only command to get object attributes.

        :param str obj_ref: valid object reference
        :return: dict(key, values) of all attributes
        """
        return self.handler.get_attributes(obj_ref)

    def set_attribute(self, context, obj_ref, attr_name, attr_value):
        """ API only command to set traffic generator object attribute.

        :param str obj_ref: valid object reference
        :param str attr_name: attribute name
        :param str attr_value: attribute value
        """
        self.handler.set_attribute(obj_ref, attr_name, attr_value)
