var server = 'http://185.20.216.94:7543'; 
//var server = 'http://127.0.0.1:7543';

var arduino_check_connect_sec = 60*5;
var arduino_check_broken_connect_sec = 60;

var branch_names = [];

$(document).ready(function() {
    var $loading = $('#loader').hide();
    $(document)
        .ajaxStart(function() {
            $loading.show();
        })
        .ajaxStop(function() {
            $loading.hide();
    });
    
    var socket = io.connect(server, {'sync disconnect on unload': true });
    socket.on('connect', function() {
        console.log("connected to websocket");
        console.log(socket.id);
    });

    socket.on('ongoind_rules_update', function(msg) {
            $("#rules_table").html(msg.data);
    });  

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

    for (var i=1; i<=20; i++){
     $('#rule_timer_selector').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
     $('#rule_timer_selector_edit').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
    }
    $('#rule_timer_selector').selectpicker('refresh');
    $('#rule_timer_selector_edit').selectpicker('refresh');

    //Add arduino touch script to determine if connection is alive
    (function update_weather() {
        $.ajax({
            url: server+'/weather',
            success: function(data) {
                $("#temp_header").text("Температура воздуха: " + data['temperature'] + " C*");
                setTimeout(update_weather, 60 * 1000 * 30);
            },
            global:false
        });
    })();

    $('#btn_add_ongoing_rule').on('click', function(e){
        branch_id = $("#branch_number_selector option:selected").data("id");
        time_min = $("#rule_timer_selector option:selected").data("value");
        datetime_start = $("#datetimepicker2_input").val();
        dow = $("#dow_selector option:selected").data("value");

        $.ajax({
            url: server+'/add_ongoing_rule',
            type: "get",
            data: {
                'branch_id': branch_id,
                'time_min':time_min,
                'datetime_start':datetime_start,
                'dow':dow
            },
            complete: function(data) {
                //$('#add_rules').modal('hide');
            }
        });
    });

    $(".btn_edit").on('click', function(e){
        id=$(this).data('id')

        branch_id = $('#brname_for_'+id).text();
        dow = $('#dow_for_'+id).text();
        time_start = $('#time_for_'+id).text();
        minutes = $('#minutes_for_'+id).text().split(" ")[0];
        
        $("#branch_number_selector_edit option").filter(function(){
            return $.trim($(this).text()) ==  branch_id
        }).prop('selected', true);
        $('#branch_number_selector_edit').selectpicker('refresh')

        $("#dow_selector_edit option").filter(function(){
            return $.trim($(this).text()) ==  dow
        }).prop('selected', true);
        $('#dow_selector_edit').selectpicker('refresh')

        $("#rule_timer_selector_edit option").filter(function(){
            return $.trim($(this).text()) ==  minutes
        }).prop('selected', true);
        $('#rule_timer_selector_edit').selectpicker('refresh')
        
        time_start = time_start.split(':');
        date_set = new Date().setHours(time_start[0],time_start[1],time_start[2])
        
        // $.ajax({
        //     url: server+'/add_ongoing_rule',
        //     type: "get",
        //     data: {
        //         'branch_id': branch_id,
        //         'time_min':time_min,
        //         'datetime_start':datetime_start,
        //         'dow':dow
        //     },
        //     complete: function(data) {
        //         //$('#add_rules').modal('hide');
        //     }
        // });
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
