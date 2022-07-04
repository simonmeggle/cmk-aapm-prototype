from robot.api import logger
from robot.api.exceptions import ContinuableFailure, Failure, Error
from robot.api.deco import library, keyword
from robot.libraries.BuiltIn import BuiltIn
import requests
import json 
import inspect
import dns.resolver
import re
from collections import namedtuple

@library(scope="GLOBAL", auto_keywords=False)
class Checkmk:
    """Generic library of the Checkmk Monitoring System for 
    application availability and performance monitoring (AAPM).
    """

    ROBOT_LIBRARY_VERSION = "0.1"
    NAGIOS_STATES = {
        'ok': 0,
        'warning': 1, 
        'critical': 2,
        'unknown': 3
    }

    State = namedtuple('NagiosState', ['nagios_code', 'msg'])

    def __init__(self, config_file=None):
        """
        Initializes the library.
        """
        self.config_file = config_file
        self.global_config = {}
        self.kws_config = {}
        self.load_config()
        builtin = BuiltIn()
        # $APP_NAME is use in test cases to refer to the application name
        if self.config_file: 
            builtin.set_suite_variable("$APP_NAME", self.global_config.get('APP_NAME', '### APP_NAME variable used, but could not be read from config file! ###'))

    def cmk_args(kw_fn):
        """
        Decorator for Monitoring keywords. Tries to read arguments from the varfile config and applies the kw args 
        on top on that. This makes it possible to use the keyword with and without a config file.
        """
        def wrapper(self, *args, **kwargs):
            # read settings for the keyword from the config file
            keyword_cfg = self._get_kw_config(kw_fn.__name__)
            # apply the kw args on top of the config
            keyword_cfg.update(kwargs)
            return kw_fn(self, *args, **keyword_cfg)
        return wrapper

    def load_config(self):
        """
        Loads the configuration from the config file.
        """
        if self.config_file != None:
            try: 
                with open(self.config_file) as f:
                    vars = json.load(f)
                self.global_config = vars['global_config']
                self.kws_config = vars['kws_config']
            except: 
                raise Error(f"Could not load configuration from {self.config_file}")

    @keyword
    @cmk_args
    def check_http(self, url, page_regex=None, header_regex=None, status_code = None, auth=None, proxy=None, proxy_auth=None, onredirect=None, pagesize=None, warning=None, critical=None, timeout=None): 
        """
        Robot Framework keyword companion for 'check_http' - Checks a URL via HTTP 

        todo: unterteilen fail/calm
        todo: parameter "continue on failure"
        | url=STRING - URL to check (http://foo.com)
        | page_regex=STRING - Search page content for this regex
        | header_regex=STRING - Search response headers for this regex (ex: header_regex=X-Powered-.*:.*)
        | status_code=INTEGER - Expected status code
        | auth=STRING - username:password on sites with basic authentication
        | proxy=STRING - Proxy to use (http://proxy.com:8080)
        | proxy_auth=STRING - username:password on proxy-servers with basic authentication
        | onredirect=STRING - how to handle redirected pages (<ok|warning|critical|follow>)
        | pagesize=INTEGER<:INTEGER> - minimum page size required (bytes) : Maximum page size required (bytes)
        | warning=DOUBLE - response time to result in warning status (seconds)
        | critical=DOUBLE - response time to result in critical status (seconds)
        | timeout=INTEGER - seconds before connection times out (default: 10) 

        Examples:
        |  Check HTTP | url=https://checkmk.com | status_code=201 | timeout=2
        |  Check HTTP | url=https://checkmk.com | warning=1 | critical=2               
        """
        # calm states don't lead to a test FAIL (even critical ones). 
        # Used for metric checks (time and size).
        # They only leave a WARNING or CRITICAL log message which is parsed by the Robotmk check. 
        states_calm = []
        # fail_states are CRITICAL states and should lead to a test FAIL. 
        # Used for fact checks like status code, search ptterns etc.
        # They don't leave a log trace because the test itself fails. 
        states_fail = []

        logger.info(f"URL = {url}")
        # valid URL given?
        if not url or not re.match(r'^https?://', url):
            raise ValueError('Valid URL required!')

        # valid page size given?
        if pagesize:
            if not re.match(r'^\d+:\d+$', pagesize):
                raise ValueError('Pagesize must be in format "min:max"')
            else: 
                pagesize = list(map(int, pagesize.split(':')))

        if onredirect and not onredirect in ('ok', 'warning', 'critical', 'follow'):
            raise ValueError('Invalid onredirect value {}!', onredirect)

        self._validate_thresholds(warning, critical)

        # buld the request arguments proxy/timeout/auth
        request_args={}

        if proxy:
            request_args['proxies'] = {'http': str(proxy), 'https': str(proxy)}
        if timeout: 
            request_args['timeout'] = float(timeout)
        if auth: 
            if not re.match(r'^[^:]+:[^:]+$', auth):
                raise ValueError('Invalid auth string (muste be in username:password format)!')
            else: 
                request_args['auth'] = tuple(auth.split(':'))

        ### do the request
        try:
            # r = requests.get(url, timeout=float(timeout), proxies=proxies)
            r = requests.get(url, **request_args)
            r.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise Failure(f"Request to {url} timed out after {timeout} seconds")

        except requests.exceptions.TooManyRedirects as e:
            raise Failure(f"Request to {url} resulted in too many redirects")

        except requests.exceptions.ConnectionError as e:
            raise Failure(f"Request to {url} resulted in a connection error")

        except requests.exceptions.HTTPError as e:
            if auth and r.status_code == 401: 
                raise Failure(f"Authentication failed for {url} (401)")
            else: 
                raise Failure(f"Request to {url} resulted in an HTTP error: {r.status_code}")

        except Exception as e:
            raise Failure(f"Request to {url} resulted in a generic error: {e}")

        ### --- do the checks ---
        ### check: PAGE CONTENT
        if page_regex and not re.search(page_regex, r.text):
            states_fail.append(self.State(self.NAGIOS_STATES['critical'], f"Page content does not match regex {page_regex}"))
        
        ### check: HEADER CONTENT
        if header_regex and not any([re.search(header_regex, "%s:%s"%(h)) for h in r.headers.items()]):
            states_fail.append(self.State(self.NAGIOS_STATES['critical'], f"Header content does not match regex {header_regex}"))

        ### check: STATUS CODE/REDIRECTS
        if status_code and status_code != r.status_code:
            states_fail.append(self.State(self.NAGIOS_STATES['critical'], f"Status code is {r.status_code} instead of {status_code}"))
        else: 
            if r.status_code in [301, 302]:
                if onredirect in ('warning', 'critical'):
                    states_fail.append(self.State(self.NAGIOS_STATES[onredirect], f"Redirected to {r.headers['Location']}"))
            elif r.status_code != 200:
                states_fail.append(self.State(self.NAGIOS_STATES['critical'], f"Status code is {r.status_code}"))

        # size and response time = calm states = no test FAIL        
        ### check: PAGE SIZE (min:max)
        if pagesize:
            response_size = len(r.text)
            # minimum size
            if response_size < pagesize[0]:
                states_calm.append(self.State(self.NAGIOS_STATES['warning'], f"Page size is too small: {response_size} < {pagesize[0]}"))
            # maximum size
            if response_size > pagesize[1]:
                states_calm.append(self.State(self.NAGIOS_STATES['critical'], f"Page size is too big: {response_size} > {pagesize[1]}"))

        ### check: RESPONSE TIME
        responseTime = float(r.elapsed.microseconds/1000)/1000
        if critical and responseTime > float(critical):
            states_calm.append(self.State(self.NAGIOS_STATES['critical'], f"Response time is too high: {responseTime}s > {critical}s"))
        elif warning and responseTime > float(warning):
            states_calm.append(self.State(self.NAGIOS_STATES['warning'], f"Response time is too high: {responseTime}s > {warning}s"))
        
        ### -------- END OF CHECKS, do the EVALUATION
        # worst_state = max(states, key=lambda x: x.nagios_code).nagios_code
        warn_calm_messages = ", ".join([s.msg for s in states_calm if s.nagios_code == 1])
        crit_calm_messages = ", ".join([s.msg for s in states_calm if s.nagios_code == 2])
        if warn_calm_messages:
            self.add_checkmk_test_state('warning', warn_calm_messages, False)
        if crit_calm_messages:
            self.add_checkmk_test_state('critical', crit_calm_messages, False)

        crit_fail_messages = ", ".join([s.msg for s in states_fail if s.nagios_code == 2])
        if crit_fail_messages:
            # fail states overwrite calm states - and that's fully OK
            raise Failure(crit_fail_messages)    
         


    def check_http2(self, url, expected_status_code=200, timeout=10, warn=None, crit=None):

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
    
    @keyword
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

    @keyword
    def add_checkmk_test_state(self, state: str, msg: str, called_as_keyword=True):
        """Adds a(nother) state to the Robotmk evaluation stack of the current test.

        Use this keyword if you want to change the state of the *current test*, together with a message.  
        These messages will appear in the log file as WARN/CRIT log messages. 
                
        This is especially useful if the test result in Checkmk should be ``WARNING`` (this state does not exist in Robot Framework).  
        Remark: for ``OK`` or ``CRITICAL`` results the same effect can be achieved with the RF keywords ``Fail`` and ``Set Test Message``.
        See `Valid state types` section for information about available state types. 

        `called as keyword` must be set to `False` when this keyword gets called within another keyword's Pyhton code.

        Example 1 - use as keyword:
        | Add Checkmk Test State    WARNING    A warning message generated from a Robot test.
        Resulting log: 
        | `Checkmk state:  A warning message generated from a Robot test. `
        Example 2 - use within a monitoring keyword to add a warning state:
        | self.add_checkmk_test_state('WARNING', 'HTTP response took too long!')
        Resulting log:
        | Checkmk state: [check_http] HTTP response took too long!
        """
        if called_as_keyword:
            msg = 'Checkmk state: {}'.format(msg)
        else: 
            msg = 'Checkmk state: [{}] {}'.format(self.caller_name(), msg)

        if state.lower() == 'warning':
            logger.warn(msg)
        elif state.lower() == 'critical':
            logger.error(msg)

    @keyword
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

    @staticmethod
    def caller_name():
        """Returns the name of the calling function/keyword."""
        all_stack_frames = inspect.stack()
        caller_stack_frame = all_stack_frames[2]
        return caller_stack_frame[3]
        

    def _validate_thresholds(self, warn, crit):
        if warn is not None and crit is not None and warn > crit:
            raise Exception('Warning threshold must be smaller than critical threshold')

    def _get_kw_config(self, kw_name):
        """
        Returns the configuration for the given keyword.
        """
        return self.kws_config.get(kw_name, {})

    def _get_kw_config_value(self, kw_name, key):
        """
        Returns the value for the given key in the configuration for the given keyword.
        """
        return self._get_kw_config(kw_name)[key]

    def _get_kw_config_value_or_default(self, kw_name, key, default):
        """
        Returns the value for the given key in the configuration for the given keyword.
        If the key is not found, returns the default value.
        """
        if key in self._get_kw_config(kw_name):
            return self._get_kw_config(kw_name)[key]
        else:
            return default

    def _get_kw_config_value_or_default_from_kw_vars(self, kw_name, key, default):
        """
        Returns the value for the given key in the configuration for the given keyword.
        If the key is not found, returns the default value.
        """
        if key in self.kw_vars:
            return self.kw_vars[key]
        else:
            return default

    def _get_kw_config_value_or_default_from_kw_vars_or_default(self, kw_name, key, default):
        """
        Returns the value for the given key in the configuration for the given keyword.
        If the key is not found, returns the default value.
        """
        if key in self.kw_vars:
            return self.kw_vars[key]
        else:
            return default
