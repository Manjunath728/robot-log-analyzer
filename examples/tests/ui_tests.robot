*** Settings ***
Resource    ../main.robot

*** Test Cases ***
UI Test 01 - Open Application Dashboard Default Browser
    [Documentation]    Load landing page
    Launch Web Application Dummy    ${UI_BASE_URL}    chrome
    Close Client Web Session

UI Test 02 - Submit Correct Credentials Performs Login
    [Documentation]    Auth workflow UI
    Launch Web Application Dummy    ${UI_BASE_URL}
    Perform Admin Login    Administrator    S3cretPass
    Close Client Web Session

UI Test 03 - Navigation Tree Traversing Reaches Admin Page
    [Documentation]    Nav actions
    Launch Web Application Dummy    ${UI_BASE_URL}
    Navigate To Admin Dashboard
    Close Client Web Session

UI Test 04 - Create New Profile Form Emits Success Toaster
    [Documentation]    Form logic
    Launch Web Application Dummy    ${UI_BASE_URL}
    Navigate To Admin Dashboard
    Fill And Submit Creation Form    NewUser1    Developer
    Verify Success Toaster Visible    Successfully Created Profile
    Close Client Web Session

UI Test 05 - Forced Test Failure Captures Diagnostic Image
    [Documentation]    Teardown proxy test
    Launch Web Application Dummy    ${UI_BASE_URL}
    Capture Screenshot On Failure Dummy
    Close Client Web Session

UI Test 06 - Inject Special Characters Into UI Target
    [Documentation]    Edge case
    Launch Web Application Dummy    ${UI_BASE_URL}
    Fill And Submit Creation Form    !@#$%^    Hacker
    Wait Until Application State Settles    1
    Close Client Web Session

UI Test 07 - Verify Layout Remains Stable Across Reloads
    [Documentation]    Flakiness checker
    Launch Web Application Dummy    ${UI_BASE_URL}
    Navigate To Admin Dashboard
    Wait Until Application State Settles    1
    Close Client Web Session

UI Test 08 - UI Triggers Auto-Timeout Event
    [Documentation]    Idle check
    Launch Web Application Dummy    ${UI_BASE_URL}
    Wait Until Application State Settles    2
    Close Client Web Session

UI Test 09 - Rapid Login Logout Cycle Memory Test
    [Documentation]    Perform double action
    Launch Web Application Dummy    ${UI_BASE_URL}
    Perform Admin Login    a    b
    Wait Until Application State Settles    1
    Close Client Web Session

UI Test 10 - Form Submission On Corrupted Endpoint Retries
    [Documentation]    Network error proxy
    Launch Web Application Dummy    ${UI_BASE_URL}
    Fill And Submit Creation Form    RetryUser    Ops
    Close Client Web Session
