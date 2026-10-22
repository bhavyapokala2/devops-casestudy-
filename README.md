# LinkLite — URL Shortener (Week 1)

A beginner-friendly Flask + MongoDB URL shortener with a responsive modern interface, URL validation, copy-to-clipboard buttons, and click tracking.

## Features
- Convert a valid HTTP/HTTPS URL into a short link.
- Validate URLs on the server and show helpful error messages.
- Copy the newly created short link or any link in Recent links.
- Redirect short links to their original destinations.
- Increment a link's click count whenever it is opened.
- Display the latest 10 saved links.
- Unit tests use mocks, so the test suite does not require a live MongoDB server.

## Requirements
- Python 3.10 or newer
- MongoDB Community Server running locally, or a MongoDB Atlas connection string
- MongoDB Compass is a database GUI; it connects to the MongoDB server but is not itself the server.

## Setup on Windows PowerShell
Run these commands from this project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` so it contains your own settings:

```dotenv
MONGO_URI=mongodb://localhost:27017/
DATABASE_NAME=url_shortener
FLASK_SECRET_KEY=replace-this-with-a-random-secret
```

If MongoDB Compass connects to `localhost:27017`, the default URI above should work. Save `.env` beside `app.py`; do not commit it to GitHub.

## Run the app

```powershell
python app.py
```

Open <http://127.0.0.1:5000> in your browser. Paste a URL such as `https://www.google.com`, click **Shorten link**, then test the new link and the Copy buttons. In MongoDB Compass, refresh the connection and open `url_shortener` → `urls` to inspect the saved document and click count.

## Run tests
Open a second terminal in the same folder:

```powershell
python -m unittest discover -s tests -v
```

## Week 1 lab evidence
Capture screenshots of:
1. The modern LinkLite home page.
2. A newly shortened URL and the copy confirmation.
3. A successful redirect and the click count increasing.
4. The `url_shortener.urls` collection in MongoDB Compass.
5. The unit test results in the terminal.

## 9-week DevOps roadmap
1. Build and test this Flask app.
2. Practise Git commands.
3. Push the project to GitHub.
4. Install and configure Jenkins.
5. Create a Jenkins CI/CD pipeline.
6. Practise Docker commands.
7. Build and run a Docker image for the app.
8. Run the containerized app with Kubernetes.
9. Automate deployment and verify the running service.

For later Docker/Kubernetes weeks, configure MongoDB networking and secrets for the deployment environment; `localhost` inside a container refers to that container, not automatically to your Windows host.

## Notes
- `app.py` enables Flask debug mode for local learning only. Do not use debug mode in a public deployment.
- Click tracking counts requests that reach the short-link redirect route, including repeat visits.
#case study