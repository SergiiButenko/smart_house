<html>
<head>
<title>Retrieve data from database 2</title>
</head>
<body>
<?php 
require 'php/db.php';
$varr = statuses();
print_r($varr);
?>
</body>
</html>
