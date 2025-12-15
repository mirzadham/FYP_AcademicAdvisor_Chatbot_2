# Gemini API Setup Helper Script
# This script helps you create your .env file with your API key

# Check if .env already exists
if (Test-Path .env) {
    Write-Host "⚠️  .env file already exists!" -ForegroundColor Yellow
    $response = Read-Host "Do you want to overwrite it? (y/n)"
    if ($response -ne "y") {
        Write-Host "Setup cancelled." -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Gemini API Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "To get your API key:" -ForegroundColor Green
Write-Host "1. Visit: https://makersuite.google.com/app/apikey"
Write-Host "2. Sign in with your Google account"
Write-Host "3. Click 'Create API Key'"
Write-Host "4. Copy the API key"
Write-Host ""

$apiKey = Read-Host "Enter your Gemini API key"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "❌ API key cannot be empty!" -ForegroundColor Red
    exit
}

# Create .env file
$envContent = "# Gemini API Configuration`nGEMINI_API_KEY=$apiKey"
Set-Content -Path ".env" -Value $envContent

Write-Host ""
Write-Host "✅ .env file created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update your domain.yml to include 'action_gemini_response'"
Write-Host "2. Run: rasa run actions"
Write-Host "3. Test your bot with: rasa shell"
Write-Host ""
Write-Host "⚠️  IMPORTANT: Never commit your .env file to git!" -ForegroundColor Yellow
