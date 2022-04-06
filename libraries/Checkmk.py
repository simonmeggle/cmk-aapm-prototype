from robot.api import logger
from robot.api.deco import not_keyword
import requests
import json 
import inspect
import dns.resolver

class Checkmk:
    """Generic library of the Checkmk Monitoring System for 
    application availability and performance monitoring (AAPM)."""

    ROBOT_LIBRARY_VERSION = "0.1"

    @not_keyword
    @staticmethod
    def state2str(state, msg):
        all_stack_frames = inspect.stack()
        caller_stack_frame = all_stack_frames[1]
        caller_name = caller_stack_frame[3]
        data = {
            caller_name: {
                'nagios_state': state, 
                'msg': msg
            }
        }
        #return json.dumps(data).encode('utf-8') 
        return json.dumps(data)

    def check_http(self, url, expected_status_code=200, timeout=10, warn=None, crit=None):
        """
        Checks a URL via HTTP

        Arguments:
        |  url - URL to check
        |  expected_status_code - expected status code
        |  timeout - seconds to wait for response
        |  warn - seconds to wait for response
        |  crit - seconds to wait for response

        Example:
        |  Check HTTP | https://checkmk.com | 200 | 10 |
        |  Check HTTP | https://checkmk.com | expected_status_code=201 | timeout=2
        |  Check HTTP | https://checkmk.com | warn=1 | crit=2
        """
        response = requests.get(url)
        if response.status_code != expected_status_code:
            raise Exception(f"HTTP response code '{response.status_code}' does not match expected status code")
            #self.add_checkmk_test_state(self, 'CRITICAL', 'HTTP status code is not as expected: ' + str(response.status_code))
        elapsed_sec = response.elapsed.total_seconds() + 1
        # elapsed_sec = response.elapsed.total_seconds() 
        if crit != None and elapsed_sec > crit:
                raise Exception(f"HTTP response took longer than {crit} seconds ({elapsed_sec}s)")
                # self.add_checkmk_test_state('CRITICAL', f'HTTP response took longer than {crit} seconds ({elapsed_sec})')
        elif warn != None and elapsed_sec > warn:
                self.add_checkmk_test_state('WARNING', 'HTTP response took longer than {warn} seconds ({elapsed_sec})')
    

    def check_dns(self, domain, expected_ip=None, timeout=10, warn=None, crit=None, use_dns_cache=False, dns_server=None):
        """
        Checks a host via DNS

        Arguments:
        |  domain - host to check
        |  expected_ip - expected IP address
        |  timeout - seconds to wait for response
        |  warn - seconds to wait for response
        |  crit - seconds to wait for response
        |  use_dns_cache - use DNS cache
        |  dns_server - DNS server to use

        Example:
        |  Check DNS | checkmk.com |
        |  Check DNS | checkmk.com | expected_ip=45.133.11.28
        |  Check DNS | checkmk.com | dns_server=8.8.8.8
        """
        my_resolver = dns.resolver.Resolver()

        if dns_server != None:
            my_resolver.nameservers = [dns_server]

        A = my_resolver.resolve(domain)
        adresses = [item.address for answer in A.response.answer for item in answer.items ]
        if expected_ip != None:
            if expected_ip not in adresses:
                self.add_checkmk_test_state('CRITICAL', 'DNS response does not match expected IP address')
            else: 
                logger.info('DNS response matches expected IP address {expected_ip}.')

    def add_checkmk_test_state(self, state: str, msg: str):
        """Adds a(nother) state to the Robotmk evaluation stack of the current test.

        Use this keyword if you want to change the state of the *current test*, together with a message. 
        
        This is especially useful if the test result in Checkmk should be ``WARNING`` (this state does not exist in Robot Framework).
        
        Remark: for ``OK`` or ``CRITICAL`` results the same effect can be achieved with the RF keywords ``Fail`` and ``Set Test Message``.

        See `Valid state types` section for information about available state types. 

        Example:

        | Add Checkmk Test State    WARNING    Hello. This test will be WARNING in Checkmk.
        """
        print(self.state2str(state, msg))

    def add_monitoring_message(self, state: str, msg: str):
        """Routes a message and state to the "Robotmk" monitoring service in Checkmk. 

        This keyword allows to generate a message/state about *administrative topics*, *unfilfilled preconditions* etc. (e.g. wrong screen resolution) and route it to the *Robotmk* service in Checkmk. This service gets automatically created once on every monitored Robot host and reports everything the *monitoring admins* should take care for. The E2E check availability will no be affected because it will remain ``OK``. 

        Why should you use this keyword? 
        
        Behind an E2E monitoring check there are often two different groups of interest:
        - The *monitoring admins*: They have to take care about the setup of test machines with Robot Framework, Checkmk, Robotmk, etc. It's their job to ensure that E2E tests have a reliable and stable environment to run.
        - The *application owners*: Their work gets judged on the availability report of the application's E2E check. It should only show application outages which actually occured. Therefore, they get pissed off if something unjustifiably pulls down the measured application availability. (In many cases they also are responsible to write the .robot tests).

        See `Valid state types` section for information about available state types. 

        Example:
        | Add Monitoring Message    WARNING    The user password for FooApp is expiring soon; make sure to change it to keep the test running.
        | Add Monitoring Message    CRITICAL   Invalid screen resolution detected! E2E suite ${SUITE_NAME} may run, but is built for 1024x768. 
        """
        print(self.state2str(state, msg))            