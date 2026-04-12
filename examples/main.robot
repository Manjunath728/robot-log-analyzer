*** Settings ***
Documentation    Main Resource File. This MUST be the ONLY file imported by Test Suites.

Resource    fragments/api.robot
Resource    fragments/db.robot
Resource    fragments/ui.robot
Resource    fragments/auth.robot
Resource    fragments/utils.robot

*** Variables ***
${GLOBAL_TIMEOUT}         30s
${BASE_URL}               http://mock-environment.local
${UI_BASE_URL}            http://mock-frontend.local
${DB_CONNECTION_STRING}   postgres://user:pass@localhost:5432/maindb
