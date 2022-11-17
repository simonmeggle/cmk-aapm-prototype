*** Comments ***
# This Robot code gets _generated_ by the Robot bakery within Checkmk.


*** Settings ***
Documentation       Checkmk AAPM Robot for '${APP_NAME}'

# simple url
#Library    CheckmkLibrary    config_file=checkmk_vars-1.json
# OK - params
Library             CheckmkLibrary    config_file=checkmk_vars-2.json
# FAIL - header regex
# Library    CheckmkLibrary    config_file=checkmk_vars-3.json
# OK - respone time too long, but test PASS
# Library    CheckmkLibrary    config_file=checkmk_vars-4.json
# CRIT - respone time too long, but test FAIL (fail_on_thresholds=True)
# Library    CheckmkLibrary    config_file=checkmk_vars-5.json


*** Tasks ***
Check HTTP ${APP_NAME}
    [Tags]    check_http
    Check Http

Check DNS ${APP_NAME}
    [Tags]    check_dns
    Check Dns

Check Ftp ${APP_NAME}
    [Tags]    check_ftp
    Check Ftp

# Check Network Bandwidth
#    [Tags]    check_network_bandwidth
#    Check Network Bandwidth

# Check Ping ${APP_NAME}
#    [Tags]    check_ping
#    Check Ping
