*** Settings ***
Documentation     How to use the monitoring keywords of CheckmkLibrary in 
...  a regular Robot Framework test file. All keywords can/must be fully parametrized.   
Library           CheckmkLibrary

*** Tasks ***
Check HTTP google.de
    [Tags]  check_http
    Check Http  
    ...  url=http://google.de
    ...  page_regex=Auf gut Glück
    ...  warning=1.5
    ...  critical=2.0
