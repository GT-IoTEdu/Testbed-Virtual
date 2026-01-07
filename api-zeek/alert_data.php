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
$logDir = '/usr/local/spool/zeek/';

// --- VALIDAÇÃO DE LOG ---
$validLogs = ['notice.log', 'http.log', 'dns.log', 'conn.log', 'ssl.log', 'files.log', 'weird.log', 'reporter.log'];
if (!in_array($logfile, $validLogs)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid log file']);
    exit;
}

$logFile = $logDir . $logfile;
if (!file_exists($logFile)) {
    http_response_code(404);
    echo json_encode(['error' => 'Log file not found']);
    exit;
}

// --- FUNÇÃO PARA PARSEAR TSV DO ZEEK ---
function parseZeekLog($filepath, $maxlines) {
    $lines = file($filepath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $fields = [];
    $types = [];
    $data = [];

    foreach ($lines as $line) {
        if (strpos($line, '#fields') === 0) {
            $fields = explode("\t", substr($line, 8));
            continue;
        }
        if (strpos($line, '#types') === 0) {
            $types = explode("\t", substr($line, 7));
            continue;
        }
        if ($line[0] === '#') continue; // ignora metadados
        if (empty($fields)) continue;

        $cols = explode("\t", $line);
        $row = [];
        foreach ($fields as $i => $field) {
            $value = $cols[$i] ?? null;
            if ($value === '-' || $value === '(empty)') $value = null;

            // Converte tipos básicos
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
        if (count($data) >= $maxlines) break;
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
