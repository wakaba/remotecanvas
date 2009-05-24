<?php
if (!isset($_SERVER['PHP_AUTH_USER'])) {
    header("WWW-Authenticate: Basic realm=\"Remote Canvas / Hatena Haiku\"");
    header("HTTP/1.0 401 Unauthorized");
    echo "401\n";
    exit;
} else {
    foreach (array(
      "SERVER_NAME", "SCRIPT_NAME", "QUERY_STRING",
      "REQUEST_METHOD",
      "HTTP_REFERER", "HTTP_USER_AGENT", "HTTP_X_DATA_URL",
      "PHP_AUTH_USER", "PHP_AUTH_PW",
    ) as $n) {
      putenv($n . '=' . $_SERVER[$n]);
    }
#    $boundary = md5(rand() . rand());
#    putenv('BOUNDARY=' . $boundary);
#    header("Content-Type: multipart/form-data; boundary=" . $boundary);
    putenv('VIA_PHP_PROXY=1');
    $result = exec ('perl server.cgi');
    if ($result == 401) {
      header("WWW-Authenticate: Basic realm=\"Remote Canvas / Hatena Haiku\"");
      header("HTTP/1.0 401 Unauthorized");
    }
}
?>
