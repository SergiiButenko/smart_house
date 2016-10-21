<html>
<head>
<title>Contidioners statuses</title>
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
