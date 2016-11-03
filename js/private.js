$( document ).ready(function() {
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

function get_image_path(img) {
	$.get("http://butenko.asuscomm.com/api/v1", {name: img.id})
		.done(function(data) {
		  cond = JSON.parse(data)[img.id];
		  if (cond.status == 0)
    			img.src = "images/airmoving_static.gif";
		  else 
    			img.src = "images/airmoving.gif";
		});
}