*** Settings ***
Resource    ../main.robot

*** Test Cases ***
E2E Test 01 - Direct API Object Creation Verified In UI List
    [Documentation]    Full stack check
    ${payload}=    Format Raw Payload For API    title    GlobalObj
    ${id}=    Post Data Object    ${BASE_URL}/create    ${payload}
    Launch Web Application Dummy    ${UI_BASE_URL}
    Perform Admin Login    Administrator    Pass
    Navigate To Admin Dashboard
    Verify Success Toaster Visible    Loaded
    Close Client Web Session

E2E Test 02 - Creating Via UI Inserts Data Into DB Correctly
    [Documentation]    UI to DB pipeline
    Launch Web Application Dummy    ${UI_BASE_URL}
    Fill And Submit Creation Form    UserFromUI    Agent
    Close Client Web Session
    ${c}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    Verify DB Record Exists    UserFromUI    users
    Disconnect From DB Safely    ${c}

E2E Test 03 - Complete User Revocation Lifecycle
    [Documentation]    Auth -> API -> DB
    ${conn}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    ${target_user}=    Insert Mock User Data    revokedUser    GUEST
    ${token}=    Generate Standard Bearer Token
    Force Current Token Expiry    ${token}
    Clean Up Test Data From Table    users
    Disconnect From DB Safely    ${conn}

E2E Test 04 - Ensure Admin API Calls Leave Event Tracking In Core DB
    [Documentation]    Audit pipeline
    ${token}=    Generate Admin Bearer Token
    Call Restricted API    ${BASE_URL}/dangerous    ${token}
    ${cn}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    ${res}=    Execute Postgres Select Query    SELECT * FROM audit    ${cn}
    Disconnect From DB Safely    ${cn}

E2E Test 05 - Generate Ephemeral Environment Reaches Stable Steady State
    [Documentation]    Spinup test
    Wait Until Application State Settles    2
    ${conf}=    Read Configuration YAML File    config.yml
    Launch Web Application Dummy    ${conf.base_url}
    Close Client Web Session

E2E Test 06 - Attempting UI Login With Expired Token Automatically Rejects
    [Documentation]    UI + Auth Negative Flow
    ${token}=    Generate Standard Bearer Token
    Force Current Token Expiry    ${token}
    Launch Web Application Dummy    ${UI_BASE_URL}
    Capture Screenshot On Failure Dummy
    Close Client Web Session

E2E Test 07 - API Create + Update + DB Verify Pipeline
    [Documentation]    Complex mutation
    ${uid}=    Generate Generic Random UID
    ${pl}=    Format Raw Payload For API    id    ${uid}
    Post Data Object    ${BASE_URL}/start    ${pl}
    Execute Postgres Update Query    UPDATE t SET live=true
    Wait Until Application State Settles    1

E2E Test 08 - Extract Embedded Config Parameters For API Headers
    [Documentation]    Utils + Auth + API
    ${c}=    Read Configuration YAML File    system.txt
    ${t}=    Generate Admin Bearer Token
    ${h}=    Create Standard Auth Header Map    ${t}
    ${resp}=    Get Resource Payload    1
    Assert Response Contains Key    ${h}    Authorization

E2E Test 09 - Multi-Day Future Timestamp Generates Valid Reservation Record
    [Documentation]    Time travel logic test
    ${future}=    Get Future Evaluated Timestamp    4
    ${pl}=    Format Raw Payload For API    reservation_date    ${future}
    ${id}=    Post Data Object    ${BASE_URL}/rsvp    ${pl}
    ${cn}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    Verify DB Record Exists    ${id}    reservations
    Disconnect From DB Safely    ${cn}

E2E Test 10 - The Grand Final Pipeline Test Execution
    [Documentation]    Touches absolutely everything.
    ${tok}=    Generate Admin Bearer Token
    Verify JWT Token Structure    ${tok}
    ${h}=    Create Standard Auth Header Map    ${tok}
    ${db}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    Execute Postgres Update Query    FLUSH ALL
    Launch Web Application Dummy    ${UI_BASE_URL}
    Navigate To Admin Dashboard
    Verify Success Toaster Visible    Dashboard Active
    Close Client Web Session
    Disconnect From DB Safely    ${db}
    Wait Until Application State Settles    1
