<?php
// /usr/local/www/zeek-api/alert_data.php
header('Content-Type: application/json');

// --- AUTENTICAÇÃO ---
$apiKey = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
if ($apiKey !== 'Bearer y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp') {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// --- PARÂMETROS ---
$logfile = $_POST['logfile'] ?? $_GET['logfile'] ?? 'notice.log';
$maxlines = (int)($_POST['maxlines'] ?? $_GET['maxlines'] ?? 50);
$logDir = '/usr/local/zeek/logs/current/';

// --- VALIDAÇÃO DE LOG ---
$validLogs = ['notice.log', 'http.log', 'dns.log', 'conn.log', 'ssl.log', 'files.log', 'weird.log', 'reporter.log', 'stats.log'];
if (!in_array($logfile, $validLogs)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid log file: ' . $logfile . '. Valid logs: ' . implode(', ', $validLogs)]);
    exit;
}

// Handle .gz compressed files
$logFile = $logDir . $logfile;
$logFileGz = $logFile . '.gz';

if (file_exists($logFileGz)) {
    // Use compressed file
    $logFile = 'compress.zlib://' . $logFileGz;
} elseif (!file_exists($logFile)) {
    http_response_code(404);
    echo json_encode(['error' => 'Log file not found. Checked: ' . $logFile . ' and ' . $logFileGz]);
    exit;
}

// --- FUNÇÃO PARA PARSEAR TSV DO ZEEK ---
function parseZeekLog($filepath, $maxlines) {
    $lines = file($filepath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if ($lines === false) {
        return ['error' => 'Cannot read log file'];
    }
    
    $fields = [];
    $types = [];
    $data = [];

    foreach ($lines as $line) {
        // Skip comment lines
        if ($line[0] === '#') {
            // Parse headers for TSV format
            if (strpos($line, '#fields') === 0) {
                $fields = explode("\t", substr($line, 8));
                continue;
            }
            if (strpos($line, '#types') === 0) {
                $types = explode("\t", substr($line, 7));
                continue;
            }
            continue;
        }
        
        // Try to parse as JSON first
        $decoded = json_decode($line, true);
        if ($decoded !== null && is_array($decoded)) {
            // Successfully parsed JSON line
            $data[] = $decoded;
        } elseif (!empty($fields) && strpos($line, "\t") !== false) {
            // Parse as TSV (fallback to original logic)
            $cols = explode("\t", $line);
            $row = [];
            foreach ($fields as $i => $field) {
                $value = $cols[$i] ?? null;
                if ($value === '-' || $value === '(empty)') $value = null;

                // Convert basic types
                if (isset($types[$i])) {
                    switch ($types[$i]) {
                        case 'count':
                        case 'port':
                            $value = $value !== null ? (int)$value : null;
                            break;
                        case 'double':
                            $value = $value !== null ? (float)$value : null;
                            break;
                        case 'time':
                            if ($value !== null) $value = ['raw' => (float)$value, 'iso' => gmdate('c', (int)$value)];
                            break;
                        case 'set[enum]':
                        case 'set[string]':
                            if ($value !== null) $value = array_map('trim', explode(',', $value));
                            break;
                    }
                }
                $row[$field] = $value;
            }
            $data[] = $row;
        }
        
        if (count($data) >= $maxlines) {
            break;
        }
    }
    return $data;
}

// --- EXECUTA O PARSE ---
$parsedLines = parseZeekLog($logFile, $maxlines);

// --- RETORNO JSON ---
echo json_encode([
    'success' => true,
    'logfile' => $logfile,
    'maxlines' => $maxlines,
    'total_lines' => count($parsedLines),
    'data' => $parsedLines
]);
?>
