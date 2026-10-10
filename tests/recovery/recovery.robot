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
${CONTAINER}          ecu-service
${DURATION}           10
${INTERVAL}           1
${RECOVERY_LOAD_PROFILE}    high
*** Test Cases ***

Verify ECU Recovers After Rogue Load
    ${profile}=    Get From Dictionary    ${LOAD_PROFILES}    ${RECOVERY_LOAD_PROFILE}
    ${start}=    Run Process    docker    compose    up    -d    --force-recreate    rogue-app
    ...    env:LOAD_PROFILE=${RECOVERY_LOAD_PROFILE}
    Should Be Equal As Integers    ${start.rc}    0    Could not start rogue load: ${start.stderr}

    Log    Applying ${RECOVERY_LOAD_PROFILE} load (${profile}[workers] workers) before recovery measurement
    Sleep    5s

    ${loaded}=    Measure Container
    ...    ${CONTAINER}
    ...    ${DURATION}
    ...    ${INTERVAL}
    ...    ${RESULTS_DIR}/recovery-load.csv

    Log    CPU average while load is active: ${loaded}[cpu_avg] %
    Should Be True
    ...    ${loaded}[cpu_avg] >= ${profile}[min_cpu_avg]
    ...    Recovery scenario did not establish load. Actual=${loaded}[cpu_avg]% Minimum=${profile}[min_cpu_avg]%

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
    ...    ${cpu_avg} <= ${RECOVERY}[max_cpu_avg]
    ...    ECU did not recover. CPU still high: ${cpu_avg}%

    Should Be True
    ...    ${memory_max} <= ${RECOVERY}[max_memory_mb]
    ...    ECU memory did not recover: ${memory_max} MB
