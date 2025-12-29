# 🚀 Quick Start Guide - Databricks Model Integration

## 1. Prerequisites ✅

- **Python 3.8+** installed
- **Node.js 18+** installed
- **Databricks CLI** authenticated
- Access to `databricks-gpt-5-1` model endpoint

## 2. Authenticate with Databricks (One-time Setup)

```bash
# Login to your Databricks workspace
databricks auth login

# Follow the prompts to authenticate via OAuth
# No profile specification needed - uses default
```

## 3. Install Dependencies

```bash
cd demo-logistics

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install
```

## 4. Configure Environment (Optional)

```bash
# Copy example environment file
cp env.example .env

# Edit .env if you want to change defaults
# nano .env
```

Default configuration works out of the box:
- Backend: `http://localhost:8001`
- Model: `databricks-gpt-5-1`
- Port: `8001`

## 5. Start the Application

**Option A: One Command (Recommended)**
```bash
./start-dev.sh
```

**Option B: Separate Terminals**
```bash
# Terminal 1 - Backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2 - Frontend
npm run dev
```

## 6. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs (FastAPI auto-generated)

## 7. Test the Integration

### Option A: Automated Test
```bash
python test_backend.py
```

### Option B: Manual UI Test
1. Open http://localhost:5173
2. Click on the **BNA-STL-AIR** lane (red, showing delays)
3. Click **"Reroute Urgent Packages"**
4. Click **"Choose this reroute"** on any option
5. Watch the AI message generate! 🎉

### Option C: API Test
```bash
curl http://localhost:8001/ | jq
```

Expected output:
```json
{
  "status": "ok",
  "service": "Logistics AI Backend",
  "model_endpoint": "databricks-gpt-5-1",
  "databricks_connected": true
}
```

## 8. Verify Databricks Integration

Look for these indicators:
- ✅ Loading spinner when generating message
- ✅ Message appears within 2-5 seconds
- ✅ **"Generated using Databricks foundation model"** label (with sparkle icon)
- ✅ Professional, factual message content
- ✅ No chatbot-like language

## 9. Deploy to Databricks Apps

When ready to deploy:

```bash
# Commit your changes
git add .
git commit -m "Add Databricks model integration"
git push

# Deploy in Databricks workspace:
# 1. Navigate to Apps
# 2. Create new app
# 3. Point to your git repository
# 4. Databricks handles the rest!
```

## Troubleshooting

### "Databricks client not initialized"
```bash
# Re-authenticate
databricks auth login

# Verify authentication
databricks auth token
```

### "Backend unavailable" (amber indicator)
```bash
# Check if backend is running
curl http://localhost:8001/

# If not, start it:
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

### "Model unavailable" (uses fallback)
- Verify model endpoint exists: Check Databricks workspace → ML → Model Serving
- Verify model is running (not paused)
- Check endpoint name matches: `databricks-gpt-5-1`
- Verify you have access permissions

### Port 8001 already in use
```bash
# Find and kill the process
lsof -i :8001
kill -9 <PID>

# Or use a different port
PORT=8002 python -m uvicorn backend.main:app --reload
# Update VITE_BACKEND_URL in .env to match
```

## Next Steps

- 📚 Read [DATABRICKS_MODEL_SETUP.md](DATABRICKS_MODEL_SETUP.md) for detailed documentation
- 📊 Read [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) for technical details
- 🎬 Try generating messages for different scenarios
- 🚀 Deploy to Databricks Apps

## Questions?

Check these resources:
- [Databricks Apps Documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime)
- [Model Serving Query Guide](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-chat-models)
- Project README.md

---

**Happy coding! 🎉**


