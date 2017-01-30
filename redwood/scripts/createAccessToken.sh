#!/bin/bash

user=testuser

docker exec -it redwood-auth-server curl -XPUT http://localhost:8543/admin/scopes/$user -u admin:secret -d"s3.upload s3.download"
docker exec -it redwood-auth-server curl http://localhost:8443/oauth/token -H "Accept: application/json" -dgrant_type=password -dusername=$user -dscope="s3.upload s3.download" -ddesc="test access token" -u mgmt:pass
