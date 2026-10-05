First-time setup

1. Go into the app folder:
2. cd /workspaces/group3-fall2026/project

2. Install the Python packages:
3. pip install -r requirements.txt

3. Install the JavaScript packages:
4. npm install

4. Build the JavaScript the pages load:
5. npm run build

5. Set up the database:
6. python manage.py migrate

6. Create an admin account. This is optional, and only needed for /admin:
7. python manage.py createsuperuser

Set up Ollama (required for missions)

Missions are written by an AI model that runs through Ollama. Without Ollama there are no missions, and the practice page just says "No mission available".

7. Install Ollama (about 1 minute):
8. curl -fsSL https://ollama.com/install.sh | sh

8. Start Ollama in the background:
9. ollama serve > /tmp/ollama.log 2>&1 &

9. Download the AI model (about 800 MB, a few minutes):
10. ollama pull gemma3:1b

10. Create a mission. The topic in quotes is optional. This can take a minute because Codespaces has no GPU:
11. python manage.py generate_mission "if statements"
12. It prints something like Created mission 1: Shortcut Troubles. Run it again any time you want a new mission; the page always shows the newest one.

Start the app

11. Start the server:
12. python manage.py runserver 0.0.0.0:8000
