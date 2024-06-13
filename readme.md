
# ReconPlane

A (quick) flyover tool to aid in bugbounty hunting, penetration testing efforts and asset discovery.

What if OpenKAT and rEngine had a bastard lovechild?

## How to run (developer mode)?
```bash

python -m venv venv
source venv/bin/activate

python3 manage.py runserver

docker compose up

celery -A reconplane worker -l INFO --pool=solo

```