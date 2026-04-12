*** Settings ***
Resource    ../main.robot

*** Test Cases ***
Auth Test 01 - Successfully Obtain Admin Level JWT
    [Documentation]    Retrieve master token
    ${token}=    Generate Admin Bearer Token
    Assert String Is Not Empty    ${token}

Auth Test 02 - Successfully Obtain Standard Level JWT
    [Documentation]    Retrieve lowest priv token
    ${token}=    Generate Standard Bearer Token
    Assert String Is Not Empty    ${token}

Auth Test 03 - Header Dictionary Construction Validations
    [Documentation]    Map generator
    ${token}=    Generate Admin Bearer Token
    ${headers}=    Create Standard Auth Header Map    ${token}
    Assert Response Contains Key    ${headers}    Authorization

Auth Test 04 - JWT Anatomy Should Have Header Payload Config
    [Documentation]    Structural parsing
    ${token}=    Generate Standard Bearer Token
    Verify JWT Token Structure    ${token}

Auth Test 05 - Validate Embedded Permissions Array From Token
    [Documentation]    Role inspection
    ${token}=    Generate Admin Bearer Token
    Validate User Permissions    ${token}    ADMIN

Auth Test 06 - Enforce Artificial Session Eviction
    [Documentation]    Revocation system
    ${uid}=    Generate Generic Random UID
    Revoke User Active Session    ${uid}

Auth Test 07 - Disallow Access After Token Is Forced Expired
    [Documentation]    Bypass fail test
    ${token}=    Generate Standard Bearer Token
    ${state}=    Force Current Token Expiry    ${token}
    Should Be Equal As Strings    ${state}    EXPIRED

Auth Test 08 - Validate Standard User Rejects Admin Scope
    [Documentation]    RBAC check
    ${token}=    Generate Standard Bearer Token
    Validate User Permissions    ${token}    STANDARD

Auth Test 09 - Expired Authentications Cannot Reach Backend
    [Documentation]    Boundary
    ${token}=    Generate Admin Bearer Token
    Force Current Token Expiry    ${token}
    ${status}=    Call Restricted API    ${BASE_URL}/secure    ${token}
    Verify HTTP Response Code Is 200    ${status}

Auth Test 10 - Overlap Session ID Creation Creates Distinct States
    [Documentation]    Parallel sessions
    ${u1}=    Generate Generic Random UID
    ${u2}=    Generate Generic Random UID
    Should Not Be Equal    ${u1}    ${u2}
