# How to View Logs from Inside the Pod

When you're inside the Kubernetes pod shell:
```bash
root@startup-intelligence-analysis-ap-5575d95796-zkzvm:/app#
```

## Pipeline Logs

The pipeline logs are written to `pipeline.log` in the `/app` directory by default.

### View the entire log file:
```bash
cat pipeline.log
```

### View last 100 lines:
```bash
tail -n 100 pipeline.log
```

### Follow logs in real-time (like `tail -f`):
```bash
tail -f pipeline.log
```

### View last 500 lines with line numbers:
```bash
tail -n 500 pipeline.log | cat -n
```

### Search for errors in logs:
```bash
grep -i error pipeline.log
grep -i "failed\|exception\|traceback" pipeline.log
```

### View logs with timestamps (if structured logging):
```bash
cat pipeline.log | jq '.'  # If JSON logs
```

## API Logs

If `ENABLE_FILE_LOGGING=true`, API logs are written to `logs/api.log`:

```bash
# Check if API logging is enabled
ls -la logs/

# View API logs
cat logs/api.log
tail -f logs/api.log
```

## Check Log File Location

The log file path can be customized with `PIPELINE_LOG_PATH` environment variable:

```bash
# Check current log path
echo $PIPELINE_LOG_PATH

# Default is pipeline.log in /app directory
ls -lh pipeline.log
```

## View Logs by Size

```bash
# Check log file size
ls -lh pipeline.log

# View last 1MB of logs
tail -c 1M pipeline.log

# View first 100 lines
head -n 100 pipeline.log
```

## Filter Logs by Phase

```bash
# View only Phase 0 (scraping) logs
grep "PHASE 0" pipeline.log

# View only Phase 1 (extraction) logs
grep "PHASE 1" pipeline.log

# View completion messages
grep -i "complete\|finished\|done" pipeline.log
```

## Debug Logs (if enabled)

If `enable_debug_logs=true` was used, you'll see DEBUG level logs:

```bash
# View all DEBUG logs
grep -i "debug" pipeline.log

# View logs with DEBUG level
grep '"level":"DEBUG"' pipeline.log  # For JSON logs
```

## Common Commands Summary

```bash
# Quick view of recent activity
tail -n 200 pipeline.log

# Watch logs in real-time
tail -f pipeline.log

# Check for errors
grep -i error pipeline.log | tail -n 50

# Count total lines
wc -l pipeline.log

# View logs from last 10 minutes (if timestamps present)
grep "$(date -d '10 minutes ago' '+%Y-%m-%d %H:%M')" pipeline.log
```

## If Log File Doesn't Exist

If `pipeline.log` doesn't exist, it means:
- No pipeline has been run yet
- The log file was cleared
- Logs are being written to a different location

Check:
```bash
# List all log files
find /app -name "*.log" -type f

# Check if pipeline is currently running
ps aux | grep pipeline.py
```

