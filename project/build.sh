set -euo pipefail
python -m pip install -r requirements-render.txt
npm ci
npm run build
python manage.py collectstatic --noinput
python manage.py migrate --noinput