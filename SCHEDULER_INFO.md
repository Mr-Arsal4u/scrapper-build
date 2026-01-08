# Automated Scheduler Feature

## Overview
The scraper now includes an automated scheduler that runs every 5 minutes to:
1. Automatically scrape the town list
2. Automatically scrape leads from all towns
3. Compare with previous lead count
4. Save only NEW leads to Excel when count increases
5. Auto-download the Excel file

## How It Works

### Automatic Execution
- **Interval**: Every 5 minutes
- **First Run**: Starts 5 minutes after the app starts
- **Background**: Runs in background, doesn't block the web interface

### Lead Comparison
- Tracks previous lead count in `temp_leads/last_lead_count.json`
- Compares current count with previous count
- Only saves new leads when count increases
- Identifies new leads by comparing docket numbers

### File Output
When new leads are found:
- **New Leads File**: `new_leads_YYYYMMDD_HHMMSS.xlsx` - Contains only the new leads
- **All Leads File**: `all_leads_YYYYMMDD_HHMMSS.xlsx` - Contains all current leads

## Manual Control

### Trigger Manually
You can manually trigger the scheduler job:
```bash
curl -X POST http://localhost:5000/trigger-scheduler
```

Or use the web interface (if button is added).

### Check Status
Check scheduler status and last run info:
```bash
curl http://localhost:5000/scheduler-status
```

Returns:
```json
{
  "scheduler_running": true,
  "last_run": "2026-01-07T17:30:00",
  "last_count": 150,
  "next_run": null
}
```

## Installation

The scheduler requires `APScheduler` which is already in `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Running

Just start the app as usual:
```bash
./run.sh
```

The scheduler will automatically start with the Flask app.

## Logs

Scheduler activity is logged to the console with `[SCHEDULER]` prefix:
```
======================================================================
[SCHEDULER] Automated scrape started at 2026-01-07 17:30:00
======================================================================
[SCHEDULER] Step 1: Scraping town list...
[SCHEDULER] Found 169 towns
[SCHEDULER] Step 2: Scraping leads from 169 towns...
[SCHEDULER] [1/169] Processing Andover...
...
[SCHEDULER] Total leads scraped: 150
[SCHEDULER] Step 3: Comparing with previous count...
[SCHEDULER] Previous count: 145, Current count: 150
[SCHEDULER] ✅ Lead count increased! (145 → 150)
[SCHEDULER] Found 5 new leads!
[SCHEDULER] ✅ Saved 5 new leads to: new_leads_20260107_173000.xlsx
[SCHEDULER] ✅ Saved all 150 leads to: all_leads_20260107_173000.xlsx
[SCHEDULER] ✅ Automated scrape completed
======================================================================
```

## Notes

- The scheduler runs independently of the web interface
- You can still use the manual "Scrape Towns" button anytime
- Excel files are saved in the project root directory
- Old lead count data is stored in `temp_leads/last_lead_count.json`
- The scheduler uses the same Chrome profile and VPN settings as manual scraping


