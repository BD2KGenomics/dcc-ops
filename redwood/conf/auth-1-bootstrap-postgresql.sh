#!/usr/bin/env bash

psql <<EOF
-- Copyright (c) 2012-2014 The Ontario Institute for Cancer Research. All rights reserved.
--
-- Script to create the SQL schema for the dcc-auth server

DROP DATABASE IF EXISTS ${AUTH_DB};
DROP USER IF EXISTS ${AUTH_DB_USERNAME};

CREATE DATABASE ${AUTH_DB};
\connect ${AUTH_DB};
CREATE USER ${AUTH_DB_USERNAME} WITH PASSWORD '${AUTH_DB_PASSWORD}';

CREATE TABLE IF NOT EXISTS oauth_client_details (
  client_id VARCHAR(256) PRIMARY KEY,
  resource_ids VARCHAR(256),
  client_secret VARCHAR(256),
  scope VARCHAR(256),
  authorized_grant_types VARCHAR(256),
  web_server_redirect_uri VARCHAR(256),
  authorities VARCHAR(256),
  access_token_validity INTEGER,
  refresh_token_validity INTEGER,
  additional_information VARCHAR(4096),
  autoapprove VARCHAR(256)
);

CREATE TABLE IF NOT EXISTS oauth_client_token (
  token_id VARCHAR(256),
  token BYTEA,
  authentication_id VARCHAR(256),
  user_name VARCHAR(256),
  client_id VARCHAR(256)
);

CREATE TABLE IF NOT EXISTS oauth_access_token (
  token_id VARCHAR(256),
  token BYTEA,
  authentication_id VARCHAR(256),
  user_name VARCHAR(256),
  client_id VARCHAR(256),
  authentication BYTEA,
  refresh_token VARCHAR(256),
  deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS oauth_refresh_token (
  token_id VARCHAR(256),
  token BYTEA,
  authentication BYTEA
);

CREATE TABLE IF NOT EXISTS oauth_code (
  code VARCHAR(256), authentication BYTEA
);

CREATE TABLE IF NOT EXISTS oauth_approvals (
  userId VARCHAR(256),
  clientId VARCHAR(256),
  scope VARCHAR(256),
  status VARCHAR(10),
  expiresAt TIMESTAMP,
  lastModifiedAt TIMESTAMP
);


-- customized oauth_client_details table
CREATE TABLE IF NOT EXISTS ClientDetails (
  appId VARCHAR(256) PRIMARY KEY,
  resourceIds VARCHAR(256),
  appSecret VARCHAR(256),
  scope VARCHAR(256),
  grantTypes VARCHAR(256),
  redirectUrl VARCHAR(256),
  authorities VARCHAR(256),
  access_token_validity INTEGER,
  refresh_token_validity INTEGER,
  additionalInformation VARCHAR(4096),
  autoApproveScopes VARCHAR(256)
);

create table if not exists users(
        username varchar(50) not null primary key,
        password varchar(120) not null,
        enabled boolean not null
);

create table if not exists authorities (
        username varchar(50) not null,
        authority varchar(50) not null,
        constraint fk_authorities_users foreign key(username) references users(username)
);
create unique index ix_auth_username on authorities (username,authority);

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dcc_auth;

-- Populate tables
INSERT INTO users (username, password, enabled) VALUES ('mgmt', '${MGMT_CLIENT_SECRET}', true);
INSERT INTO authorities (username, authority) VALUES ('mgmt', 'ROLE_MANAGEMENT');

INSERT INTO oauth_client_details (client_id, resource_ids, client_secret, scope, authorized_grant_types, web_server_redirect_uri, authorities, access_token_validity, refresh_token_validity, additional_information, autoapprove) VALUES ('mgmt', '', '${MGMT_CLIENT_SECRET}', 'aws.DEV.upload,aws.DEV.download,aws.TEST.upload,aws.TEST.download,aws.upload,aws.download', 'password', '', 'ROLE_MANAGEMENT', 31536000, NULL, '{}', '');
-- INSERT INTO oauth_client_details (client_id, resource_ids, client_secret, scope, authorized_grant_types, web_server_redirect_uri, authorities, access_token_validity, refresh_token_validity, additional_information, autoapprove) VALUES ('resource', '', 'pass', 'deny_resource_servers_to_generate_tokens_with_valid_scope', '', '', 'ROLE_RESOURCE', 0, NULL, '{}', '');
INSERT INTO oauth_client_details (client_id, resource_ids, client_secret, scope, authorized_grant_types, web_server_redirect_uri, authorities, access_token_validity, refresh_token_validity, additional_information, autoapprove) VALUES ('storage', '', '${STORAGE_CLIENT_SECRET}', 'deny_resource_servers_to_generate_tokens_with_valid_scope', '', '', 'ROLE_RESOURCE', 0, NULL, '{}', '');
INSERT INTO oauth_client_details (client_id, resource_ids, client_secret, scope, authorized_grant_types, web_server_redirect_uri, authorities, access_token_validity, refresh_token_validity, additional_information, autoapprove) VALUES ('metadata', '', '${METADATA_CLIENT_SECRET}', 'deny_resource_servers_to_generate_tokens_with_valid_scope', '', '', 'ROLE_RESOURCE', 0, NULL, '{}', '');
-- INSERT INTO oauth_client_details (client_id, resource_ids, client_secret, scope, authorized_grant_types, web_server_redirect_uri, authorities, access_token_validity, refresh_token_validity, additional_information, autoapprove) VALUES ('id', '', 'pass', 'deny_resource_servers_to_generate_tokens_with_valid_scope', '', '', 'ROLE_RESOURCE', 0, NULL, '{}', '');
EOF
