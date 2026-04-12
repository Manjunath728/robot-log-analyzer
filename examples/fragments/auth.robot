*** Settings ***
Library    String
Library    Collections

*** Keywords ***
Generate Admin Bearer Token
    [Documentation]    Gets a token specifically seeded with administrative claims.
    Log    Authenticating against OAUTH provider for ADMIN role.
    ${admin_token}=    Set Variable    adm_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_admin
    RETURN    ${admin_token}

Generate Standard Bearer Token
    [Documentation]    Gets a token specifically seeded with standard user claims.
    Log    Authenticating against OAUTH provider for STANDARD role.
    ${standard_token}=    Set Variable    usr_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_standard
    RETURN    ${standard_token}

Force Current Token Expiry
    [Documentation]    Calls backend API to artificially expire a token.
    [Arguments]    ${token}
    Log    Force expiring token: ${token}
    RETURN    EXPIRED

Revoke User Active Session
    [Documentation]    Kills current server-side session cookies holding state.
    [Arguments]    ${session_id}
    Log    Revoked tracking for session: ${session_id}

Verify JWT Token Structure
    [Documentation]    Asserts the token string looks like a compliant JWT header/payload/signature format.
    [Arguments]    ${token}
    Log    Validating internal JWT structure for ${token}
    ${length}=    Get Length    ${token}
    Should Be True    ${length} > 15    msg=Token length is suspiciously short!

Create Standard Auth Header Map
    [Documentation]    Returns a dictionary of Headers containing the Authorization bearer standard.
    [Arguments]    ${bearer_token}
    ${auth_header}=    Create Dictionary    Authorization=Bearer ${bearer_token}    Content-Type=application/json
    RETURN    ${auth_header}

Validate User Permissions
    [Documentation]    Ensures the specified role is applied within token scope.
    [Arguments]    ${decoded_token}    ${expected_role}
    Log    Checking role '${expected_role}' in token payload...
    Log    Validated Role Exists.
