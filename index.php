<html>
<head>
<title>Retrieve data from database</title>
</head>
<body>
<?php 
 require 'php/db.php';
 foreach (statuses() as $key => $value) {
  echo $key . ": status: " . $value['status'] . "; settings: " . $value['settings'];
  echo "<br>";
}
?>
</body>
</html>
