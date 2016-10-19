<?php
// Use in the "Post-Receive URLs" section of your GitHub repo.
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  echo 'Executed: ';
  shell_exec('sh ~/conditioner_update_frontend.sh >> log');
}
?>Done!
