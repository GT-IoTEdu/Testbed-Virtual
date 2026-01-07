# Script de teste para IoT-EDU (Windows PowerShell)
# Uso: .\test_windows.ps1

param(
    [string]$BaseUrl = "https://sp-python.cafeexpresso.rnp.br"
)

# Configurações
$Timeout = 10
$TotalTests = 0
$PassedTests = 0

# Função para log colorido
function Write-Log {
    param(
        [string]$Message,
        [string]$Color = "Green"
    )
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

# Função para testar endpoint
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "Testando $Name... " -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Timeout -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✅ OK" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ FALHOU (Status: $($response.StatusCode), esperado: $ExpectedStatus)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ FALHOU" -ForegroundColor Red
        return $false
    }
}

# Função para testar JSON response
function Test-JsonEndpoint {
    param(
        [string]$Url,
        [string]$Name,
        [string]$ExpectedField
    )
    
    Write-Host "Testando $Name (JSON)... " -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Timeout -ErrorAction Stop
        $content = $response.Content
        
        if ($content -match $ExpectedField) {
            Write-Host "✅ OK" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ FALHOU" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ FALHOU" -ForegroundColor Red
        return $false
    }
}

# Função para testar SSL
function Test-SslCertificate {
    Write-Host "Testando certificado SSL... " -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec $Timeout -ErrorAction Stop
        Write-Host "✅ Certificado SSL válido" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Problema com certificado SSL" -ForegroundColor Red
        return $false
    }
}

# Função para testar performance
function Test-Performance {
    Write-Host "Testando performance... " -NoNewline
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec $Timeout -ErrorAction Stop
        $stopwatch.Stop()
        $responseTime = $stopwatch.Elapsed.TotalSeconds
        
        if ($responseTime -lt 2.0) {
            Write-Host "✅ Performance OK (${responseTime}s)" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Performance lenta (${responseTime}s)" -ForegroundColor Yellow
        }
        return $true
    } catch {
        Write-Host "❌ Falha no teste de performance" -ForegroundColor Red
        return $false
    }
}

# Função principal
function Main {
    Write-Log "🚀 Teste Rápido - IoT-EDU" "Cyan"
    Write-Log "🌐 URL Base: $BaseUrl" "Cyan"
    Write-Log "⏰ Timestamp: $(Get-Date)" "Cyan"
    Write-Host "==================================" -ForegroundColor Cyan
    
    # 1. Teste básico de conectividade
    Write-Log "1. Testando conectividade básica..." "Blue"
    $script:TotalTests++
    if (Test-Endpoint -Url $BaseUrl -Name "Acesso básico") {
        $script:PassedTests++
    }
    
    # 2. Teste de health check
    Write-Log "2. Testando health check..." "Blue"
    $script:TotalTests++
    if (Test-JsonEndpoint -Url "$BaseUrl/health" -Name "Health check" -ExpectedField "status") {
        $script:PassedTests++
    }
    
    # 3. Teste da documentação
    Write-Log "3. Testando documentação da API..." "Blue"
    $script:TotalTests++
    if (Test-Endpoint -Url "$BaseUrl/docs" -Name "Documentação") {
        $script:PassedTests++
    }
    
    # 4. Teste de metadados SAML
    Write-Log "4. Testando metadados SAML..." "Blue"
    $script:TotalTests++
    if (Test-Endpoint -Url "$BaseUrl/saml2/metadata/" -Name "Metadados SAML") {
        $script:PassedTests++
    }
    
    # 5. Teste de status de autenticação
    Write-Log "5. Testando status de autenticação..." "Blue"
    $script:TotalTests++
    if (Test-JsonEndpoint -Url "$BaseUrl/auth/status" -Name "Status de autenticação" -ExpectedField "status") {
        $script:PassedTests++
    }
    
    # 6. Teste de endpoints da API
    Write-Log "6. Testando endpoints da API..." "Blue"
    
    # 6.1 Listagem de dispositivos
    $script:TotalTests++
    if (Test-JsonEndpoint -Url "$BaseUrl/api/devices/" -Name "Listagem de dispositivos" -ExpectedField "status") {
        $script:PassedTests++
    }
    
    # 6.2 Listagem de aliases
    $script:TotalTests++
    if (Test-JsonEndpoint -Url "$BaseUrl/api/devices/aliases/" -Name "Listagem de aliases" -ExpectedField "status") {
        $script:PassedTests++
    }
    
    # 6.3 Servidores DHCP
    $script:TotalTests++
    if (Test-JsonEndpoint -Url "$BaseUrl/api/devices/dhcp/servers" -Name "Servidores DHCP" -ExpectedField "status") {
        $script:PassedTests++
    }
    
    # 7. Teste de SSL
    Write-Log "7. Testando certificado SSL..." "Blue"
    $script:TotalTests++
    if (Test-SslCertificate) {
        $script:PassedTests++
    }
    
    # 8. Teste de performance
    Write-Log "8. Testando performance..." "Blue"
    $script:TotalTests++
    if (Test-Performance) {
        $script:PassedTests++
    }
    
    # 9. Teste de erro 404
    Write-Log "9. Testando tratamento de erro 404..." "Blue"
    $script:TotalTests++
    if (Test-Endpoint -Url "$BaseUrl/api/endpoint-inexistente" -Name "Erro 404" -ExpectedStatus 404) {
        $script:PassedTests++
    }
    
    # Relatório final
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host "📋 RELATÓRIO FINAL" -ForegroundColor Cyan
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host "Total de testes: $TotalTests"
    Write-Host "Testes aprovados: $PassedTests"
    Write-Host "Testes reprovados: $($TotalTests - $PassedTests)"
    Write-Host "Taxa de sucesso: $([math]::Round(($PassedTests * 100 / $TotalTests), 1))%"
    
    if ($PassedTests -eq $TotalTests) {
        Write-Host ""
        Write-Log "🎉 TODOS OS TESTES PASSARAM!" "Green"
        Write-Log "A aplicação está funcionando corretamente." "Green"
        exit 0
    } elseif ($PassedTests -ge ($TotalTests * 0.8)) {
        Write-Host ""
        Write-Log "⚠️ A maioria dos testes passou." "Yellow"
        Write-Log "Verifique os endpoints que falharam." "Yellow"
        exit 1
    } else {
        Write-Host ""
        Write-Log "❌ Muitos testes falharam." "Red"
        Write-Log "Verifique a configuração da aplicação." "Red"
        exit 2
    }
}

# Verificar se estamos no PowerShell
if ($PSVersionTable.PSVersion.Major -lt 3) {
    Write-Log "❌ PowerShell 3.0 ou superior é necessário." "Red"
    exit 1
}

# Executar testes
Main 