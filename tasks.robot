# This Robot code gets _generated_ by the Robot bakery within Checkmk. 
# It is fully parametrized by the variables in ./variables/checkmk_vars.py

*** Settings ***
Documentation     Checkmk AAPM Robot
Library           Checkmk
Variables         checkmk_vars.py

*** Tasks ***
Check HTTP for ${APP_NAME}
    Check Http
    ...  ${CHECK_HTTP_URL}  
    ...  expected_status_code=${CHECK_HTTP_RESPONSE_CODE}  
    ...  timeout=${CHECK_HTTP_TIMEOUT}
    ...  warn=${CHECK_HTTP_WARN}
    ...  crit=${CHECK_HTTP_CRIT}

Check DNS for ${APP_NAME}
    # Check DNS  checkmk.com  expected_ip='45.133.11.28'
    Check DNS  ${CHECK_DNS_DOMAIN}
    ...  expected_ip=${CHECK_DNS_EXPECT_IP}
    ...  dns_server=${CHECK_DNS_SERVER}