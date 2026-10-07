*** Settings ***
Library    Process


*** Variables ***
${RESULTS_DIR}    results


*** Keywords ***
Prepare Performance Suite
    ${result}=    Run Process    docker    compose    up    -d    ecu-service
    Should Be Equal As Integers    ${result.rc}    0    Could not start ecu-service: ${result.stderr}
    Stop Rogue Load

Stop Rogue Load
    ${result}=    Run Process    docker    compose    stop    rogue-app
    IF    ${result.rc} != 0
        Log    Rogue load was already stopped or unavailable: ${result.stderr}    WARN
    END
