# PowerShell helper script to run docker-compose from root directory
Set-Location deployment
& docker-compose @args 