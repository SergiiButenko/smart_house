<?php
require '../../php/db.php';
try{
    // Use in the "Post-Receive URLs" section of your GitHub repo.
	switch($_SERVER['REQUEST_METHOD'])
	{
	case 'GET': $the_request = &$_GET; 
	foreach (statuses($_GET['name']) as $key => $value) {
  		echo $key . ": status: " . $value['status'] . "; settings: " . $value['settings'];
  		echo "<br>";
 		}
	break;
	case 'POST': $the_request = &$_POST; break;
	default:
       echo "Works fine.";
	}
	print_r($the_request);
} catch ( Exception $e ) {
    echo $e->getMessage();
  }
?>
