<?php
require '../../php/db.php';
try{
    // Use in the "Post-Receive URLs" section of your GitHub repo.
	switch($_SERVER['REQUEST_METHOD'])
	{
	case 'GET': 
	$the_request = &$_GET; 
	print_r($the_request);
	$test = statuses($the_request['name']);
		echo "test ";
		print_r($test);
	foreach (statuses($the_request['name']) as $key => $value) {
  		echo $key . ": status: " . $value['status'] . "; settings: " . $value['settings'];
  		echo "<br>";
 		}
	break;
	case 'POST': $the_request = &$_POST; break;
	default:
       echo "Works fine.";
	}
} catch ( Exception $e ) {
    echo $e->getMessage();
  }
?>
