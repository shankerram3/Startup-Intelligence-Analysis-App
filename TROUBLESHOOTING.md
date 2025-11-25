# Troubleshooting Pipeline Issues

## Common Errors

### "waiting on pid X in sandbox: urpc method failed: EOF"

This error indicates that the container runtime lost connection to a process. This can happen when:

1. **Container Restart**: The container was restarted while the pipeline was running
2. **Process Killed**: The process was killed by the system (OOM killer, resource limits)
3. **Timeout**: The process exceeded a timeout limit
4. **Resource Limits**: Memory or CPU limits were exceeded

#### Solutions:

**Check if the process is still running:**
```bash
# Inside the pod
ps aux | grep pipeline.py
ps aux | grep python
```

**Check container logs:**
```bash
# From your local machine or DO dashboard
# Check DigitalOcean App Platform logs for:
# - Container restarts
# - OOM (Out of Memory) errors
# - Resource limit warnings
```

**Check resource usage:**
```bash
# Inside the pod
free -h  # Check memory
df -h    # Check disk space
top      # Check CPU usage
```

**Check if the pipeline log file exists:**
```bash
ls -lh pipeline.log
tail -n 100 pipeline.log
```

**Restart the pipeline:**
- If the process died, you can restart it through the web UI
- The status endpoint should detect that the process is no longer running

### Pipeline Stops Unexpectedly

**Possible causes:**
1. Memory limits exceeded
2. Container restart
3. Process crash
4. Network timeout

**Check logs:**
```bash
# View recent pipeline logs
tail -n 500 pipeline.log

# Search for errors
grep -i "error\|failed\|exception\|traceback" pipeline.log

# Check for OOM errors
grep -i "killed\|oom\|out of memory" pipeline.log
```

### 503/504 Gateway Timeout Errors

**Causes:**
- Server overloaded
- Long-running requests
- Container restarting

**Solutions:**
- The frontend now handles these gracefully
- Check server logs for the actual error
- Reduce pipeline workload if needed

### Logs Not Showing in History

**Causes:**
- Server was unavailable when saving logs (503/504)
- Log file was cleared
- Logs too large and truncated

**Solutions:**
- Check if logs exist in the pod: `cat pipeline.log`
- Enable DEBUG logging for more detailed information
- Check browser console for error messages

## Debugging Steps

### 1. Check Pipeline Status

```bash
# Inside the pod
ps aux | grep pipeline.py

# Check if process exists
ls -l /proc/$(cat /tmp/pipeline.pid 2>/dev/null) 2>/dev/null || echo "No PID file"
```

### 2. Check Logs

```bash
# View recent logs
tail -f pipeline.log

# Check for specific errors
grep -i error pipeline.log | tail -n 50

# Check for completion
grep -i "complete\|finished" pipeline.log
```

### 3. Check Resources

```bash
# Memory usage
free -h

# Disk space
df -h

# CPU usage
top -n 1
```

### 4. Check Environment Variables

```bash
# Check if required env vars are set
echo $OPENAI_API_KEY | cut -c1-10  # First 10 chars only
echo $NEO4J_URI
echo $NEO4J_USER
echo $LOG_LEVEL
```

### 5. Test Pipeline Manually

```bash
# Try running pipeline.py directly
python -u pipeline.py --max-articles 1 --skip-enrichment

# Check for import errors
python -c "import pipeline; print('OK')"
```

## Container-Specific Issues

### DigitalOcean App Platform

**Check App Platform logs:**
- Go to DigitalOcean dashboard
- Navigate to your app
- Check "Runtime Logs" tab
- Look for:
  - Container restarts
  - OOM errors
  - Health check failures
  - Build/deploy errors

**Check resource limits:**
- App Platform → Your App → Settings
- Check CPU and Memory limits
- Increase if pipeline is being killed

**Check health checks:**
- Ensure health check endpoint is responding
- Health checks might be killing the container if they fail

### Kubernetes (if applicable)

```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name>

# Check resource limits
kubectl describe pod <pod-name> | grep -i "limits\|requests"
```

## Getting Help

1. **Collect logs:**
   ```bash
   # Save logs to a file
   tail -n 1000 pipeline.log > pipeline_error.log
   ```

2. **Check error patterns:**
   ```bash
   # Find common error patterns
   grep -i "error\|failed\|exception" pipeline.log | sort | uniq -c | sort -rn
   ```

3. **Enable DEBUG logging:**
   - Use the "Enable DEBUG level logging" option in the UI
   - This will show more detailed information

4. **Check system resources:**
   - Document memory/CPU usage when the error occurs
   - Check if it correlates with resource limits

