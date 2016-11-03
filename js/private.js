$( document ).ready(function() {
  	document.getElementById("hall").src = set_image_path(document.getElementById("hall"));
	document.getElementById("kids").src = set_image_path(document.getElementById("kids"));
	document.getElementById("bedroom").src = set_image_path(document.getElementById("bedroom"));
    });


function turn_on_off(img) {
$.get("http://butenko.asuscomm.com/api/v1", {name: img.id})
		.done(function(data) {
		  cond = JSON.parse(data)[img.id];
		  set_conditioner_status(!cond.status);
		  set_image_path(img);
		});
}

function set_image_path(img) {
	$.get("http://butenko.asuscomm.com/api/v1", {name: img.id})
		.done(function(data) {
		  cond = JSON.parse(data)[img.id];		
		  if (cond.status == 0)
    			img.src = "images/airmoving_static.gif";
		  else 
    			img.src = "images/airmoving.gif";
		});
		  
}

function set_conditioner_status(id, status, settings){
	$.ajax({
	   url: "http://butenko.asuscomm.com/api/v1",
	   type: 'PUT',
	   headers: {"X-HTTP-Method-Override": "PUT"},
	   data: "name="+id+"&status="+status+"&settings="+settings,
	   success: function(data) {
	     cond = JSON.parse(data)[id];
	      alert(cond.status);
	   }
});
}