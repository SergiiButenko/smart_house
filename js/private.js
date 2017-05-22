var aruino_ip='http://185.20.216.94:5555/';
//var aruino_ip='http://192.168.1.10/';
var arduino_check_connect_sec=6;
var arduino_check_broken_connect_sec=2;

var branch_names=[ '', // Arduino stars numeration from 1. So skiping 0 index
	'Первая ветка',
	'Вторая ветка',
	'Третья ветка',
	'Четвертая ветка',
	'',
	'',
	'Насос'
	];

$(document).ready(function(){
	//Rename branches
	for (var i = 1; i < branch_names.length; i++) {
	   $('#title-'+i+" span").text(branch_names[i]);
	}

	(function update_temperature() {
	  $.ajax({
	    url: "http://185.20.216.94:7542/weather", 
	    success: function(data) {
	    	alert(data['temperature']);
	    	$("#temp_header").text("Температура воздуха - "+data['temperature']+" C*");
	    }
	  });
	})();

	// Add labels for swticher values
	$('.switchers-main').bootstrapToggle({
		 on: 'Остановить Полив',
		 off: 'Начать полив'
	});

	// Add labels for swticher values
	$('.switchers-pump').bootstrapToggle({
		 on: 'Выключить насос',
		 off: 'Включить насос'
	});

	//Add arduino touch script to determine if connection is alive
	(function worker() {
	  $.ajax({
	    url: aruino_ip, 
	    beforeSend: function(xhr, opts){
	    	$("#arduino_status").text("connecting to arduino...");
	    	if ($('#time_modal').hasClass('in')){
	    		xhr.abort();
	    	}
	    }, 
	    success: function(data) {
	    	$('#loader').hide();
	    	console.log("connected to arduino");
	    	$("#arduino_status").text("connected to arduino");
	    	update_branches(data);
	    	setTimeout(worker, arduino_check_connect_sec*1000);     
	    },
	    error: function(){	    	
	    	console.error("Can't connect to arduino");
	    	$("#arduino_status").text("error connection to arduino");
	    	$('#loader').show()
	    	setTimeout(worker, arduino_check_broken_connect_sec*1000);     
	    }
	  });
	})();


   //Assign onClick for close buttons on Modal window
   $(".modal_close").click(function(){ 
   	    update_branches_request();
   });

   //Assign onChange for all switchers, so they open modal window
   $(".switchers-main, .switchers-pump").change(function(){ 
   	if ($(this).prop('checked') && $(this).data('user-action') == 1){
	   	index = $(this).data('id');
	   	name = branch_names[index];
	   	
	   	$('#time_modal').data('id', index);
	   	$('.modal-title').html(name);
	    $('#time_modal').modal('show');
	} 

	if (!$(this).prop('checked') && $(this).data('user-action') == 1){
	   	index = $(this).data('id');
	   	branch_off(index);
	}
   });

   //Function to start irrigation
   $(".start-irrigation").click(function(){ 
   	index = $('#time_modal').data('id');
   	branch_on(index);
   });

});

function branch_on(index){
	$.ajax({
	    url: aruino_ip+'/on', 
	    type: "get",
	    data: {
	    	'params' : index
	    },
	    beforeSend: function(req){ $('#loader').show()},
	    success: function(data) {
	      if (data['return_value']==0){
	      	   alert("Не могу включить "+branch_names[index]);
	   		   console.error('Line '+index+' cannot be activated');
	   		}

	    	if (data['return_value']==1){
	   		   console.log('Line '+index+' activated');
	   		}
	    },
	    error: function(){
	    	alert("Не могу включить "+branch_names[index]);
	    	console.error("Can't update "+branch_names[index]);
	    },
	    complete: function() {
	      update_branches_request();
	      $('#loader').hide();
	    }
	  });
}

function branch_off(index){
	$.ajax({
	    url: aruino_ip+'/off', 
	    type: "get",
	    data: {
	    	'params' : index
	    },
	    beforeSend: function(req){ $('#loader').show()},
	    success: function(data) {
			if (data['return_value']==1){
			   alert("Не могу включить "+branch_names[index]);
	   		   console.error('Line '+index+' cannot be deactivated');
	   		}

	    	if (data['return_value']==0){
	   		   console.log('Line '+index+' deactivated');
	   		}
	  	
	    },
	    error: function(){
	    	alert("Не могу включить "+branch_names[index]);
	    	console.error("Can't update "+branch_names[index]);
	    },
	    complete: function() {
	      update_branches_request();
	      $('#loader').hide();
	    }
	  });
}

function update_branches_request(){
	$.ajax({
	    url: aruino_ip, 
	    beforeSend: function(req){ $('#loader').show()},
	    success: function(data) {
			branches = data['variables'];

			$('#1').data('user-action', 0);
			$('#1').bootstrapToggle(get_state(branches['1']));	
			$('#1').data('user-action', 1);

			$('#2').data('user-action', 0);
			$('#2').bootstrapToggle(get_state(branches['2']));	
			$('#2').data('user-action', 1);

			$('#3').data('user-action', 0);
			$('#3').bootstrapToggle(get_state(branches['3']));	
			$('#3').data('user-action', 1);

			$('#4').data('user-action', 0);
			$('#4').bootstrapToggle(get_state(branches['4']));	
			$('#4').data('user-action', 1);

			$('#7').data('user-action', 0);
			$('#7').bootstrapToggle(get_state(branches['pump']));	
			$('#7').data('user-action', 1);

			function get_state(i){
				if (i==0)
				 return 'off';
				else
				  return 'on';
			}
	    },
	    error: function(){
	    	console.error("Branches statuses are out-of-date");
	    	$("#arduino_status").text("Branches statuses are out-of-date");
	    },
	    complete: function() {
	      $('#loader').hide();
	    }
	  });
}

function update_branches(json){
	branches = json['variables'];

	$('#1').data('user-action', 0);
	$('#1').bootstrapToggle(get_state(branches['1']));	
	$('#1').data('user-action', 1);

	$('#2').data('user-action', 0);
	$('#2').bootstrapToggle(get_state(branches['2']));	
	$('#2').data('user-action', 1);

	$('#3').data('user-action', 0);
	$('#3').bootstrapToggle(get_state(branches['3']));	
	$('#3').data('user-action', 1);

	$('#4').data('user-action', 0);
	$('#4').bootstrapToggle(get_state(branches['4']));	
	$('#4').data('user-action', 1);

	$('#7').data('user-action', 0);
	$('#7').bootstrapToggle(get_state(branches['pump']));	
	$('#7').data('user-action', 1);


	function get_state(i){
		if (i==0)
		 return 'off';
		else
		  return 'on';
	}
}
