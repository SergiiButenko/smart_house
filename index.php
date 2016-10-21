<html>
<head>
<title>Contidioners statuses</title>
</head>
<body>
<?php 
 require 'php/db.php';
 require 'php/check_mobile.php';
 
 foreach (statuses() as $key => $value) {
  echo $key . ": status: " . $value['status'] . "; settings: " . $value['settings'];
  echo "<br>";
 }
  
  echo "<br>";
  if (is_mobile()){
      echo 'It is mobile'; 
    } else {
      echo 'No mobile browser detected.';
    } 
?>
<div data-role="page" id="demo-page" data-theme="d" data-url="demo-page">
    <div data-role="header" data-theme="b">
        <h1>Swipe left or right</h1>
        <a href="#left-panel" data-theme="d" data-icon="arrow-r" data-iconpos="notext" data-shadow="false" data-iconshadow="false" class="ui-icon-nodisc">Open left panel</a>
        <a href="#right-panel" data-theme="d" data-icon="arrow-l" data-iconpos="notext" data-shadow="false" data-iconshadow="false" class="ui-icon-nodisc">Open right panel</a>
    </div><!-- /header -->
    <div data-role="content">
        <dl>
            <dt>Swipe <span>verb</span></dt>
            <dd><b>1.</b> to strike or move with a sweeping motion</dd>
        </dl>
        <a href="#demo-intro" data-rel="back" class="back-btn" data-role="button" data-mini="true" data-inline="true" data-icon="back" data-iconpos="right">Back to demo intro</a>
    </div><!-- /content -->
    <div data-role="panel" id="left-panel" data-theme="b">
        <p>Left reveal panel.</p>
        <a href="#" data-rel="close" data-role="button" data-mini="true" data-inline="true" data-icon="delete" data-iconpos="right">Close</a>
    </div><!-- /panel -->
    <div data-role="panel" id="right-panel" data-display="push" data-position="right" data-theme="c">
        <p>Right push panel.</p>
        <a href="#" data-rel="close" data-role="button" data-mini="true" data-inline="true" data-icon="delete" data-iconpos="right">Close</a>
    </div><!-- /panel -->
</div>

</body>
</html>
