<?php
// Use in the "Post-Receive URLs" section of your GitHub repo.
if ( $_POST['payload'] ) {
  echo 'Executed: ';
  shell_exec('sh ~/conditioner_update_frontend.sh');
}
?>Done!