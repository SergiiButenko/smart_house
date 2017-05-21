var aruino_ip='http://192.168.1.10';
var arduino_timeout_sec=3;

var branch_names=[ '', // Arduino stars numeration from 1. So skiping 0 index
	'Первая ветка',
	'Вторая ветка',
	'Третья ветка',
	'Четвертая ветка',
	'Пятая ветка',
	'',
	'Насос'
	];

$(document).ready(function(){
	for (var i = 1; i < branch_names.length; i++) {
	   $('#title-'+i+" span").text(branch_names[i]);
	}

   //Assign onClick for close buttons on Modal window
   $(".modal_close").click(function(){ 
   	id=$('#time_modal').data('id');
   	$('#'+id).bootstrapToggle('off');
    $('#time_modal').modal('hide');
   });

   // Add labels for swticher values
	$('.switchers').bootstrapToggle({
		 on: 'Остановить Полив',
		 off: 'Начать полив'
	});

   //Assign onChange for all switchers, so they open modal window
   $(".switchers").change(function(){ 
   	if ($(this).prop('checked') && $(this).data('user-action') == 1){
	   	index = $(this).data('id');
	   	name = branch_names[index];
	   	
	   	$('#time_modal').data('id',index);
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
	
	update_branches_request();
	// (function worker() {
	//   $.ajax({
	//     url: aruino_ip, 
	//     success: function(data) {
	//       update_branches(JSON.stringify(data));
	//       $("#for_test").html("DEMON updates each 3sec: "+JSON.stringify(data));
	//     },
	//     complete: function() {
	//       // Schedule the next request when the current one's complete
	//       setTimeout(worker, arduino_timeout_sec*1000);
	//     }
	//   });
	// })();
});


function branch_on(index){
	$.ajax({
	    url: aruino_ip+'/on', 
	    type: "get",
	    data: {
	    	'params' : index
	    },
	    success: function(data) {
	      console.log('Line '+index+' activated');
	    },
	    complete: function() {
	      update_branches_request();
	      console.log('done');
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
	    success: function(data) {
	      console.log('Line '+index+' deactivated');
	    },
	    complete: function() {
	      update_branches_request();
	      console.log('done');
	    }
	  });
}

function update_branches_request(){
	$.ajax({
	    url: aruino_ip, 
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

			$('#5').data('user-action', 0);
			$('#5').bootstrapToggle(get_state(branches['5']));	
			$('#5').data('user-action', 1);

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
	  });
}

function update_branches(json){
	json = JSON.parse(json);
	branches = json['variables'];
	console.log();

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

	$('#5').data('user-action', 0);
	$('#5').bootstrapToggle(get_state(branches['5']));	
	$('#5').data('user-action', 1);

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
