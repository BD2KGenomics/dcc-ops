FROM nginx:alpine
RUN apk add --update bash 

COPY start.sh /
COPY nginx.conf /etc/nginx/
COPY nginx-secure.conf /etc/nginx/
RUN chmod +x /start.sh
CMD ./start.sh

