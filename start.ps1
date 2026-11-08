$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
try {
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker was not found. Install and start Docker Desktop, then rerun .\start.ps1."
}

if (-not (Test-Path ".env")) {
    $envTemplate = Join-Path $PSScriptRoot ".env.example"
    if (-not (Test-Path $envTemplate)) {
        throw "Missing .env.example."
    }

    $template = [System.IO.File]::ReadAllText($envTemplate)
    if ($template -notmatch "(?m)^SECRET_KEY=.*$" -or
        $template -notmatch "(?m)^POSTGRES_PASSWORD=.*$" -or
        $template -notmatch "(?m)^DATABASE_URL=.*$") {
        throw ".env.example is missing required settings."
    }

    function New-RandomHex([int] $byteCount) {
        $bytes = New-Object byte[] $byteCount
        $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        try {
            $generator.GetBytes($bytes)
        }
        finally {
            $generator.Dispose()
        }
        return [System.BitConverter]::ToString($bytes).Replace("-", "").ToLowerInvariant()
    }

    $secretKey = New-RandomHex 32
    $databasePassword = New-RandomHex 24
    $databaseUrl = "DATABASE_URL=postgresql+psycopg://flatmate:$databasePassword@127.0.0.1:5432/flatmate"
    $template = [regex]::Replace($template, "(?m)^SECRET_KEY=.*$", "SECRET_KEY=$secretKey")
    $template = [regex]::Replace(
        $template,
        "(?m)^POSTGRES_PASSWORD=.*$",
        "POSTGRES_PASSWORD=$databasePassword"
    )
    $template = [regex]::Replace($template, "(?m)^DATABASE_URL=.*$", $databaseUrl)
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot ".env"), $template, $encoding)
    Write-Host "Created local .env with random secrets."
}
else {
    Write-Host "Using existing .env; its contents were not changed."
}

docker compose up --build
if ($LASTEXITCODE -ne 0) {
    throw "docker compose failed with exit code $LASTEXITCODE."
}
}
finally {
    Pop-Location
}
