*** Settings ***
Library    String

*** Keywords ***
Launch Web Application Dummy
    [Documentation]    Opens dummy browser interface for UI testing.
    [Arguments]    ${url}    ${browser}=chrome
    Log    Opening browser: ${browser} targeted at URL: ${url}

Perform Admin Login
    [Documentation]    Simulates UI actions for filling admin login.
    [Arguments]    ${username}    ${password}
    Log    Filling username textbox with: ${username}
    Log    Filling password textbox with: ${password}
    Log    Clicking Login Button

Navigate To Admin Dashboard
    [Documentation]    Simulates clicking layout links to arrive at destination.
    Log    Clicking left navigation panel.
    Log    Selecting 'Admin Dashboard'
    Sleep    0.5s
    Log    Dashboard loaded.

Fill And Submit Creation Form
    [Documentation]    Types randomly generated form payloads into UI.
    [Arguments]    ${entity_name}    ${entity_type}
    Log    Typing Name: ${entity_name}
    Log    Selecting Dropdown Type: ${entity_type}
    Log    Clicking Submit

Verify Success Toaster Visible
    [Documentation]    Asserts that the green success message popup appeared.
    [Arguments]    ${expected_message}
    Log    Checking for toaster visibility...
    Log    Found Toaster. Message reads: ${expected_message}

Capture Screenshot On Failure Dummy
    [Documentation]    Called normally on test teardown if UI test failed.
    Log    [MOCK] Screenshot Captured: /tmp/mock_screenshot_123.png

Close Client Web Session
    [Documentation]    Kills the browser webdriver session.
    Log    Browser closed cleanly.
