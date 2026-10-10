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

Verify ECU Idle Performance
    ${result}=    Measure Container
    ...    ${CONTAINER}
    ...    ${DURATION}
    ...    ${INTERVAL}
    ...    ${RESULTS_DIR}/idle.csv

    ${graphs}=    Generate Graphs
    ...    ${RESULTS_DIR}/idle.csv
    ...    ${RESULTS_DIR}/idle

    ${cpu_avg}=       Set Variable    ${result}[cpu_avg]
    ${cpu_max}=       Set Variable    ${result}[cpu_max]
    ${memory_avg}=    Set Variable    ${result}[memory_avg]
    ${memory_max}=    Set Variable    ${result}[memory_max]

    Log    Average CPU: ${cpu_avg} %
    Log    Maximum CPU: ${cpu_max} %
    Log    Average RAM: ${memory_avg} MB
    Log    Maximum RAM: ${memory_max} MB

    Should Be True
    ...    ${cpu_avg} <= ${IDLE}[max_cpu_avg]
    ...    Average CPU exceeded limit: ${cpu_avg}% > ${IDLE}[max_cpu_avg]%

    Should Be True
    ...    ${cpu_max} <= ${IDLE}[max_cpu_peak]
    ...    Peak CPU exceeded limit: ${cpu_max}% > ${IDLE}[max_cpu_peak]%

    Should Be True
    ...    ${memory_max} <= ${IDLE}[max_memory_mb]
    ...    RAM exceeded limit: ${memory_max} MB > ${IDLE}[max_memory_mb] MB
