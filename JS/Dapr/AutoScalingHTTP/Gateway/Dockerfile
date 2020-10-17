FROM node:latest

WORKDIR /usr/src/app

# Install deps
RUN apt-get update

# 1. Install Package.json dependendencies
# Note: Same docker layer, to keep re-chowned files from using up several hundred MBs more space
COPY package.json .
RUN npm install

# Copy Source Code
COPY . /usr/src/app

# Install the App
RUN npm run build

CMD [ "npm", "run", "start" ]
EXPOSE 5000 5001