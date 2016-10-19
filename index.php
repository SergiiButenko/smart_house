<html>
<head>
<title>Retrieve data from database </title>
</head>
<body>
<?php
// Connect to database server 
$servername = $_ENV["DB_HOST"].":".$_ENV["DB_PORT"];
$username = $_ENV["DB_USERNAME"];
$password = $_ENV["DB_PASS"];
mysql_connect($servername, $username, $password) or die (mysql_error());

// Select database
mysql_select_db($_ENV["DB_NAME"]) or die(mysql_error());

// SQL query
$strSQL = "SELECT * FROM new_table";
echo "Sql string: $strSQL"."</br>";

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
