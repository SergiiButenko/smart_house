<?php
try{
    // Use in the "Post-Receive URLs" section of your GitHub repo.
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
      shell_exec('sh /ffp/home/root/git-hook/conditioner_update_frontend.sh >> /ffp/home/root/git-hook/logs/"$(date +%F_%R)_log" 2>&1');
      echo 'Updated!';
    } else {
        echo "Works fine.";
    }
} catch ( Exception $e ) {
    echo $e->getMessage();
  }
?>
