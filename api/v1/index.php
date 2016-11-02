<?php
try{
    // Use in the "Post-Receive URLs" section of your GitHub repo.
	switch($_SERVER['REQUEST_METHOD'])
	{
	case 'GET':
	json_encode(statuses($_GET['name'])
	break;

	case 'POST': $the_request = &$_POST; break;
	default:
       echo "Works fine.";
	}
} catch ( Exception $e ) {
    echo $e->getMessage();
  }


function statuses($name="all") {
    // Connect to database server 
    mysql_connect("192.168.1.104:3306", "php_user", "password") or die (mysql_error());
    // Select database
    mysql_select_db("test") or die(mysql_error());
    // SQL query
    if ($name == "all") {
    $strSQL = "SELECT * FROM conditioners";
    } else {
        $strSQL = "SELECT * FROM conditioners WHERE name='".$name."'";
    }
    // Execute the query (the recordset $rs contains the result)
    $rs = mysql_query($strSQL);

    $values = array();
    while($row = mysql_fetch_array($rs)) {
    $values[$row['name']] = array( 
        'status' => $row['status'],
        'settings' => $row['settings']
        );
    } 
    // Close the database connection
    mysql_close();
    return $values;
}

?>
