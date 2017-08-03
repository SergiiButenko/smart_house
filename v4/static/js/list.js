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

    socket.on('list_update', function(msg) {
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
                if (branch_names[i] == undefined){
                    continue;
                }
                $('#branch_number_selector').append("<option data-id="+i+" id=\"option"+i+"\">"+branch_names[i]+"</option>");
            }    
            $('#branch_number_selector').selectpicker('refresh');
      }
    });

    for (var i=1; i<=20; i++){
     $('#rule_timer_selector').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
     $('#time_wait_selector').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
    }
    $('#rule_timer_selector').selectpicker('refresh');
    $('#time_wait_selector').selectpicker('refresh');
    
    for (var i=1; i<=10; i++){
     $('#interval_selector').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
    }
    $('#interval_selector').selectpicker('refresh');
    
    $('#interval_selector').on('change', function(){
     var selected = $(this).find("option:selected").data("value");
     if (selected == 1) {
        $('#time_wait_selector').selectpicker('hide');
        $('#time_wait_selector_label').hide();
     } 

     if (selected > 1) {
        $('#time_wait_selector').selectpicker('show');
        $('#time_wait_selector_label').show();
     } 
    });


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

    //Function to start irrigation
    $(".deactivate_rules").click(function() {        
        id = $("#rule_selector option:selected").data("value");
        $.ajax({
            url: server+'/deactivate_all_rules',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                $("#rules_table").html(data);
            }
        });
    });


    $('#datetimepicker2').on("dp.show", function(e){
    	$('#datetimepicker2_input').prop("readonly", true);
    });

        $("#datetimepicker2").on("dp.hide", function(e) {
        					 $('#datetimepicker2_input').prop("readonly", false);
                             $('.bootstrap-datetimepicker-widget').hide();
                             $('#datetimepicker2_input').blur();
                             $.ajax({
                             url: server + '/get_timetable_list',
                             type: "get",
                             data: {
                                 'before': '0',
                                 'after': '12',
                             },
                             success: function(data) {
                                 $('#result_table').html(data);
                             }
                             });
                         });

    $('#btn_add_rule').on('click', function(e){
        branch_id = $("#branch_number_selector option:selected").data("id");
        time_min = $("#rule_timer_selector option:selected").data("value");
        datetime_start = $("#datetimepicker2_input").val();
        interval_quantity = $("#interval_selector option:selected").data("value");
        time_wait = $("#time_wait_selector option:selected").data("value");

        if (interval_quantity == 0){
        is_interval = false
        } else if (interval_quantity > 0){
            is_interval = true
        } else {
            is_interval = null
        }



        $.ajax({
            url: server+'/add_rule',
            type: "get",
            data: {
                'is_interval': is_interval, 
                'branch_id': branch_id,
                'time_min':time_min,
                'datetime_start':datetime_start,
                'quantity' : interval_quantity,
                'time_wait' : time_wait
            },
            success: function(data) {
                $("#result_table").html(data);
            }
        });
    });


     $('#add_rule').on('shown.bs.modal', function() {
     var selected = $("#interval_selector option:selected").data("value");
     if (selected == 0) {
        $('#time_wait_selector').selectpicker('hide');
        $('#time_wait_selector_label').hide();
     } 

     if (selected > 1) {
        $('#time_wait_selector').selectpicker('show');
        $('#time_wait_selector_label').show();
     } 
    })

    $('#add_rule').on('hidden.bs.modal', function() {
        $('#branch_number_selector').val(1);
        $('#branch_number_selector').selectpicker('refresh');

        $('#interval_selector').val(1);
        $('#interval_selector').selectpicker('refresh');

        $('#time_wait_selector').val(1);
        $('#time_wait_selector').selectpicker('refresh');

        $('#time_wait_selector').selectpicker('hide');
        $('#time_wait_selector_label').hide();
    })

});


    function activate_rule(that){
        id = $(that).data('id');
        $.ajax({
            url: server+'/activate_rule',
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
            url: server+'/deactivate_rule',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                $("#rules_table").html(data);
            }
        });
    }
