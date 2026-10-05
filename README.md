Go into the app folder

cd /workspaces/group3-fall2026/project
If this says "No such file or directory", project/ isn't on GitHub yet. Stop here and do the push steps from my earlier message on your Mac first.

Install the Python packages

pip install -r requirements.txt
Install the JavaScript packages

npm install
Build the JavaScript the pages load

npm run build
Set up the database

python manage.py migrate
Create an admin account

python manage.py createsuperuser
Install Ollama (about 1 minute):
curl -fsSL https://ollama.com/install.sh | sh
Start Ollama in the background:
ollama serve > /tmp/ollama.log 2>&1 &
Download the AI model (about 800 MB, a few minutes):
ollama pull gemma3:1b
Create a mission. The topic in quotes is optional, and this can take a minute because the Codespace has no GPU:
cd /workspaces/group3-fall2026/project && python manage.py generate_mission "if statements"
you dont get any missions and you cant use punch if you dont install ollama
