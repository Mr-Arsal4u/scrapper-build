# Lead Counting & Auto-Download Explanation

## 📊 How Lead Counting Works

### ✅ YES - Code Counts Leads After Every Scheduler Hit

**Every 5 minutes, the scheduler:**

1. **Scrapes all towns** (102 towns)
2. **Counts all leads** found: `current_count = len(all_leads)`
3. **Compares with previous count** from `last_lead_count.json`
4. **Saves the new count** for next comparison

**Example from logs:**
```
[SCHEDULER] Total leads scraped: 319
[SCHEDULER] Step 3: Comparing with previous count...
[SCHEDULER] Previous count: 319, Current count: 319
[SCHEDULER] No increase in lead count (same or decreased)
[SCHEDULER] ✅ Saved current count (319 leads) for next comparison
```

---

## 🔄 What Happens When Lead Count Increases

### Scenario: Count Increases (e.g., 319 → 325)

When `current_count > previous_count`, the system:

#### Step 1: Detect Increase
```
[SCHEDULER] ✅ Lead count increased! (319 → 325)
[SCHEDULER] Finding new leads...
```

#### Step 2: Find New Leads
- Compares **docket numbers** between old and new leads
- Identifies truly new leads (not duplicates)
- Example: `Found 6 new leads!`

#### Step 3: Save New Leads to Excel
- Creates `new_leads_YYYYMMDD_HHMMSS.xlsx` with **only new leads**
- Creates `all_leads_YYYYMMDD_HHMMSS.xlsx` with **all current leads**
- Both files saved in project root directory

#### Step 4: Update Count File
- Saves to `temp_leads/last_lead_count.json`:
  ```json
  {
    "count": 325,
    "leads": [...all 325 leads...],
    "timestamp": "2026-01-08T13:04:25"
  }
  ```

#### Step 5: Frontend Auto-Download (if browser is open)
- Frontend checks every **30 seconds** for new leads
- When count increases detected:
  - ✅ Updates display with new count
  - ✅ Shows notification: "New leads detected! (319 → 325) Auto-downloading Excel..."
  - ✅ **Automatically downloads Excel file** after 1 second
  - ✅ Updates leads table with new data

---

## 📋 Complete Flow Diagram

```
┌─────────────────────────────────────────────────┐
│  Scheduler Runs Every 5 Minutes                 │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  1. Scrape All Towns (102 towns)                │
│  2. Collect All Leads                            │
│  3. Count: current_count = len(all_leads)       │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Load Previous Count from last_lead_count.json  │
│  previous_count = 319                            │
└─────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────┴───────────┐
        │                       │
   current_count          current_count
   > previous_count       <= previous_count
        │                       │
        ▼                       ▼
┌───────────────┐      ┌──────────────────┐
│ COUNT         │      │ No Action        │
│ INCREASED!    │      │ Just save count  │
└───────────────┘      └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│  Find New Leads (by docket number comparison)   │
│  new_leads = [leads not in previous list]       │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│  Save Excel Files:                               │
│  • new_leads_TIMESTAMP.xlsx (only new ones)     │
│  • all_leads_TIMESTAMP.xlsx (all current)       │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│  Update last_lead_count.json                    │
│  Save current_count and all_leads                │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│  Frontend (if browser open):                    │
│  • Checks every 30 seconds                      │
│  • Detects count increase                       │
│  • Auto-downloads Excel file                    │
│  • Updates display                              │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Key Points

### ✅ Lead Counting
- **YES** - Counts after every scheduler run
- Count is: `len(all_leads)` after scraping all towns
- Always saves count to `last_lead_count.json`

### ✅ When Count Increases
1. **Detects increase** immediately
2. **Finds new leads** by comparing docket numbers
3. **Saves 2 Excel files**:
   - `new_leads_*.xlsx` - Only the new leads
   - `all_leads_*.xlsx` - All current leads
4. **Updates count file** with new data
5. **Frontend auto-downloads** (if browser is open)

### ✅ When Count Stays Same or Decreases
- Just saves the current count
- No Excel files created
- No frontend action

---

## 📁 Files Created

### When Count Increases:
- `new_leads_20260108_130425.xlsx` - New leads only
- `all_leads_20260108_130425.xlsx` - All leads
- `temp_leads/last_lead_count.json` - Updated with new count

### When Count Same/Decreased:
- Only `temp_leads/last_lead_count.json` updated

---

## 🎯 Example Scenario

**Initial State:**
- Previous count: 319 leads
- Scheduler runs...

**After Scraping:**
- Current count: 325 leads
- **Count increased!** (319 → 325)

**What Happens:**
1. ✅ Finds 6 new leads (by docket number)
2. ✅ Saves `new_leads_20260108_130425.xlsx` (6 leads)
3. ✅ Saves `all_leads_20260108_130425.xlsx` (325 leads)
4. ✅ Updates `last_lead_count.json` (count: 325)
5. ✅ Frontend auto-downloads Excel (if browser open)

---

## 💡 Summary

**Question 1: Does code count leads after every scheduler hit?**
- **YES** ✅ - Counts `len(all_leads)` after every scheduler run

**Question 2: What happens when count increases?**
- ✅ Detects increase
- ✅ Finds new leads (by docket number)
- ✅ Saves 2 Excel files (new leads + all leads)
- ✅ Updates count file
- ✅ Frontend auto-downloads (if browser open)

The system is fully automated and tracks every change! 🎉

