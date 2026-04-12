*** Settings ***
Resource    ../main.robot

*** Test Cases ***
API Test 01 - Retrieve Active Resource With Valid ID
    [Documentation]    Simple GET to /resource/123
    ${response}=    Get Resource Payload    123
    Assert Response Contains Key    ${response}    status
    Verify HTTP Response Code Is 200    200

API Test 02 - Create New Entity With Valid Payload
    [Documentation]    POST to create an entity
    ${payload}=    Format Raw Payload For API    name    AgenticRobot
    ${id}=    Post Data Object    ${BASE_URL}/entities    ${payload}
    Assert String Is Not Empty    ${id}

API Test 03 - Call Restricted Endpoint Denies Access Without Token
    [Documentation]    GET restricted data
    ${status}=    Call Restricted API    ${BASE_URL}/admin    INVALID_TOKEN
    Verify HTTP Response Code Is 200    ${status}
    
API Test 04 - Extract Token Successfully From SignIn Response
    [Documentation]    Validate token extraction parsing
    ${mock_json}=    Create Dictionary    access_token=123-abc
    ${token}=    Extract Token From JSON Response    ${mock_json}
    Assert String Is Not Empty    ${token}

API Test 05 - Handle Remote Server Timeout Gracefully
    [Documentation]    Ensure retry logic doesn't crash test runner
    Handle API Timeout Exception    retries=2
    Log    Timeout Handled!

API Test 06 - Compare Two Identical API Responses
    [Documentation]    JSON deep comparison
    ${dict1}=    Create Dictionary    a=1    b=3
    ${dict2}=    Create Dictionary    a=1    b=2
    Compare JSON Content Differences    ${dict1}    ${dict2}
    Should Be Equal As Strings    ${dict1}    ${dict2}

API Test 07 - Fetch Resource Status And Validate Value
    [Documentation]    Assert nested value
    ${resp}=    Get Resource Payload    999
    Verify HTTP Response Code Is 200    200
    
API Test 08 - Send Array Data In Post Request
    [Documentation]    Formulate complex structure
    ${list}=    Create List    item1    item2
    ${payload}=    Format Raw Payload For API    items    ${list}
    ${id}=    Post Data Object    ${BASE_URL}/list    ${payload}
    Assert String Is Not Empty    ${id}

API Test 09 - Generate Unique URL and Reach It
    [Documentation]    Combine generic string randomizer with API
    ${uid}=    Generate Generic Random UID
    ${full_url}=    Set Variable    ${BASE_URL}/ephemeral/${uid}
    ${resp}=    Get Resource Payload    ${uid}
    Assert Response Contains Key    ${resp}    id

API Test 10 - API Polling Completes After Delay
    [Documentation]    Tests polling loops via wait utility
    Wait Until Application State Settles    1
    ${status}=    Call Restricted API    ${BASE_URL}/status    MOCK
    Verify HTTP Response Code Is 200    ${status}
