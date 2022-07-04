# This Robot code gets _generated_ by the Robot bakery within Checkmk. 

*** Settings ***
Documentation     Checkmk AAPM Robot for '${APP_NAME}'
# Library           Checkmk  
Library           Checkmk  config_file=checkmk_vars.json

*** Tasks ***
# Check HTTP elabit.de
#     [Tags]  check_http
#     # Check Http
#     Check Http  url=http://elabit.de

Check HTTP ${APP_NAME}
    [Tags]  check_http
    Check Http
    
