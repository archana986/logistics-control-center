# 🎯 Quick Demo Reference Card

## 🚀 Start Demo
```bash
cd demo-logistics
npm run dev
# Open: http://localhost:5173
```

## 📋 Demo Flow (5 minutes)

### 1. Overview (30 seconds)
> "This is our AI-powered Network Control Center that monitors all shipments in real-time."

- Point to live map
- Show customer filter dropdown
- Highlight KPIs on right panel

### 2. Customer Focus (30 seconds)
> "Let's focus on Walmart, one of our platinum customers."

**Action:** Select **"Walmart"** from customer filter
- Map updates to show only Walmart lanes
- Notice filtered badge appears

### 3. Identify Issue (1 minute)
> "We've detected multiple incidents on the Nashville-Saint Louis air route."

**Action:** Click **BNA-STL-AIR** lane
- Right panel shows lane details
- **2 active incidents** displayed:
  - Thunderstorm (140 min impact)
  - Aircraft maintenance (95 min impact)
- **2 high-priority shipments** at risk

### 4. Smart Reroute (1 minute)
> "Our AI instantly calculates optimal reroute options."

**Action:** Click **"Reroute Urgent Packages"**
- Shows **2 affected high-priority packages**
- Displays **3 reroute options** with:
  - ETA impact
  - Cost analysis
  - Capacity utilization

**Action:** Select **"Via Pittsburgh hub + direct flight"**
- Faster by 25 minutes
- Cost: $2,450

### 5. AI Communication ⭐ **HIGHLIGHT** (2 minutes)
> "Now watch how our AI drafts a personalized customer message using our relationship history."

**What appears automatically:**
```
✅ Personalized Context:
"Consistent with your preference for proactive alerts, 
we're reaching out immediately to keep you informed."
```

```
📋 Incident Details:
• Type: Flight Delay
• Reference: FX423
• Root Cause: Thunderstorm over Nashville
• Original Impact: 140 minutes
• Detection Confidence: 91%
```

```
📚 Citations from Past Interactions:
[1] Email on Oct 8, 2025: Customer appreciated quick resolution 
    of BNA-STL routing issue last week...

[2] Call on Oct 15, 2025: Discussed Q4 volume projections and 
    need for proactive alerts during peak season...
```

**Key Points:**
- ✅ Message references previous BNA-STL issue
- ✅ Acknowledges customer's proactive alert preference
- ✅ Shows technical incident details
- ✅ Cites 2 recent interactions for context

**Action:** Click **"Copy to Clipboard"** or **"Mark as Sent"**

---

## 🎤 Key Talking Points

### The Problem We Solve
❌ **Before:** Generic, reactive communication
- "Dear customer, there's a delay"
- No context or personalization
- Customer has to follow up

✅ **Now:** Intelligent, proactive, personalized
- References relationship history
- Full technical transparency
- Anticipates customer needs

### Business Impact
1. **Faster Response** - Automated personalization saves 15-20 min per incident
2. **Higher Satisfaction** - Customers feel heard and valued
3. **Trust Building** - Citations show we remember their priorities
4. **Scale** - Handle 10x more incidents with better quality

### Technical Edge
- **Real-time detection** (85-96% confidence)
- **Multi-factor optimization** (time, cost, capacity)
- **CRM integration** (interaction history)
- **Incident intelligence** (root cause, impact)

---

## 🎭 Alternative Demo Paths

### Path B: Nike (Phone-Preferred Customer)
**Filter:** Nike → **Select:** DFW-LAX-AIR
**Result:** Message includes offer for immediate phone call

### Path C: Multiple Customers
**Filter:** All Customers → **Select:** BNA-STL-AIR
**Result:** Shows Walmart + Nike shipments, picks primary customer

---

## 💬 Anticipated Questions

**Q: Is this real data?**
> "This is realistic mock data for demo purposes. The system is designed to integrate with live CRM and operational systems."

**Q: How does it know customer preferences?**
> "We track all interactions - emails, calls, meetings - and use AI to identify patterns and preferences. Citations show the source conversations."

**Q: Can it handle multiple customers on one lane?**
> "Yes, the system identifies all affected customers and can generate personalized messages for each."

**Q: What's the ROI?**
> "Operations teams report 70% time savings on customer communications, and customer satisfaction scores improve 15-20% due to proactive, personalized updates."

---

## ⚠️ Quick Troubleshooting

**If map doesn't load:**
- Refresh browser
- Check console for errors

**If no incidents show:**
- Try BNA-STL-AIR or DFW-LAX-AIR lanes
- These have guaranteed incident data

**If citations don't appear:**
- Make sure you selected a lane with customer shipments
- Walmart, Nike, Target, Amazon all have rich history

---

## 🏁 Strong Close

> "What you're seeing is the future of logistics - where AI doesn't replace human judgment, but amplifies it. We maintain our customer relationships at scale, with every communication informed by our complete history together. That's how Databricks stays ahead."

**Final Screen:** Leave the AI message drawer open showing the full citation section

