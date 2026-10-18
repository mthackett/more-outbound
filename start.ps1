
# More Outbound - Local Development Launcher

$projectDir = $PSScriptRoot
$streamlitExe = Join-Path $projectDir ".venv\Scripts\streamlit.exe"
$appPath = Join-Path $projectDir "job_pipeline\adapters\primary\app.py"
$url = "http://localhost:8501"

# Verify local environment
if (-not (Test-Path $streamlitExe)) {
    Write-Error "Streamlit not found. Create the virtual environment and install dependencies first."
    exit 1
}

# Launch More Outbound server
Write-Host "Launching More Outbound local dev server..."

Add-Type -AssemblyName System.Net.Http

Start-Process `
    -FilePath $streamlitExe `
    -ArgumentList "run", "--logger.level=debug", "`"$appPath`"" `
    -WorkingDirectory $projectDir

# Wait until Streamlit is ready
Write-Host "Waiting for Streamlit server..."

$client = [System.Net.Http.HttpClient]::new()
$client.Timeout = [TimeSpan]::FromMilliseconds(200)

$ready = $false
$timer = [System.Diagnostics.Stopwatch]::StartNew()

try {
    while (-not $ready -and $timer.Elapsed.TotalSeconds -lt 30) {
        try {
            $response = $client.GetAsync(
                "$url/_stcore/health"
            ).GetAwaiter().GetResult()

            $ready = $response.IsSuccessStatusCode
            $response.Dispose()
        }
        catch {
            Start-Sleep -Milliseconds 100
        }
    }
}
finally {
    $client.Dispose()
    $timer.Stop()
}

if ($ready) {
    Write-Host "Streamlit ready in $([math]::Round($timer.Elapsed.TotalSeconds, 2)) seconds."
    Start-Process "chrome.exe" -ArgumentList "--new-tab", $url
}
else {
    Write-Warning "Streamlit did not respond within 30 seconds."
}
