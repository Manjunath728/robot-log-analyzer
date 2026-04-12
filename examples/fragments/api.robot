*** Settings ***
Library    String
Library    Collections

*** Keywords ***
Call Restricted API
    [Documentation]    Simulates calling a restricted API endpoint.
    [Arguments]    ${endpoint_url}    ${auth_token}
    Log    Calling restricted endpoint: ${endpoint_url} with token: ${auth_token}
    ${status}=    Set Variable    200
    RETURN    ${status}

Get Resource Payload
    [Documentation]    Simulates a GET request to an API endpoint.
    [Arguments]    ${resource_id}
    Log    GET API query for resource ID: ${resource_id}
    ${mock_response}=    Create Dictionary    id=${resource_id}    name=MockComponent    status=active
    RETURN    ${mock_response}

Post Data Object
    [Documentation]    Simulates a POST request to create an object.
    [Arguments]    ${url}    ${payload}
    Log    POST API pushing data to: ${url}
    Log    Payload: ${payload}
    ${mock_id}=    Generate Random String    8    [NUMBERS]
    RETURN    ${mock_id}

Verify HTTP Response Code Is 200
    [Documentation]    Asserts the given response code is strictly 200.
    [Arguments]    ${response_code}
    Should Be Equal As Strings    ${response_code}    200    msg=Expected HTTP 200 but got ${response_code}

Extract Token From JSON Response
    [Documentation]    Simulates extracting an auth token from a complex JSON dump.
    [Arguments]    ${json_response}
    ${token}=    Get From Dictionary    ${json_response}    access_token    default=mock_jwt_token_12345
    RETURN    ${token}

Assert Response Contains Key
    [Documentation]    Verifies that a specified key exists in the JSON response dictionary.
    [Arguments]    ${response_dict}    ${expected_key}
    Dictionary Should Contain Key    ${response_dict}    ${expected_key}

Handle API Timeout Exception
    [Documentation]    Simulates API exception handling behaviour limit retries.
    [Arguments]    ${retries}=3
    Log    Waiting for API responsiveness, retry limit: ${retries}
    Sleep    1s
    Log    API responsiveness stabilized.
