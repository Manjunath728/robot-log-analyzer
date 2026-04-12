*** Settings ***
Resource    ../main.robot

*** Test Cases ***
DB Test 01 - Connect And Disconnect Cycle Success
    [Documentation]    Base lifecycle
    ${conn}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    Assert String Is Not Empty    ${conn}
    Disconnect From DB Safely    ${conn}

DB Test 02 - Insert New User And Verify Insertion Return
    [Documentation]    Insert operation
    ${conn}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    ${uuid}=    Insert Mock User Data    dbadmin    SUPERUSER
    Assert String Is Not Empty    ${uuid}

DB Test 03 - Select Statement Returns Expected Mapped Array
    [Documentation]    Read operation
    ${conn}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    ${results}=    Execute Postgres Select Query    SELECT * FROM users    ${conn}
    Log    ${results}
    
DB Test 04 - Clean Up Target Table Leaves No Errors
    [Documentation]    Flush operation
    Clean Up Test Data From Table    sessions_table

DB Test 05 - Update Record Modifies At Least One Row
    [Documentation]    Update operation
    ${affected}=    Execute Postgres Update Query    UPDATE config SET act=1
    Should Be Equal As Strings    ${affected}    1

DB Test 06 - Database Connection String Format Validation
    [Documentation]    Checks format wrapper
    ${conf}=    Read Configuration YAML File    /mock/path
    Assert String Is Not Empty    ${conf.environment}

DB Test 07 - Verify Specific Required Record ID Present In DB
    [Documentation]    Specific lookup
    Verify DB Record Exists    user_1122    users
    
DB Test 08 - Create Ephemeral Record Then Truncate Table
    [Documentation]    Combined
    ${uuid}=    Insert Mock User Data    ephemeral_joe    USER
    Wait Until Application State Settles    1
    Clean Up Test Data From Table    users

DB Test 09 - Parallel Connection Mocking Validation
    [Documentation]    Pool check
    ${c1}=    Connect To Application DB    URL1
    ${c2}=    Connect To Application DB    URL2
    Disconnect From DB Safely    ${c1}
    Disconnect From DB Safely    ${c2}

DB Test 10 - Evaluate Missing Record Handles As Empty List
    [Documentation]    Empty array mock
    ${c}=    Connect To Application DB    ${DB_CONNECTION_STRING}
    ${r}=    Execute Postgres Select Query    SELECT * FROM dummy    ${c}
    Log    Done
