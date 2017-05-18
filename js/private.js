var branch_names=[ '', // Arduino stars numeration from 1. So skiping 0 index
	'Первая ветка',
	'Вторая ветка',
	'Третья ветка',
	'Четвертая ветка',
	'Пятая ветка'
	];

$(document).ready(function(){
	for (var i = 1; i < branch_names.length; i++) {
	   $('#title-'+i+" span").text(branch_names[i]);
	}

   //Assign onClick for close buttons on Modal window
   $(".modal_close").click(function(){ 
   	id=$('#time_modal').data('id');
   	$('#'+id).bootstrapToggle('off')
    $('#time_modal').modal('hide');
   });

   // Add labels for swticher values
	$('.switchers').bootstrapToggle({
		 on: 'Остановить Полив',
		 off: 'Начать полив'
	});

   //Assign onChange for all switchers, so they open modal window
   $(".switchers").change(function(){ 
   	if ($(this).prop('checked')){
	   	index = $(this).data('id')
	   	name = branch_names[index];
	   	
	   	$('#time_modal').data('id',index);
	   	$('.modal-title').html(name);

	    $('#time_modal').modal('show');
	}
   });

	(function worker() {
	  $.ajax({
	    url: 'http://93.126.68.60:6542', 
	    success: function(data) {
	      $("#for_test").html(data);
	      alert(data);
	    },
	    complete: function() {
	      alert("data2");
	      $("#for_test").html("data");
	      // Schedule the next request when the current one's complete
	      setTimeout(worker, 3*1000);
	    }
	  });
	})();


});