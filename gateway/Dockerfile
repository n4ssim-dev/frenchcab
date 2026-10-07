FROM node:22

WORKDIR /app

RUN apt-get update && apt-get install -y python3 make g++

COPY package*.json ./

RUN npm install
RUN npm rebuild sqlite3 --build-from-source

COPY . .

EXPOSE 3000

CMD ["npm","run","start"]