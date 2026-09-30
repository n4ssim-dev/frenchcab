FROM node:24-alpine AS build

WORKDIR /app

# Installation des dépendances
COPY package*.json ./
RUN npm ci

# Copie du code source
COPY . .

# Build Angular en production
RUN npm run build


FROM nginx:alpine

# Supprime la configuration Nginx par défaut
RUN rm /etc/nginx/conf.d/default.conf

# Copie notre configuration Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copie le build Angular
COPY --from=build /app/dist/ms_front /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]