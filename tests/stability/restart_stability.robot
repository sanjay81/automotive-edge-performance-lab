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
${RESTART_COUNT}         5


*** Test Cases ***

Verify ECU Restart Stability
    FOR    ${index}    IN RANGE    ${RESTART_COUNT}

        Log    Restart cycle: ${index + 1}

        ${startup_time}=    Measure Container Startup Time
        ...    ${CONTAINER}
        ...    ${HEALTH_URL}
        ...    ${STARTUP_TIMEOUT}

        Log    Startup time cycle ${index + 1}: ${startup_time} seconds

        Should Be True
        ...    ${startup_time} < ${STARTUP}[max_seconds]
        ...    Startup time exceeded in restart cycle ${index + 1}: ${startup_time}s

    END
