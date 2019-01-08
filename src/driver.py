from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface


class IxiaIxnetworkControllerShell2GDriver(ResourceDriverInterface):
    SHELL_TYPE = "CS_TrafficGeneratorController"
    SHELL_NAME = "Ixia IxNetwork Controller Shell 2G"

    def __init__(self):
        super(IxiaIxnetworkControllerShell2GDriver, self).__init__()
        self._cli = None

    def initialize(self, context):
        """

        :param context: ResourceCommandContext,ReservationContextDetailsobject with all Resource Attributes inside
        :type context:  context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        resource_config = IxiaIxnetworkControllerShell2GDriver.from_context(context=context,
                                                                            shell_name=self.SHELL_NAME,
                                                                            shell_type=self.SHELL_TYPE)
        session_pool_size = int(resource_config.sessions_concurrency_limit)
        # self._cli = get_cli(session_pool_size)

        return 'Finished initializing'

    def load_config(self, context, config_file_location):
        """Reserve ports and load configuration

        :param context:
        :param str config_file_location: configuration file location
        :return:
        """
        pass

    def start_traffic(self, context, blocking):
        """Start traffic on all ports

        :param context: the context the command runs on
        :param bool blocking: True - return after traffic finish to run, False - return immediately
        """
        pass

    def stop_traffic(self, context):
        """Stop traffic on all ports

        :param context: the context the command runs on
        """
        pass

    def get_statistics(self, context, view_name, output_type):
        """Get real time statistics as sandbox attachment

        :param context:
        :param str view_name: requested view name
        :param str output_type: CSV or JSON
        :return:
        """
        pass

    def send_arp(self, context):
        """Send ARP/ND for all protocols

        :param context:
        :return:
        """
        pass

    def start_protocols(self, context):
        """Start all protocols

        :param context:
        :return:
        """
        pass

    def stop_protocols(self, context):
        """Stop all protocols

        :param context:
        :return:
        """
        pass

    def run_quick_test(self, context):
        """Run quick test

        :param context:
        :return:
        """
        pass

    def get_session_id(self, context):
        """API only command to get REST session ID

        :param context:
        :return:
        """
        pass

    def get_children(self, context, obj_ref, child_type):
        """API only command to get list of children

        :param context:
        :param str obj_ref: valid object reference
        :param str child_type: requested children type. If None returns all children
        :return:
        """
        pass

    def get_attributes(self, context, obj_ref):
        """API only command to get object attributes

        :param context:
        :param str obj_ref: valid object reference
        :return:
        """
        pass

    def set_attribute(self, context, obj_ref, attr_name, attr_value):
        """API only command to set traffic generator object attribute

        :param context:
        :param str obj_ref: valid object reference
        :param str attr_name: attribute name
        :param str attr_value: attribute value
        :return:
        """
        pass

    def cleanup_reservation(self, context):
        """Clear reservation when it ends

        :param context:
        :return:
        """
        pass

    def cleanup(self, context):
        """

        :param context:
        :return:
        """
        pass

    def keep_alive(self, context, cancellation_context):
        """

        :param context:
        :param cancellation_context:
        :return:
        """
        pass
