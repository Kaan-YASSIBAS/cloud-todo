FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html

# Statik files
COPY index.html .
COPY dashboard.html .

COPY styles.css .
COPY login.css .
COPY dashboard.css .

COPY main.js .
COPY dashboard.js .

COPY assets ./assets

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
