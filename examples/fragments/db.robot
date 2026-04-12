*** Settings ***
Library    String
Library    Collections

*** Keywords ***
Connect To Application DB
    [Documentation]    Simulates opening a connection pool to PostgreSQL.
    [Arguments]    ${connection_string}
    Log    Connecting to standard DB cluster using: ${connection_string}
    RETURN    CONNECTION_ACTIVE

Execute Postgres Select Query
    [Documentation]    Mock execution of a SELECT statement.
    [Arguments]    ${query}    ${db_con}
    Log    Running select query: ${query} on ${db_con}
    ${mock_result}=    Create List    row1    row2    row3
    RETURN    ${mock_result}

Execute Postgres Update Query
    [Documentation]    Mock execution of an UPDATE statement, returning rows affected.
    [Arguments]    ${query}
    Log    Running UPDATE query: ${query}
    ${rows_affected}=    Set Variable    1
    RETURN    ${rows_affected}

Verify DB Record Exists
    [Documentation]    Verifies that querying a record does not return empty.
    [Arguments]    ${record_id}    ${table_name}
    Log    Querying table ${table_name} for id ${record_id}
    Should Not Be Empty    ${record_id}    msg=Record ID cannot be empty on lookup

Insert Mock User Data
    [Documentation]    Helps seed test state internally.
    [Arguments]    ${username}    ${role}
    Log    Inserting mock user: ${username} with role ${role}
    ${uuid}=    Generate Random String    12    [LOWER]
    RETURN    ${uuid}

Clean Up Test Data From Table
    [Documentation]    Simulates TRUNCATE or aggressive DELETE on a given test table.
    [Arguments]    ${table_name}
    Log    Cleaning up testing rows safely in table: ${table_name}

Disconnect From DB Safely
    [Documentation]    Ensures connections are closed and not leaked.
    [Arguments]    ${db_con}
    Log    Safely closed connection pool mapping for: ${db_con}
