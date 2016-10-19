<?php
// Use in the "Post-Receive URLs" section of your GitHub repo.
if ( $_POST['payload'] ) {
  shell_exec('sh ~/conditioner_update_frontend.sh');
}
?>hi
