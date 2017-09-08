var branch_names = [];

$(document).ready(function() {

    //Rename branches
    $.ajax({
      url: server+'/branches_names',
      success: function(data) {
         list=data['list']
            for (j in list) {
                item = list[j]
                branch_names[item['id']]=item['name']
            }

            for (var i = 1; i < branch_names.length; i++) {
                $('#branch_number_selector').append("<option data-id="+i+" id=\"option"+i+"\">"+branch_names[i]+"</option>");
                $('#branch_number_selector_edit').append("<option data-id="+i+" id=\"option"+i+"\">"+branch_names[i]+"</option>");
            }    
            $('#branch_number_selector').selectpicker('refresh');
            $('#branch_number_selector_edit').selectpicker('refresh');
      }
    });


    $(".btn-open-modal2").click(function() {
         $('#irrigate_modal').modal('show');
    });

});


    function activate_rule(that){
        id = $(that).data('id');
        $.ajax({
            url: server+'/activate_ongoing_rule',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                $("#rules_table").html(data);
            }
        });
    }

    function deactivate_rule(that){
        id = $(that).data('id');
        $.ajax({
            url: server+'/deactivate_ongoing_rule',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                $("#rules_table").html(data);
            }
        });
    }

    function remove_rule(that){
        id = $(that).data('id');
        $.ajax({
            url: server+'/remove_ongoing_rule',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                $("#rules_table").html(data);
            }
        });
    }
