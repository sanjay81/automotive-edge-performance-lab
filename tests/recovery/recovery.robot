*** Settings ***
Library    ../../libraries/PerformanceLibrary.py
Variables    ../../config/thresholds.yaml
Resource    ../../resources/test_lifecycle.resource

Suite Setup       Prepare Performance Suite
Suite Teardown    Stop Rogue Load


*** Variables ***
${CONTAINER}          ecu-service
${DURATION}           10
${INTERVAL}           1
*** Test Cases ***

Verify ECU Recovers After Rogue Load
    Stop Rogue Load
    Sleep    5s

    ${result}=    Measure Container
    ...    ${CONTAINER}
    ...    ${DURATION}
    ...    ${INTERVAL}
    ...    ${RESULTS_DIR}/recovery.csv

    ${graphs}=    Generate Graphs
    ...    ${RESULTS_DIR}/recovery.csv
    ...    ${RESULTS_DIR}/recovery


    ${cpu_avg}=       Set Variable    ${result}[cpu_avg]
    ${memory_max}=    Set Variable    ${result}[memory_max]

    Log    Recovery CPU Average: ${cpu_avg} %
    Log    Recovery RAM Maximum: ${memory_max} MB

    Should Be True
    ...    ${cpu_avg} < ${RECOVERY}[max_cpu_avg]
    ...    ECU did not recover. CPU still high: ${cpu_avg}%

    Should Be True
    ...    ${memory_max} < ${RECOVERY}[max_memory_mb]
    ...    ECU memory did not recover: ${memory_max} MB
