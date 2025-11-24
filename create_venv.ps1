param(
    [string]$Name = ".venv",
    [string]$Python = "python",
    [switch]$Recreate
)

$fullPath = Join-Path (Get-Location) $Name

if (Test-Path $fullPath) {
    if ($Recreate) {
        Write-Host "Removing existing virtualenv '$Name'..."
        Remove-Item -Recurse -Force $fullPath
    }
    else {
        Write-Host "Virtual environment '$Name' already exists. Use -Recreate to recreate."
        exit 0
    }
}

Write-Host "Creating virtual environment '$Name' using executable: $Python"
# 使用 Start-Process 来避免解析歧义并取得退出码
$proc = Start-Process -FilePath $Python -ArgumentList '-m', 'venv', $fullPath -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Error "Failed to create virtual environment. Check Python availability or permissions. (ExitCode: $($proc.ExitCode))"
    exit $proc.ExitCode
}
Write-Host "Virtual environment '$Name' created successfully."
Write-Host 'Activation instructions:'
Write-Host ('  PowerShell: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force;') ('.\' + $Name + '\Scripts\Activate.ps1')
Write-Host ('  CMD:') ($Name + '\Scripts\activate.bat')


