<?php
try{
    // Use in the "Post-Receive URLs" section of your GitHub repo.
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
      shell_exec('~/git-hook/conditioner_update_frontend.sh >> ~/git-hook/logs/"$(date +%F_%R)_log"');
      echo 'Updated!';
    } else {
        echo "Works fine.";
    }
} catch ( Exception $e ) {
    echo $e->getMessage();
  }
?>
