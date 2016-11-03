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
         	set_src(img, JSON.parse(data)[img.id].status);		
	    }
      });	  
}


function turn_on_off(img) {
// make it look like a waiting button
$(img.id).unbind('click');

$.ajax({
         url: "http://butenko.asuscomm.com/api/v1",
         data: { name: img.id },
         type: "GET",
		 headers: {'X_ACTION':'turn_on_off'},
         success: function(data) { 
         	set_src(img, JSON.parse(data)[img.id].status);
	     },
	     complete: function() {
            $(img.id).bind('click'); // will fire either on success or error
         }
      });
}

function set_conditioner_status(img, status, settings){
	$.ajax({
         url: "http://butenko.asuscomm.com/api/v1",
         data: { name: img.id, status: status, settings: settings},
         type: "GET",
		 headers: {'X_ACTION':'write'},
         success: function(data) { 
         	set_src(JSON.parse(data)[img.id].status);
	    }
      });
}

function set_src(img, status){
if (status == 0)
	img.src = "images/airmoving_static.gif";
else 
	img.src = "images/airmoving.gif";
}
