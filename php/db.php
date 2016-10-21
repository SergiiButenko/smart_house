<?php
function statuses() {
    // Connect to database server 
    mysql_connect("192.168.1.104:3306", "php_user", "password") or die (mysql_error());
    // Select database
    mysql_select_db("test") or die(mysql_error());
    // SQL query
    $strSQL = "SELECT * FROM conditioners";
    // Execute the query (the recordset $rs contains the result)
    $rs = mysql_query($strSQL);

    class values {};
    $values = new values();

    while($row = mysql_fetch_array($rs)) {
    $values->$row['name'];
        //
        //'status': $row['status'],
        //'settings': $row['settings']
        //
    } 
    // Close the database connection
    mysql_close();
    echo $values;
}

statuses();

?>
