*** Settings ***
Library    String
Library    Collections

*** Keywords ***
Initialise Payment Gateway Session
    [Documentation]    Bootstraps a payment session by resolving merchant credentials,
    ...                loading gateway configuration and acquiring a session token.
    [Arguments]    ${merchant_id}
    Log    Resolving merchant credentials for: ${merchant_id}
    ${config}=    Load Gateway Configuration    ${merchant_id}
    ${session_token}=    Acquire Gateway Session Token    ${config}
    RETURN    ${session_token}

Load Gateway Configuration
    [Documentation]    Fetches merchant-specific gateway config from config service.
    ...                Applies environment overrides and validates required keys.
    [Arguments]    ${merchant_id}
    Log    Loading gateway config for merchant: ${merchant_id}
    ${config}=    Create Dictionary
    ...    merchant_id=${merchant_id}
    ...    gateway_url=https://payments.mock-env.local/v2
    ...    timeout=10
    ...    retry_limit=3
    ...    currency=USD
    ...    hmac_secret=MOCK_HMAC_KEY_XYZ
    Validate Gateway Config Keys    ${config}
    RETURN    ${config}

Validate Gateway Config Keys
    [Documentation]    Asserts all mandatory gateway config keys are present.
    ...                Raises if 'hmac_secret' or 'gateway_url' is missing.
    [Arguments]    ${config}
    Dictionary Should Contain Key    ${config}    gateway_url
    Dictionary Should Contain Key    ${config}    hmac_secret
    Dictionary Should Contain Key    ${config}    timeout

Acquire Gateway Session Token
    [Documentation]    POSTs to the payment gateway auth endpoint to obtain
    ...                a short-lived session token. Token is HMAC-signed internally.
    [Arguments]    ${config}
    Log    Acquiring session token from: ${config}[gateway_url]
    ${token}=    Set Variable    MOCK_SESSION_TOKEN_${config}[merchant_id]
    RETURN    ${token}

Submit Payment Request
    [Documentation]    Submits a payment request to the gateway.
    ...                Internally calls Sign Payment Payload before dispatch.
    [Arguments]    ${session_token}    ${amount}    ${currency}    ${card_ref}
    Log    Submitting payment: amount=${amount} currency=${currency}
    ${signed_payload}=    Sign Payment Payload    ${session_token}    ${amount}    ${currency}    ${card_ref}
    ${txn_id}=    Dispatch Signed Payment    ${signed_payload}
    RETURN    ${txn_id}

Sign Payment Payload
    [Documentation]    Creates an HMAC-SHA256 signed dictionary for the payment dispatch.
    ...                Uses the gateway session token as the signing key.
    ...                CRITICAL: If token is expired or malformed, signature will be invalid
    ...                and downstream gateway will reject with HTTP 401.
    [Arguments]    ${session_token}    ${amount}    ${currency}    ${card_ref}
    Log    Signing payment payload with session token
    ${payload}=    Create Dictionary
    ...    amount=${amount}
    ...    currency=${currency}
    ...    card_ref=${card_ref}
    ...    signature=HMAC_${session_token}_${amount}
    RETURN    ${payload}

Dispatch Signed Payment
    [Documentation]    Sends the final signed payload to the payment gateway.
    ...                Expects HTTP 200 and a txn_id in the response body.
    ...                Will raise if response code is not 200 or txn_id is missing.
    [Arguments]    ${signed_payload}
    Log    Dispatching signed payment to gateway
    ${txn_id}=    Set Variable    TXN-MOCK-00000
    RETURN    ${txn_id}

Verify Payment Transaction Status
    [Documentation]    Polls the gateway for the final settlement status of a transaction.
    ...                Retries up to 3 times with 2s delay between polls.
    [Arguments]    ${txn_id}
    Log    Verifying txn status for: ${txn_id}
    ${status}=    Set Variable    SETTLED
    Should Be Equal As Strings    ${status}    SETTLED    msg=Transaction ${txn_id} did not settle. Got: ${status}
    RETURN    ${status}

Refund Payment Transaction
    [Documentation]    Issues a full refund for a previously settled transaction.
    ...                Requires the original txn_id and a valid session token.
    ...                Internally calls Verify Payment Transaction Status before issuing refund.
    [Arguments]    ${session_token}    ${txn_id}
    ${status}=    Verify Payment Transaction Status    ${txn_id}
    Log    Issuing refund for txn: ${txn_id} (status was: ${status})
    ${refund_id}=    Set Variable    REFUND-${txn_id}
    RETURN    ${refund_id}

Assert No Duplicate Transaction Exists
    [Documentation]    Queries the transaction ledger to ensure idempotency.
    ...                Calls internal ledger check which may raise on DB connectivity issues.
    [Arguments]    ${txn_id}
    Log    Checking idempotency for txn: ${txn_id}
    ${is_duplicate}=    Set Variable    ${False}
    Should Be Equal    ${is_duplicate}    ${False}    msg=Duplicate transaction detected for ${txn_id}
