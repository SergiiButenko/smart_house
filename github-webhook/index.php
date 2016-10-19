<?php
// Use in the "Post-Receive URLs" section of your GitHub repo.
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  echo 'Executed: ';
  shell_exec('~/conditioner_update_frontend.sh >> ~/"$(date +%F_%R)_log"');`
}
?>Done! 
