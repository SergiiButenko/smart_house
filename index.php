<html>
<head>
<title>Retrieve data from database </title>
</head>
<body>
<?php
// Connect to database server 
mysql_connect("192.168.1.104:3306", "php_user", "password") or die (mysql_error());
// Select database
mysql_select_db("test") or die(mysql_error());
// SQL query
$strSQL = "SELECT * FROM new_table";
echo "Sql string: $strSQL";

// Execute the query (the recordset $rs contains the result)
$rs = mysql_query($strSQL);
// Loop the recordset $rs
// Each row will be made into an array ($row) using mysql_fetch_array
while($row = mysql_fetch_array($rs)) {
// Write the value of the column FirstName (which is now in the array $row)
echo $row['id'] . ":" . $row['value'] . "</br>";
}
// Close the database connection
mysql_close();
?>
</body>
</html>
