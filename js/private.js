$( document ).ready(function() {
  	set_image_path(document.getElementById("hall"));
	set_image_path(document.getElementById("kids"));
	set_image_path(document.getElementById("bedroom"));
    });

function set_image_path(img) {
	  $.ajax({
         url: "http://butenko.asuscomm.com/api/v1",
         data: {name: img.id},
         type: "GET",
         success: function(data) { 
         	set_src(JSON.parse(data)[img.id].status);		
	    }
      });	  
}


function turn_on_off(img) {
$.ajax({
         url: "http://butenko.asuscomm.com/api/v1",
         data: { name: id },
         type: "GET",
		 headers: {'X_ACTION':'turn_on_off'},
         success: function(data) { 
         	set_src(JSON.parse(data)[id].status);
	    }
      });


$.get("http://butenko.asuscomm.com/api/v1", {name: img.id})
		.done(function(data) {
		  cond = JSON.parse(data)[img.id];
		  cond.status == 1 ? revers = 0 : revers = 1;
		  set_conditioner_status(img.id, revers);
		});
}

function set_conditioner_status(id, status, settings){
	$.ajax({
         url: "http://butenko.asuscomm.com/api/v1",
         data: { name: id, status: status, settings: settings},
         type: "GET",
		 headers: {'X_ACTION':'write'},
         success: function(data) { 
         	set_src(JSON.parse(data)[id].status);
	    }
      });
}


function chng_src_to_oposite(img){
if (img.src == "images/airmoving_static.gif")
	img.src = "images/airmoving.gif";

if (img.src == "images/airmoving.gif")
	img.src = "images/airmoving_static.gif";
}

function set_src(status){
if (status == 0)
	img.src = "images/airmoving_static.gif";
else 
	img.src = "images/airmoving.gif";
}
