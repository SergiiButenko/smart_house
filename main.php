<html>
<head>
<title>Retrieve data from database 2</title>
</head>
<body>
<?php 
require 'php/db.php';
foreach (statuses() as $key => $value) {
 echo $key . ": " . print_r($value) . '</br>';
}
?>
</body>
</html>
