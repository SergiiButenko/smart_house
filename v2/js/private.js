$( document ).ready(function() {
	alert(get_image_path(document.getElementById("hall")));
  	document.getElementById("hall").src = get_image_path(document.getElementById("hall"));
	document.getElementById("kids").src = get_image_path(document.getElementById("kids"));
	document.getElementById("bedroom").src = get_image_path(document.getElementById("bedroom"));
    });



function changeImagePath(img) {
	if (img.src.match(/airmoving.gif/))
    	img.src = "../images/airmoving_static.gif";
	else if (img.src.match(/airmoving_static.gif/))
    	img.src = "../images/airmoving.gif";
   }

 function get_image_path(img){
 	var xmlHttp = new XMLHttpRequest();
 	alert("http://butenko.asuscomm.com/api/v1?name="+img.id);
    xmlHttp.open( "GET", "http://butenko.asuscomm.com/api/v1?name="+img.id, true ); // false for synchronous request
    var reponce = xmlHttp.send(null);
    alert(reponce);
    reponce = JSON.parse(reponce);
    alert(reponce);
    if (reponce.status == 1)
    	img.src = "../images/airmoving_static.gif";
	else 
    	img.src = "../images/airmoving.gif";
 }