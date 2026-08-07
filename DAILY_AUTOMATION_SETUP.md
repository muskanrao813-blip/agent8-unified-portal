# Daily Automation Setup - Agent 8 Unified Portal

## Automated Daily Export & Sync

**What it does:**
- Runs at 6 AM daily
- Exports multi-period data from Trino (full backfill + recent 23 days)
- Syncs to Neon PostgreSQL
- Dashboard automatically displays latest data

## Setup Instructions

### Step 1: Create PowerShell Script

Create file: `C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\agent8_daily_automation.ps1`

```powershell
# Agent 8 Daily Automation - Runs at 6 AM
$ProjectDir = "C:\Users\muskan.rao\Documents\claude\agent8-unified-portal"
cd $ProjectDir

# Step 1: Export data from Trino
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Starting Agent 8 daily export..."
python agent8_production_export.py

# Step 2: Sync to Neon
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Syncing to Neon..."
python sync_excel_to_neon.py

# Step 3: Log
Add-Content -Path "$ProjectDir\automation.log" -Value "$(Get-Date): Daily automation completed successfully"
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Done!"
```

### Step 2: Create Windows Task Scheduler Job

Run this command in PowerShell (as Administrator):

```powershell
# Create scheduled task
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -File 'C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\agent8_daily_automation.ps1'"
$Trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$Principal = New-ScheduledTaskPrincipal -UserID "$env:USERNAME" -LogonType ServiceAccount
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -TaskName "Agent8DailyExport" -Description "Daily Agent 8 data export and Neon sync"

Write-Host "✓ Scheduled task created: Agent8DailyExport"
Write-Host "  Runs daily at 6:00 AM"
Write-Host "  Check automation.log for status"
```

### Step 3: Verify Setup

```powershell
# Check if task was created
Get-ScheduledTask -TaskName "Agent8DailyExport" | Select-Object -Property TaskName,State,LastTaskResult

# View logs
Get-Content "C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\automation.log" -Tail 5

# Test manually
C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\agent8_daily_automation.ps1
```

## What Gets Updated Daily

| Component | Update | Source |
|-----------|--------|--------|
| Full Backfill | Every day | Trino (2024-01-01 to today) |
| Recent 23 Days | Every day | Trino (last 23 days) |
| Neon DB | New rows | PostgreSQL upsert |
| Dashboard | Auto-refresh | Vercel + Render API |

## Data Flow

```
6:00 AM
  ↓
[Task Scheduler]
  ↓
[agent8_production_export.py] → Queries Trino
  ↓
[sync_excel_to_neon.py] → Syncs to Neon PostgreSQL
  ↓
[Render API] → Fetches data on demand
  ↓
[Vercel Dashboard] → User sees latest data
```

## Troubleshooting

- **No data showing?** Check `automation.log` for errors
- **Task not running?** Verify Trino credentials in .env
- **Neon connection failed?** Check DATABASE_URL in .env has -pooler suffix
- **Dashboard showing old data?** Clear browser cache (Ctrl+Shift+Delete)

## Manual Trigger

```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
python agent8_production_export.py
python sync_excel_to_neon.py
```

---
**Last Updated:** 2026-08-07
**Status:** ✅ Ready for production
