# Cinnamon 🍂

> A Django-based social network for sharing culinary recipes, building friendships, and joining thematic communities.

## Features

- **User Profiles** — Public/private profiles with bio, cuisine specialties, experience level, location and social links.
- **Friendship System** — Send, accept and reject friend requests; bidiretional friendship model.
- **Recipes** — Create, edit and delete recipes with images, ingredients, instructions, tags and three visibility levels (public / friends-only / private).
- **Like & Comment System** — Toggle likes and threaded comments on recipes.
- **Private Communities** — Create public or invite-only communities with Reddit-style post voting (upvote/downvote), moderation tools, and join-request management.
- **Private Messaging** — Conversation-based direct messaging between friends.
- **Notifications** — In-app notifications for community invites and join requests.
- **User Search** — Find other users by username, bio, experience level and cuisine specialty.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10 + Django 5.2.7 |
| Database | SQLite (development) |
| Frontend | Bootstrap 5 + HTML5 |
| Forms | django-crispy-forms 1.14.0 |
| Images | Pillow 11.2.1 |
| Dependencies | pip / pipenv |

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/cinnamon.git
cd cinnamon
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install dependencies

With pip:
```bash
pip install -r requirements.txt
```

Or with pipenv:
```bash
pipenv install
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. (Optional) Create a superuser for the admin panel

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.  
The admin panel is at `http://127.0.0.1:8000/admin/`.

## Environment Variables

For production deployments, set the following environment variable:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key (required in production) |

For local development the app uses a built-in fallback key — **never use the fallback in production**.

## Project Structure

```
cinnamon/
├── config/             # Django project settings, URLs, WSGI/ASGI
├── users/              # User profiles, friendships, notifications
├── recipes/            # Recipes, likes, comments
├── community/          # Communities, posts, voting, moderation, invites
├── user_messages/      # Private conversations and messages
├── manage.py
├── requirements.txt
└── Pipfile
```

## Running Tests

Run the full test suite:

```bash
python manage.py test users recipes community
```

Run tests for a single app:

```bash
python manage.py test users
python manage.py test recipes
python manage.py test community
```

The test suite covers:

- **users** — `FriendRequest`, `Friendship` and `UserProfile` models; public/private profile access via test client.
- **recipes** — Home page visibility rules (anonymous/authenticated/friends); `toggle_like` endpoint behaviour.
- **community** — `CommunityDetailView` access (public/private, member/moderator/friend); join/leave consistency and idempotency.

## Screenshots

### Home page
![Home page](/docs/screenshots/homepage.png)

### Home page with login prompt
![Home page – login prompt](/docs/screenshots/home_login.png)

### Login
![Login](/docs/screenshots/login.png)

### Community
![Community](/docs/screenshots/community.png)

### Users
![Users](/docs/screenshots/users.png)

## Architecture

For a detailed description of the data model, use-case diagram, architectural decisions and technology choices, see [ARCHITECTURE.md](ARCHITECTURE.md).

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
