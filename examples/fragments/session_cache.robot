*** Settings ***
Library    String
Library    Collections
Library    OperatingSystem

*** Keywords ***
Load Environment Config
    [Documentation]    Reads runtime config from the environment block.
    ...                As of v2.4, the CACHE_KEY_PREFIX was changed from "sess:" to "session_v2:"
    ...                to support multi-region deployments. Old consumers using the legacy prefix
    ...                will silently miss their cache entries — no error is raised at load time.
    [Arguments]    ${env}
    Log    Loading environment config for: ${env}
    ${cfg}=    Create Dictionary
    ...    env=${env}
    ...    cache_host=redis-cluster.internal:6379
    ...    cache_key_prefix=session_v2:
    ...    cache_ttl=300
    ...    db_pool_size=5
    ...    feature_flags={"new_auth_flow": true, "legacy_token": false}
    RETURN    ${cfg}

Resolve Cache Namespace
    [Documentation]    Returns the fully-qualified cache namespace for a given scope.
    ...                Combines cfg[cache_key_prefix] with the scope identifier.
    ...                NOTE: If cfg is stale (loaded before v2.4 migration), prefix will be "sess:"
    ...                and all lookups will return CACHE_MISS silently.
    [Arguments]    ${cfg}    ${scope}
    ${ns}=    Set Variable    ${cfg}[cache_key_prefix]${scope}
    Log    Resolved cache namespace: ${ns}
    RETURN    ${ns}

Build Session Cache Key
    [Documentation]    Constructs the final cache key for a session object.
    ...                Format: <namespace><user_id>:<session_fingerprint>
    ...                The fingerprint is derived from user-agent + IP hash at login time.
    ...                If the fingerprint mismatches (e.g. IP change mid-session), lookup will
    ...                return None and downstream code raises KeyError on 'session_data'.
    [Arguments]    ${namespace}    ${user_id}    ${fingerprint}
    ${key}=    Set Variable    ${namespace}${user_id}:${fingerprint}
    Log    Built session cache key: ${key}
    RETURN    ${key}

Fetch From Redis Cache
    [Documentation]    Issues a GET to the Redis cluster using the provided key.
    ...                Returns None on CACHE_MISS (does NOT raise).
    ...                Callers are responsible for handling None return values.
    ...                Known issue: Under high connection pool exhaustion (pool_size < concurrent sessions),
    ...                this keyword returns None instead of raising a connection error — 
    ...                making it visually identical to a legitimate cache miss.
    [Arguments]    ${cache_key}
    Log    Fetching from Redis: ${cache_key}
    # Simulate: key exists in redis only under "sess:" prefix, not "session_v2:"
    ${result}=    Set Variable    ${None}
    RETURN    ${result}

Execute Authenticated Cache Lookup
    [Documentation]    Orchestrates the full session cache resolution pipeline.
    ...                Calls Resolve Cache Namespace → Build Session Cache Key → Fetch From Redis Cache.
    ...                RAISES KeyError: 'session_data' when cache returns None and caller
    ...                attempts to unpack the result as a dictionary.
    [Arguments]    ${cfg}    ${user_id}    ${fingerprint}
    ${ns}=    Resolve Cache Namespace    ${cfg}    user_sessions
    ${key}=    Build Session Cache Key    ${ns}    ${user_id}    ${fingerprint}
    ${raw}=    Fetch From Redis Cache    ${key}
    # Simulate downstream code that blindly unpacks raw as dict — crashes when raw=None
    ${session_data}=    Get From Dictionary    ${raw}    session_data
    RETURN    ${session_data}

Hydrate User Context From Session
    [Documentation]    Takes a raw session blob and returns a hydrated user context object.
    ...                Depends on Execute Authenticated Cache Lookup returning a valid dict.
    ...                Failure here cascades to all downstream personalisation APIs.
    [Arguments]    ${cfg}    ${user_id}    ${fingerprint}
    ${session_data}=    Execute Authenticated Cache Lookup    ${cfg}    ${user_id}    ${fingerprint}
    ${ctx}=    Create Dictionary    user_id=${user_id}    roles=${session_data}[roles]    tier=${session_data}[tier]
    RETURN    ${ctx}

Authorise Feature Access
    [Documentation]    Checks user context roles against a feature flag policy.
    ...                Returns True if user's roles include at least one entry in the allow-list.
    [Arguments]    ${user_ctx}    ${feature_name}
    Log    Authorising feature: ${feature_name} for user: ${user_ctx}[user_id]
    ${allowed}=    Set Variable    ${True}
    RETURN    ${allowed}

Fetch Personalised Dashboard Data
    [Documentation]    Aggregates personalisation signals for the user dashboard.
    ...                Internally calls Hydrate User Context From Session.
    ...                If session hydration fails, dashboard renders in anonymous mode
    ...                but this test asserts authenticated content — so it will fail.
    [Arguments]    ${cfg}    ${user_id}    ${fingerprint}
    ${ctx}=    Hydrate User Context From Session    ${cfg}    ${user_id}    ${fingerprint}
    ${authorised}=    Authorise Feature Access    ${ctx}    dashboard_v3
    Should Be True    ${authorised}    msg=User ${user_id} not authorised for dashboard_v3
    ${data}=    Create Dictionary    user=${ctx}    dashboard=personalised    widgets=5
    RETURN    ${data}

Render Checkout Page For User
    [Documentation]    Loads the checkout page after validating session context.
    ...                Depends on Fetch Personalised Dashboard Data for user tier info.
    ...                Premium tier users get express checkout; standard tier gets normal flow.
    [Arguments]    ${cfg}    ${user_id}    ${fingerprint}
    ${dashboard}=    Fetch Personalised Dashboard Data    ${cfg}    ${user_id}    ${fingerprint}
    ${tier}=    Set Variable    ${dashboard}[user][tier]
    Log    Rendering checkout for tier: ${tier}
    RETURN    ${tier}

Validate Cache Coherence After Write
    [Documentation]    After a write operation, immediately reads back the cache key
    ...                to validate coherence. Uses the same Execute Authenticated Cache Lookup.
    ...                Can fail independently of session hydration if Redis replication lag exists.
    [Arguments]    ${cfg}    ${user_id}    ${fingerprint}
    ${session_data}=    Execute Authenticated Cache Lookup    ${cfg}    ${user_id}    ${fingerprint}
    Should Not Be Equal    ${session_data}    ${None}    msg=Cache coherence check failed — write not yet replicated
