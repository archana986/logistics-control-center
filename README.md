# Databricks Network Control Center - Demo

An interactive logistics network visualization demo showcasing real-time operations monitoring, incident management, intelligent rerouting, and **AI-powered customer communications with Databricks foundation models**.

## 📚 Documentation

- **[CEO Demo Highlights](CEO_DEMO_HIGHLIGHTS.md)** - Executive summary and demo walkthrough
- **[Quick Reference Card](DEMO_QUICK_REFERENCE.md)** - 5-minute demo script with talking points
- **[Example Message Output](EXAMPLE_MESSAGE_OUTPUT.md)** - Sample AI-generated messages with explanations
- **[Technical Changes](CHANGES_SUMMARY.md)** - Detailed implementation overview
- **[Databricks Model Setup](DATABRICKS_MODEL_SETUP.md)** - Complete guide for model integration

## 🚀 Quick Start

### For Local Development

```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Option 1: Start both backend and frontend with one command
./start-dev.sh

# Option 2: Start separately
# Terminal 1 - Backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2 - Frontend
npm run dev
```

The app will be available at:
- Frontend: `http://localhost:5173` (dev) or `http://localhost:8000` (preview)
- Backend API: `http://localhost:8001`

### Test the Backend

```bash
# Test the API endpoints
python test_backend.py
```

### For Databricks Apps Deployment

Simply push your code to git and deploy from Databricks Apps. No changes needed!

```bash
git add .
git commit -m "Deploy to Databricks"
git push
```

See **[Databricks Model Setup](DATABRICKS_MODEL_SETUP.md)** for detailed deployment instructions.

## 📋 Demo Flow

### 1. Network Overview
- **What you see**: Full-screen interactive map showing the entire logistics network
- **Key features**:
  - Arcs (lanes) colored by delay status (green = on-time, yellow = caution, red = at-risk)
  - Arc thickness represents daily package volume
  - Hub locations marked with colored dots (purple = air hub, blue = distribution center)
  - KPI cards showing network health metrics
  
**Demo Script**: "Here's our entire network in real-time. The arcs show package flows between hubs. Color indicates delay status—green is good, red means we need to take action. The Nashville to Saint Louis lane is showing red today."

### 2. Drill-Down Analysis
- **Action**: Click on the Nashville → Saint Louis (BNA-STL-AIR) lane
- **What appears**: Right panel shows detailed lane analytics
  - Performance metrics (volume, on-time %, delays, SLA risk)
  - 24-hour performance trend chart
  - Active incidents with confidence scores
  - Root cause analysis (FX423 weather delay, I-65 closure)

**Demo Script**: "Let me click into this problematic lane. The panel shows us the root causes—ranked by AI confidence. We've got a thunderstorm delaying flight FX423 by 140 minutes, plus a highway accident reducing our ground backup by 38%."

### 3. Take Action - Reroute
- **Action**: Click "Reroute Urgent Packages" button
- **What appears**: Reroute panel slides in from the right
  - Shows number of affected high-priority shipments
  - Presents pre-computed rerouting options
  - Each option shows: ETA improvement, added cost, capacity utilization, and implementation notes
  
**Demo Script**: "We have 3 urgent packages at risk. Let's look at our options. The truck via Chicago option actually improves ETA by 75 minutes for $3,100. The AI solver has already reserved dock slots to make this work."

### 4. AI-Generated Customer Message ⭐ **NEW FEATURES**
- **Action**: Click "Choose this reroute" on any option
- **What appears**: Bottom drawer opens with a personalized customer message
  - **Personalized context** based on past customer interactions
  - **Detailed incident analysis** (type, reference, root cause, confidence)
  - **Citations** from recent customer conversations
  - Professional, branded communication ready to send
  
**Demo Script**: "Now let's proactively notify our platinum customer. Watch what the AI does—it's not just generating a generic message. It's referencing our previous conversations with Walmart, including their request for proactive alerts we discussed on October 15th. The message cites specific past interactions, shows full incident details, and acknowledges their documented preferences. This is relationship management at scale."

**What makes this special:**
- AI analyzes customer interaction history (emails, calls, meetings)
- Personalizes tone based on customer preferences
- Includes numbered citations linking to past conversations
- Shows detailed incident context (91% confidence detection)
- Demonstrates institutional memory and relationship continuity

## 🛠️ Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Python FastAPI + Databricks SDK
- **AI Model**: Databricks foundation model serving (databricks-gpt-5-1)
- **UI Framework**: Tailwind CSS + shadcn/ui components
- **Mapping**: deck.gl + MapLibre GL JS (open-source)
- **Charts**: recharts
- **State**: Zustand
- **Data**: Static JSON files + Databricks model API

## 📁 Project Structure

```
demo-logistics/
├── backend/
│   ├── __init__.py
│   └── main.py           # FastAPI backend with Databricks SDK
├── public/mock/          # Mock data JSON files
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   ├── MapView/      # deck.gl map components
│   │   ├── KPICards.tsx
│   │   ├── LaneDetails.tsx
│   │   ├── IncidentTimeline.tsx
│   │   ├── ReroutePanel.tsx
│   │   └── GenAIDrawer.tsx
│   ├── lib/
│   │   ├── mockApi.ts    # Simulated API calls
│   │   ├── genai.ts      # Message generation with AI
│   │   └── format.ts     # Utility formatters
│   ├── pages/
│   │   └── NetworkOverview.tsx
│   ├── store/
│   │   └── useAppStore.ts
│   └── types/
│       └── domain.ts
├── app.yaml              # Databricks Apps configuration
├── requirements.txt      # Python dependencies
├── start-dev.sh          # Local development startup script
├── test_backend.py       # Backend API tests
└── package.json
```

## 🎨 Key Features

### Interactive Map
- **WebGL-powered visualization** using deck.gl for smooth performance with large datasets
- **Color-coded lanes** based on delay metrics
- **Clickable elements** for detailed drill-down
- **3D perspective** for visual impact

### Real-Time Analytics
- Network-wide KPIs (volume, on-time %, at-risk lanes)
- Lane-specific performance metrics
- Incident timeline with confidence scores
- 24-hour trend visualization

### Intelligent Rerouting
- Pre-computed optimization scenarios
- Cost-benefit analysis for each option
- Capacity and constraint awareness
- One-click implementation

### AI-Powered Communications ⭐ **DATABRICKS INTEGRATION**
- **Databricks foundation model** (databricks-gpt-5-1) for intelligent message generation
- **Customer interaction history** - References past emails, calls, meetings
- **Personalized messaging** - Adapts tone based on documented preferences
- **Citation system** - Shows sources from previous conversations
- **Incident intelligence** - Full technical context with confidence scores
- **Relationship continuity** - Demonstrates institutional memory
- **Seamless authentication** - Works locally with CLI OAuth and in Databricks Apps automatically
- **Fallback mechanism** - Gracefully degrades to template-based generation if model unavailable
- Copy-to-clipboard for easy distribution

## 🔧 Customization

### Adding New Hubs
Edit `public/mock/centers.json`:
```json
{
  "id": "NYC",
  "name": "New York Hub",
  "lat": 40.7128,
  "lng": -74.0060,
  "type": "dc"
}
```

### Adding New Lanes
Edit `public/mock/lanes.json`:
```json
{
  "id": "NYC-BOS-GROUND",
  "origin": "NYC",
  "dest": "BOS",
  "mode": "ground",
  "avgDailyVolume": 2500,
  "onTimePct": 0.94,
  "delayMinutes": 35,
  "slaRiskPct": 0.06
}
```

### Customizing Colors
Edit `src/index.css` to change the color scheme (CSS variables).

## 🚢 Deployment

### Build for Production
```bash
npm run build
```

The build output will be in the `dist/` folder.

### Deploy to Databricks Apps

The application is configured for seamless Databricks Apps deployment:

1. **Commit and push your code**:
   ```bash
   git add .
   git commit -m "Deploy to Databricks Apps"
   git push
   ```

2. **Deploy in Databricks**:
   - Navigate to Apps in your Databricks workspace
   - Create a new app or update existing
   - Point to your git repository
   - Databricks will automatically install dependencies and start services

3. **Configuration**:
   - Model endpoint: Set via `DATABRICKS_MODEL_ENDPOINT` in `app.yaml`
   - Authentication: Handled automatically by Databricks
   - No code changes needed between local and deployed!

See **[Databricks Model Setup](DATABRICKS_MODEL_SETUP.md)** for detailed instructions.

### Deploy Anywhere
The app is a static bundle that can be deployed to:
- **Vercel**: `vercel deploy`
- **Netlify**: Drag & drop the `dist/` folder
- **AWS S3 + CloudFront**: Upload `dist/` to S3 bucket
- **Azure Static Web Apps**: Connect to GitHub repo

## 📊 Demo Data

All data is mocked and stored in `public/mock/`:
- **6 hub locations** across the US (Nashville, Saint Louis, Pittsburgh, Chicago, etc.)
- **8+ lane routes** with varying performance metrics
- **Multiple incidents** affecting various routes (weather, maintenance, traffic)
- **13+ shipments** from major customers (Walmart, Nike, Target, Amazon, Chewy)
- **5 customer profiles** with rich interaction history:
  - **Walmart** - Emphasized proactive alerts, previous BNA-STL issue
  - **Nike** - Prefers phone calls for critical issues
  - **Target** - Needs advance notice for store coordination
  - **Amazon** - System integration, automated alerts
  - **Chewy** - Focus on customer satisfaction (pet owners)
- **3 reroute options** per affected lane with cost/time analysis
- **15+ customer interactions** (emails, calls, meetings) with dates and summaries

## 🎯 What's Next

To make this production-ready:
1. ~~Replace mock data with real API calls~~ ✅ **Backend API implemented**
2. Add authentication/authorization
3. Implement actual rerouting logic (optimization solver)
4. ~~Connect to real GenAI service~~ ✅ **Databricks model integrated**
5. Add historical data and trend analysis
6. Implement real-time WebSocket updates
7. Add user preferences and saved views
8. Scale model endpoint for production load

## 📝 Notes

- This is a **demo/prototype** designed for executive presentations
- Mock data is **hardcoded** for fallback—no network required for basic functionality
- **AI message generation** uses Databricks foundation models in production
- **Graceful fallback**: App works offline with template-based generation
- The "reroute" and "send message" actions are **simulated** (no actual operations)
- Performance is optimized for demos (< 50 locations, < 100 lanes)
- **Authentication**: Uses Databricks CLI OAuth locally, automatic in Databricks Apps

## 🙋 Support

For questions or issues, contact the development team.

---

Built with ❤️ for Databricks
