<?php
try{
    switch($_SERVER['REQUEST_METHOD']) {
	case 'GET': 
        $headerStringValue = $_SERVER['HTTP_X_ACTION'];
        if ($headerStringValue == '' or $headerStringValue == 'read'){
            echo json_encode(get_status($_GET['name'])); 
        } elseif ($headerStringValue == 'write') {
            set_status($_GET['name'], $_GET['status'], $_GET['settings']);
            echo json_encode(get_status($_GET['name']));
        } else {
            echo "incorrect X-ACTION header value";
        }
        break;
	default:
       echo "Works fine.";
	}
} catch ( Exception $e ) {
    echo $e->getMessage();
  }


function get_status($name="all") {
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

function set_status($name, $status, $settings) {
    // Connect to database server 
    mysql_connect("192.168.1.104:3306", "php_user", "password") or die (mysql_error());
    // Select database
    mysql_select_db("test") or die(mysql_error());
    // SQL query
    $strSQL = "UPDATE conditioners SET ";
	$status != null ? $strSQL .= "status=".$status : '';
	$settings != null ? $strSQL .= ", settings='".$settings."'" : '';
	$strSQL .= " WHERE name='".$name."'";
    // Execute the query (the recordset $rs contains the result)
    // Close the database connection
    mysql_query($strSQL);
    mysql_close();
}

?>
