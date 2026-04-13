*** Settings ***
Resource    ../main.robot

*** Test Cases ***
CACHE-01 - Dashboard Loads With Valid Session For Premium User
    [Documentation]    Happy path: premium user session exists in cache, dashboard renders.
    [Tags]    cache    session    e2e    premium
    ${cfg}=    Load Environment Config    prod
    ${data}=    Fetch Personalised Dashboard Data    ${cfg}    USER_PREM_001    fp:ab12cd
    Should Not Be Empty    ${data}

CACHE-02 - Checkout Page Renders With Correct Tier For Premium User
    [Documentation]    Validates checkout tier resolution for premium users.
    [Tags]    cache    checkout    regression    context-depth-test
    ${cfg}=    Load Environment Config    prod
    ${tier}=    Render Checkout Page For User    ${cfg}    USER_PREM_002    fp:xy99zz
    Should Be Equal As Strings    ${tier}    premium

CACHE-03 - Session Hydration Fails Due To Cache Miss On Migrated Key Prefix
    [Documentation]    Reproduces the production incident SRE-2041.
    ...                After the v2.4 deployment, CACHE_KEY_PREFIX changed from "sess:" to "session_v2:".
    ...                Legacy sessions stored under "sess:" are invisible to the new prefix.
    ...                The failure manifests as KeyError: 'session_data' in Execute Authenticated Cache Lookup
    ...                because Fetch From Redis Cache silently returns None on a CACHE_MISS.
    ...                The actual root cause is NOT the session being missing — it is the config migration
    ...                that was applied without a Redis key backfill strategy.
    [Tags]    cache    session    regression    incident    context-depth-test    rag-confuser
    ${cfg}=    Load Environment Config    prod
    ${data}=    Fetch Personalised Dashboard Data    ${cfg}    USER_LEGACY_003    fp:dead00beef

CACHE-04 - Cache Coherence Validation Races Redis Replication Lag
    [Documentation]    After a session write, the coherence check immediately reads back.
    ...                Under replication lag (> 50ms), the replica the test reads from
    ...                has not yet received the write — returns None → assertion fails.
    ...                Root cause is NOT the write failing — it is the test using a non-primary read node.
    [Tags]    cache    coherence    flaky    context-depth-test    rag-confuser
    ${cfg}=    Load Environment Config    staging
    Validate Cache Coherence After Write    ${cfg}    USER_NEW_004    fp:11223344
