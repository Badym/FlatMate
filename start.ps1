$ErrorActionPreference = "Stop"

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

function Get-EnvValue([string] $content, [string] $name) {
    $match = [regex]::Match($content, "(?m)^$([regex]::Escape($name))=([^\r\n]*)\r?$")
    if ($match.Success) {
        return $match.Groups[1].Value
    }
    return $null
}

function Set-EnvValue([string] $content, [string] $name, [string] $value) {
    $pattern = "(?m)^$([regex]::Escape($name))=[^\r\n]*(?=\r?$)"
    if ([regex]::IsMatch($content, $pattern)) {
        return [regex]::Replace($content, $pattern, "$name=$value")
    }
    return $content.TrimEnd() + "`n$name=$value`n"
}

Push-Location $PSScriptRoot
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker was not found. Install and start Docker Desktop, then rerun .\start.ps1."
    }

    $generatedDemoPassword = $false
    if (-not (Test-Path ".env")) {
        $envTemplate = Join-Path $PSScriptRoot ".env.example"
        if (-not (Test-Path $envTemplate)) {
            throw "Missing .env.example."
        }

        $template = [System.IO.File]::ReadAllText($envTemplate)
        if ($template -notmatch "(?m)^SECRET_KEY=[^\r\n]*\r?$" -or
            $template -notmatch "(?m)^POSTGRES_PASSWORD=[^\r\n]*\r?$" -or
            $template -notmatch "(?m)^DATABASE_URL=[^\r\n]*\r?$" -or
            $template -notmatch "(?m)^DEMO_PASSWORD=[^\r\n]*\r?$") {
            throw ".env.example is missing required settings."
        }

        $secretKey = New-RandomHex 32
        $databasePassword = New-RandomHex 24
        $demoPassword = New-RandomHex 24
        $databaseUrl = "DATABASE_URL=postgresql+psycopg://flatmate:$databasePassword@127.0.0.1:5432/flatmate"
        $template = [regex]::Replace($template, "(?m)^SECRET_KEY=[^\r\n]*(?=\r?$)", "SECRET_KEY=$secretKey")
        $template = [regex]::Replace(
            $template,
            "(?m)^POSTGRES_PASSWORD=[^\r\n]*(?=\r?$)",
            "POSTGRES_PASSWORD=$databasePassword"
        )
        $template = [regex]::Replace($template, "(?m)^DATABASE_URL=[^\r\n]*(?=\r?$)", $databaseUrl)
        $template = [regex]::Replace($template, "(?m)^DEMO_PASSWORD=[^\r\n]*(?=\r?$)", "DEMO_PASSWORD=$demoPassword")
        $encoding = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot ".env"), $template, $encoding)
        $generatedDemoPassword = $true
        Write-Host "Created local .env with random application, database, and demo passwords."
    }
    else {
        Write-Host "Using existing .env; application and database passwords are preserved."
    }

    $envPath = Join-Path $PSScriptRoot ".env"
    $environment = [System.IO.File]::ReadAllText($envPath)
    $demoPassword = Get-EnvValue $environment "DEMO_PASSWORD"
    if ([string]::IsNullOrWhiteSpace($demoPassword)) {
        $demoPassword = New-RandomHex 24
        $environment = Set-EnvValue $environment "DEMO_PASSWORD" $demoPassword
        $encoding = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::WriteAllText($envPath, $environment, $encoding)
        $generatedDemoPassword = $true
    }

    if ($generatedDemoPassword) {
        Write-Host "A demo password was generated and saved to .env as DEMO_PASSWORD."
    }

    $databaseUser = Get-EnvValue $environment "POSTGRES_USER"
    $databaseName = Get-EnvValue $environment "POSTGRES_DB"
    $databasePassword = Get-EnvValue $environment "POSTGRES_PASSWORD"
    if ([string]::IsNullOrWhiteSpace($databaseUser)) {
        $databaseUser = "flatmate"
    }
    if ([string]::IsNullOrWhiteSpace($databaseName)) {
        $databaseName = "flatmate"
    }
    if ([string]::IsNullOrWhiteSpace($databasePassword)) {
        throw "POSTGRES_PASSWORD is empty in .env. Set a database password and rerun .\start.ps1."
    }
    if ((Get-EnvValue $environment "APP_ENV") -ne "development") {
        throw "start.ps1 requires APP_ENV=development. Use the production deployment procedure for other environments."
    }

    docker compose up -d db
    if ($LASTEXITCODE -ne 0) {
        throw "Could not start PostgreSQL. Check Docker Desktop and the configured database port."
    }

    $safeUser = $databaseUser.Replace('"', '""')
    $safePassword = $databasePassword.Replace("'", "''")
    $sql = "ALTER ROLE `"$safeUser`" WITH PASSWORD '$safePassword';"
    $databaseReady = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        $sql | docker compose exec -T db psql -U $databaseUser -d postgres -v ON_ERROR_STOP=1 *> $null
        if ($LASTEXITCODE -eq 0) {
            $databaseReady = $true
            break
        }
        Start-Sleep -Seconds 2
    }
    if (-not $databaseReady) {
        throw "Could not synchronize the PostgreSQL password. No database data was deleted. Check docker compose logs db and verify that POSTGRES_USER matches the existing database owner."
    }

    docker compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT 1"' *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL still rejects the configured password. Check .env and database logs; no database data was deleted."
    }

    docker compose up --build -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose failed with exit code $LASTEXITCODE."
    }
    Write-Host "FlatMate is running. Use 'docker compose logs -f web' to follow logs."
}
finally {
    Pop-Location
}
