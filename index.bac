<html>
<head>
<title>Contidioners statuses</title>
</head>
<body>
<?php 
 require 'php/db.php';
 require 'php/check_mobile.php';
 
 foreach (statuses() as $key => $value) {
  echo $key . ": status: " . $value['status'] . "; settings: " . $value['settings'];
  echo "<br>";
 }
  
  echo "<br>";
  if (is_mobile()){
      echo 'It is mobile'; 
    } else {
      echo 'No mobile browser detected.';
    } 
?>
</body>
</html>
