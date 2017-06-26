# Core NGINX

The core nginx is responsible for rerouting the various components from the public facing nginx to the appropriate containers. There is currently a unknown behavior where after turning the VM off and bringing it back on, the core nginx fails to reroute to the appropriate services. To quickly fix this, you can do `sudo docker start core-config-gen` to regenerate the config file for the core nginx. 

This group of services is based on:

https://github.com/jwilder/nginx-proxy
https://github.com/JrCs/docker-letsencrypt-nginx-proxy-companion
