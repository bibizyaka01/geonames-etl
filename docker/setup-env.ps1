$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectDir '.env'
$templatePath = Join-Path $projectDir '.env.example'

function New-RandomBytes([int]$Count) {
    $buffer = New-Object byte[] $Count
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($buffer) } finally { $generator.Dispose() }
    return ,$buffer
}

if (Test-Path -LiteralPath $envPath) {
    $content = [System.IO.File]::ReadAllText($envPath)
} else {
    $content = [System.IO.File]::ReadAllText($templatePath)
}

# Add new settings from the template without replacing existing values.
foreach ($line in [System.IO.File]::ReadAllLines($templatePath)) {
    if ($line -match '^([A-Z][A-Z0-9_]*)=') {
        $settingName = $Matches[1]
        if ($content -notmatch "(?m)^$settingName=") {
            $content = $content.TrimEnd() + "`n" + $line + "`n"
        }
    }
}

foreach ($settingName in @('DWH_PASSWORD', 'AIRFLOW_DB_PASSWORD',
    'AIRFLOW_ADMIN_PASSWORD', 'AIRFLOW_JWT_SECRET', 'AIRFLOW_API_SECRET_KEY',
    'AIRFLOW_FERNET_KEY')) {
    $blankPattern = "(?m)^$settingName=[ \t]*\r?$"
    if ($content -match $blankPattern) {
        $bytes = New-RandomBytes 32
        if ($settingName -eq 'AIRFLOW_FERNET_KEY') {
            $secretValue = [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_')
        } else {
            $secretValue = ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
        }
        $content = [regex]::Replace($content, $blankPattern, "$settingName=$secretValue")
    }
}

# Credentials are interpolated into PostgreSQL URIs; reject unescaped characters.
foreach ($settingName in @('DWH_USER', 'DWH_DB', 'DWH_PASSWORD',
    'AIRFLOW_DB_USER', 'AIRFLOW_DB', 'AIRFLOW_DB_PASSWORD')) {
    if ($content -notmatch "(?m)^$settingName=[A-Za-z0-9_-]+\r?$") {
        throw "$settingName must contain only ASCII letters, digits, underscores or hyphens."
    }
}

[System.IO.File]::WriteAllText($envPath, $content.Replace("`r`n", "`n"),
    [System.Text.UTF8Encoding]::new($false))
Write-Host 'Local .env is ready. Existing non-empty settings were preserved.'
