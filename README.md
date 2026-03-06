# Sales Report App

A web app that takes an Excel spreadsheet and produces:
- A plain text report of partners, customers, sales prices, and estimated close dates
- A pie chart showing which partners have the most sales attributed to them

Filtered by a **Created Date** range you define in the UI.

---

## Project Structure

```
sales-report-app/
├── app.py                        # Main Flask app + column config
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── deployment.yaml               # K3s deployment + service
├── templates/
│   └── index.html                # Web UI
└── .github/
    └── workflows/
        └── build.yml             # Auto-build on push to main
```

---

## Step 1 — Configure your column names

Open `app.py` and find `COLUMN_CONFIG` near the top:

```python
COLUMN_CONFIG = {
    "partner":      "Partner",
    "customer":     "Customer",
    "sales_price":  "Sales Price",
    "close_date":   "Est. Close Date",
    "created_date": "Created Date",
}
```

Change the **values** (right side) to match the exact column headers in your spreadsheet.

---

## Step 2 — Push to GitHub

```bash
# One-time setup (run from inside the project folder)
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sales-report-app.git
git push -u origin main
```

GitHub Actions will automatically build a Docker image and push it to
`ghcr.io/YOUR_USERNAME/sales-report-app:latest` on every push to `main`.

---

## Step 3 — Update deployment.yaml

Edit `deployment.yaml` and replace `YOUR_GITHUB_USERNAME` with your actual GitHub username:

```yaml
image: ghcr.io/YOUR_GITHUB_USERNAME/sales-report-app:latest
```

Commit and push that change too.

---

## Step 4 — Deploy to K3s via Rancher Desktop

Wait for the GitHub Actions build to complete (check the Actions tab on GitHub), then:

```bash
# Apply the deployment
kubectl apply -f deployment.yaml

# Check it's running
kubectl get pods

# Find the NodePort (look for the port after 80:)
kubectl get service sales-report-app
```

The app will be available at:
```
http://localhost:NODE_PORT
```
(replace NODE_PORT with the number shown, e.g. `http://localhost:31234`)

---

## Updating the app

1. Make your code changes locally
2. `git add . && git commit -m "your change" && git push`
3. GitHub Actions rebuilds the image automatically
4. Pull the new image in K3s:

```bash
kubectl rollout restart deployment/sales-report-app
```

That's it — the app updates live with no downtime.

---

## Changing column names later

1. Edit `COLUMN_CONFIG` in `app.py`
2. Push to GitHub
3. Run `kubectl rollout restart deployment/sales-report-app`
