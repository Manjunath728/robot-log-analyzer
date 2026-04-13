*** Settings ***
Resource    ../main.robot

*** Test Cases ***
PAY-01 - Full Payment Flow With Valid Merchant And Card
    [Documentation]    End-to-end happy path: merchant session → payment → settlement verify
    [Tags]    payment    e2e    critical
    ${session}=    Initialise Payment Gateway Session    MERCHANT_001
    ${txn_id}=    Submit Payment Request    ${session}    99.99    USD    CARD-REF-4242
    Verify Payment Transaction Status    ${txn_id}
    Assert No Duplicate Transaction Exists    ${txn_id}

PAY-02 - Refund Settled Transaction Successfully
    [Documentation]    Verifies full refund can be issued after settlement.
    [Tags]    payment    refund    regression
    ${session}=    Initialise Payment Gateway Session    MERCHANT_002
    ${txn_id}=    Submit Payment Request    ${session}    249.00    USD    CARD-REF-5353
    Verify Payment Transaction Status    ${txn_id}
    ${refund_id}=    Refund Payment Transaction    ${session}    ${txn_id}
    Should Not Be Empty    ${refund_id}

PAY-03 - Expired Session Token Causes Signature Rejection At Gateway
    [Documentation]    Simulates an expired/stale session token scenario.
    ...                The HMAC signature created with the stale token will be rejected
    ...                by the downstream gateway with HTTP 401 Unauthorized.
    ...                Root cause is session token TTL expiry from Acquire Gateway Session Token —
    ...                but the surface failure appears at Dispatch Signed Payment.
    [Tags]    payment    auth    negative    context-depth-test
    ${session}=    Initialise Payment Gateway Session    MERCHANT_EXPIRED
    # Simulates token going stale mid-flow (e.g. clock skew or long-running test)
    ${stale_token}=    Set Variable    EXPIRED_TOKEN_abc123
    ${txn_id}=    Submit Payment Request    ${stale_token}    500.00    USD    CARD-REF-9999
    Verify Payment Transaction Status    ${txn_id}

PAY-04 - Duplicate Transaction Idempotency Check Fails Under Load
    [Documentation]    When the same txn_id is re-submitted under load, the idempotency
    ...                guard should catch it. This test verifies the ledger check works.
    [Tags]    payment    idempotency    load    context-depth-test
    ${session}=    Initialise Payment Gateway Session    MERCHANT_003
    ${txn_id}=    Submit Payment Request    ${session}    75.00    USD    CARD-REF-1111
    Assert No Duplicate Transaction Exists    ${txn_id}
    # Simulate a re-submission of the same txn (would normally come from a retry storm)
    Assert No Duplicate Transaction Exists    ${txn_id}
