# Agent 8 Daily Automation Script - Runs at 6 AM via Task Scheduler
# Exports multi-period data from Trino and syncs to Neon PostgreSQL

$ProjectDir = "C:\Users\muskan.rao\Documents\claude\agent8-unified-portal"
$LogFile = "$ProjectDir\automation.log"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log {
    param([string]$Message)
    Write-Host "[${Timestamp}] ${Message}"
    Add-Content -Path $LogFile -Value "[${Timestamp}] ${Message}"
}

# Initialize
Write-Log "╔════════════════════════════════════════════════════════════════╗"
Write-Log "║           Agent 8 Daily Automation Starting                    ║"
Write-Log "╚════════════════════════════════════════════════════════════════╝"

Set-Location $ProjectDir

# Step 1: Export data from Trino
Write-Log "Step 1/2: Exporting multi-period data from Trino..."
try {
    $Output = python agent8_production_export.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ Export successful"
        Write-Log "  - Full backfill: 2024-01-01 to today"
        Write-Log "  - Recent period: Last 23 days"
    } else {
        Write-Log "✗ Export failed"
        Write-Log "Output: $Output"
        Write-Log "ERROR: Skipping sync due to export failure"
        exit 1
    }
} catch {
    Write-Log "✗ Export error: $_"
    exit 1
}

# Step 2: Sync to Neon PostgreSQL
Write-Log "Step 2/2: Syncing to Neon PostgreSQL..."
try {
    $Output = python sync_excel_to_neon.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ Sync successful"
        Write-Log "  - Updated Neon database"
        Write-Log "  - Dashboard will auto-refresh"
    } else {
        Write-Log "✗ Sync failed"
        Write-Log "Output: $Output"
        exit 1
    }
} catch {
    Write-Log "✗ Sync error: $_"
    exit 1
}

# Completion
Write-Log "═════════════════════════════════════════════════════════════════"
Write-Log "✓ Daily automation completed successfully"
Write-Log "  All 26 professionals updated with latest data"
Write-Log "  Dashboard ready for user queries"
Write-Log "═════════════════════════════════════════════════════════════════"
