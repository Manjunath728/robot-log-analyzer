*** Settings ***
Library    String
Library    Collections
Library    DateTime

*** Keywords ***
Generate Generic Random UID
    [Documentation]    Creates a UUID format like string for test entity names.
    [Arguments]    ${prefix}=TEST_
    ${random_chars}=    Generate Random String    8    [LETTERS][NUMBERS]
    ${uid}=    Catenate    SEPARATOR=    ${prefix}    ${random_chars}
    RETURN    ${uid}

Get Future Evaluated Timestamp
    [Documentation]    Gets a future timestamp based on current time + days offset.
    [Arguments]    ${days_offset}
    ${current}=    Get Current Date
    ${future}=    Add Time To Date    ${current}    ${days_offset} days
    RETURN    ${future}

Compare JSON Content Differences
    [Documentation]    Mocks diffing two json dictionaries.
    [Arguments]    ${dict1}    ${dict2}
    Log    Comparing dictionaries...
    Should Be Equal    ${dict1}    ${dict2}

Format Raw Payload For API
    [Documentation]    Normalizes parameters into JSON format for HTTP libraries.
    [Arguments]    ${key}    ${value}
    ${payload}=    Create Dictionary    ${key}=${value}
    RETURN    ${payload}

Wait Until Application State Settles
    [Documentation]    Pauses test explicitly to let asynchronous message brokers finish.
    [Arguments]    ${seconds_to_wait}=2
    Log    Sleeping for ${seconds_to_wait}s to allow async state to settle
    Sleep    ${seconds_to_wait}s

Read Configuration YAML File
    [Documentation]    Simulates reading an env config block.
    [Arguments]    ${filepath}
    Log    Reading YAML config off disk -> ${filepath}
    ${mock_config}=    Create Dictionary    environment=QA    timeout=30    base_url=http://localhost
    RETURN    ${mock_config}

Assert String Is Not Empty
    [Documentation]    Validate the variable holds data.
    [Arguments]    ${string_var}
    Should Not Be Empty    ${string_var}    msg=Provided string was inexplicably empty.
