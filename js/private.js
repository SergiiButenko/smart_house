$(document).ready(function(){
   //Assign onChange for all switchers, so they open modal window
   $(".switchers").change(function(){ // Click to only happen on announce links
   	index = $(this).data('id')
   	console.log("index="+index);
   	name = get_branch_name(index);
   	console.log("branch name="+name);
   	// $("#modal_title").text(name);
    $('#time_modal').modal('show');
   });

});


//Vocabulary for all branches
function get_branch_name(index){
	var names=[
	'Сад, левая ветка',
	'Сад, правая ветка'
	];

	return names[index];
}