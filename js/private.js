$(document).ready(function(){

   //Assign onClick for close buttons on Modal window
   $(".modal_close").click(function(){ 
   	id=$('#time_modal').data('id');
   	$('#'+id).bootstrapToggle('off')
    $('#time_modal').modal('toggle');
   });


	$('.switchers').bootstrapToggle({
		 on: 'Остановить Полив',
		 off: 'Начать полив'
	});

   //Assign onChange for all switchers, so they open modal window
   $(".switchers").change(function(){ 
   	if ($(this).prop('checked')){
	   	index = $(this).data('id')
	   	name = get_branch_name(index);
	   	
	   	$('#time_modal').data('id',index);
	   	$('.modal-title').html(name);

	    $('#time_modal').modal('show');
	}
   });

});


//Vocabulary for all branches
function get_branch_name(index){
	var names=[ '', // Arduino stars numeration from 1. So skiping 0 index
	'Сад, левая ветка',
	'Сад, правая ветка'
	];

	return names[index];
}