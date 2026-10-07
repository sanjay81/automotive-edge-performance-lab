*** Settings ***
Library    ../../libraries/PerformanceLibrary.py
Variables    ../../config/thresholds.yaml
Resource    ../../resources/test_lifecycle.resource

Suite Setup       Prepare Performance Suite
Suite Teardown    Stop Rogue Load


*** Variables ***
${CONTAINER}             ecu-service
${HEALTH_URL}            http://localhost:8080/health

${STARTUP_TIMEOUT}       15
*** Test Cases ***

Verify ECU Startup Time
    ${startup_time}=    Measure Container Startup Time
    ...    ${CONTAINER}
    ...    ${HEALTH_URL}
    ...    ${STARTUP_TIMEOUT}

    Log    ECU startup time: ${startup_time} seconds

    Should Be True
    ...    ${startup_time} < ${STARTUP}[max_seconds]
    ...    ECU startup time exceeded limit. Actual=${startup_time}s Maximum=${STARTUP}[max_seconds]s
