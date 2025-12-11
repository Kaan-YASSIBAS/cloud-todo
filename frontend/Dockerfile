FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html
COPY . /usr/share/nginx/html

# Allow OpenShift compatible permissions + change the port in default.conf from 80 to 8080.
RUN mkdir -p /var/cache/nginx /var/run /var/log/nginx /var/tmp && \
    chgrp -R 0 /var/cache/nginx /var/run /var/log/nginx /var/tmp /etc/nginx && \
    chmod -R g+rwX /var/cache/nginx /var/run /var/log/nginx /var/tmp /etc/nginx && \
    sed -i 's/listen[[:space:]]\+80;/listen 8080;/' /etc/nginx/conf.d/default.conf && \
    sed -i 's/listen[[:space:]]\+\[::\]:80;/listen [::]:8080;/' /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
