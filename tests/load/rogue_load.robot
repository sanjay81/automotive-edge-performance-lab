*** Settings ***
Library    ../../libraries/PerformanceLibrary.py
Library    Collections
Variables    ../../config/thresholds.yaml
Variables    ../../config/load_profiles.yaml
Resource    ../../resources/test_lifecycle.resource

Suite Setup       Prepare Performance Suite
Suite Teardown    Stop Rogue Load
Test Teardown     Stop Rogue Load


*** Variables ***
${CONTAINER}                 ecu-service
${DURATION}                  10
${INTERVAL}                  1
${LOAD_PROFILE}              medium

*** Test Cases ***

Verify ECU Performance Under Rogue Load
    ${profile}=    Get From Dictionary    ${LOAD_PROFILES}    ${LOAD_PROFILE}
    ${start}=    Run Process    docker    compose    up    -d    --force-recreate    rogue-app
    ...    env:LOAD_PROFILE=${LOAD_PROFILE}
    Should Be Equal As Integers    ${start.rc}    0    Could not start rogue load: ${start.stderr}

    Log    Running load profile=${LOAD_PROFILE}, workers=${profile}[workers]

    Sleep    5s

    ${result}=    Measure Container
    ...    ${CONTAINER}
    ...    ${DURATION}
    ...    ${INTERVAL}
    ...    ${RESULTS_DIR}/load-${LOAD_PROFILE}.csv

    ${graphs}=    Generate Graphs
    ...    ${RESULTS_DIR}/load-${LOAD_PROFILE}.csv
    ...    ${RESULTS_DIR}/load-${LOAD_PROFILE}

    ${cpu_avg}=       Set Variable    ${result}[cpu_avg]
    ${cpu_max}=       Set Variable    ${result}[cpu_max]
    ${memory_max}=    Set Variable    ${result}[memory_max]

    Log    Average CPU under load: ${cpu_avg} %
    Log    Maximum CPU under load: ${cpu_max} %
    Log    Maximum RAM under load: ${memory_max} MB

    Should Be True
    ...    ${cpu_avg} >= ${profile}[min_cpu_avg]
    ...    RogueApp profile '${LOAD_PROFILE}' did not generate enough CPU load. Actual=${cpu_avg}% Minimum=${profile}[min_cpu_avg]%

    Should Be True
    ...    ${cpu_avg} <= ${LOAD}[max_cpu_avg]
    ...    ECU CPU exceeded allowed load limit. Actual=${cpu_avg}% Maximum=${LOAD}[max_cpu_avg]%

    Should Be True
    ...    ${memory_max} <= ${LOAD}[max_memory_mb]
    ...    Memory limit exceeded. Actual=${memory_max} MB Maximum=${LOAD}[max_memory_mb] MB
