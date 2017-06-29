var server = 'http://butenko.asuscomm.com:7543'; 
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
                $('#branch_number_selector').append("<option data-id="+i+" id=\"option"+i+"\">"+branch_names[i]+"</option>");
            }    
            $('#branch_number_selector').selectpicker('refresh');
      }
    });

    for (var i=1; i<=20; i++){
     $('#rule_timer_selector').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
    }
    $('#rule_timer_selector').selectpicker('refresh');

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
                             url: server + '/get_list',
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
        $.ajax({
            url: server+'/add_rule',
            type: "get",
            data: {
                'branch_id': branch_id,
                'time_min':time_min,
                'datetime_start':datetime_start
            },
            success: function(data) {
                $("#result_table").html(data);
            }
        });
    });
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