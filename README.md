# Transcendence – A Multiplayer Pong Game with Microservices Architecture

Transcendence is a fully functional online multiplayer Pong game built using a **microservices architecture**. The project was developed over 1.5 months as part of an intensive learning experience, focusing on modern backend and frontend technologies.

## Key Features & Tech Stack

- **Microservices Backend**: Built using **Django**, **PostgreSQL**, **NGINX**, **Redis** structured as independent Docker containers for scalability and modularity.
- **Real-time Gameplay**: Game logic is handled server-side, with **WebSockets** enabling smooth multiplayer interaction. Players can also challenge an **AI opponent**.
- **User Management & Authentication**: A dedicated authentication service ensures secure user registration, login, and session management.
- **Frontend SPA**: A lightweight **JavaScript** single-page application (SPA) with a retro Pong design, styled with **Bootstrap**.

## Challenges & Learning Experience

Before this project, we had little to no experience with **Django, microservices, or SPAs**, but we took on the challenge and delivered a working product. Along the way, we learned how to:

- Design and orchestrate **microservices** using **Docker**.
- Implement **real-time multiplayer logic** with WebSockets.
- Structure a **RESTful API** for game and user management.
- Build and deploy a **scalable web application**.

The code isn't perfect, and there are still improvements to be made, but this project marks a significant milestone in our growth as developers. We’re excited to keep refining our skills and tackling even bigger challenges in the future! 🚀

## ⚙️ Running the Project

### 1. Setup
This project requires a .env file containing credentials necessary to run it. For security this file cannot be shared, but here is an example fo how you can create your own:

```py
#Redis
REDIS_PASS=your_redis_password

#DB
POSTGRES_DB=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password

SECRET_KEY=your_django_secret_key
```

 💡 Due to security reasons the 42 API will NOT be available with this .env file.

 If you are a 42 student and have access to an API key you can enable it by adding the following fields:

 ```py
 #42 API

CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

### 2. Build

The project runs on docker, so make sure you have it installed. Then at the project root folder execute:
```sh
make
```

once the containersa are running, you can access the page at:
```link
https://localhost
```

