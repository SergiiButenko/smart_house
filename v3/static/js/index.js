var server = 'http://185.20.216.94:7543';

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
                 $('#title-'+i).text(branch_names[i]);
                 console.log(branch_names[i])
                 console.log(branch_names[i]=='')
            }    
   
      }
    });
    

    for (var i=1; i<=20; i++){
     $('#time_selector').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
     $('#time_wait_selector').append("<option data-value="+i+" id=\"option"+i+"\">"+i+"</option>");
    }
    $('#time_selector').selectpicker('refresh');
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

    var socket = io.connect(server, {'sync disconnect on unload': true });
    socket.on('connect', function() {
        console.log("connected to websocket");
        console.log(socket.id);
    });

    socket.on('branch_status', function(msg) {
               console.log('Message received. New brach status: '  + msg.data);
               update_branches(msg.data);
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


    touch_analog_sensor();
    
    //Add arduino touch script to determine if connection is alive
    (function worker() {
        $.ajax({
            url: server+'/arduino_status',
            beforeSend: function(xhr, opts) {
                set_status_spinner();

                if ($('#time_modal').hasClass('in')) {
                    xhr.abort();
                }
            },
            success: function(data) {
                $('#loader').hide();
                console.log("connected to arduino");
                
                set_status_ok();

                update_branches(data);
                setTimeout(worker, arduino_check_connect_sec * 1000);
            },
            error: function() {
                console.error("Can't connect to arduino");

                set_status_error();

                $('#loader').show()
                setTimeout(worker, arduino_check_broken_connect_sec * 1000);
            },
            complete: function(){$("#button_gif").removeClass("fa-spin");}
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

    $('#time_modal').on('shown.bs.modal', function() {
     var selected = $("#interval_selector option:selected").data("value");
     if (selected  == 1) {
        $('#time_wait_selector').selectpicker('hide');
        $('#time_wait_selector_label').hide();
     } 

     if (selected > 1) {
        $('#time_wait_selector').selectpicker('show');
        $('#time_wait_selector_label').show();
     } 
    })

    $('#time_modal').on('hidden.bs.modal', function() {
        $('#time_selector').val(1);
        $('#time_selector').selectpicker('refresh');

        $('#interval_selector').val(1);
        $('#interval_selector').selectpicker('refresh');

        $('#time_wait_selector').val(1);
        $('#time_wait_selector').selectpicker('refresh');

        $('#time_wait_selector').selectpicker('hide');
        $('#time_wait_selector_label').hide();

        update_branches_request();
    })

    //Assign onClick for close buttons on Modal window
    // $(".modal_close").click(function() {
    //     update_branches_request();
    // });

    //Assign onChange for all switchers, so they open modal window
    $(".switchers-main, .switchers-pump").change(function() {
        if ($(this).data('user-action') == 1) {
            
            index = $(this).data('id');
            if ($(this).prop('checked')) {
                name = branch_names[index];

                $('#time_modal').data('id', index);
                $('.modal-title').html(name);
                $('#time_modal').modal('show');
            }

            if (!$(this).prop('checked')) {
               branch_off(index);
            }
        }
    });

    //Function to start irrigation
    $(".start-irrigation").click(function() {
        index = $('#time_modal').data('id');
        time = $("#time_selector option:selected").data("value");
        interval_quantity = $("#interval_selector option:selected").data("value");
        time_wait = $("#time_wait_selector option:selected").data("value");
        console.log(branch_names[index]+" will be activated on "+time+" minutes, "+interval_quantity+" times with "+time_wait+" period");
        branch_on(index, time, interval_quantity, time_wait);
    });

});

function branch_on(index, time_minutes, interval_quantity, time_wait) {
    if (interval_quantity == 0){
        is_interval = false
    } else if (interval_quantity > 0){
        is_interval = true
    } else {
        is_interval = null
    }
    
    $.ajax({
        url: server + '/activate_branch',
        type: "get",
        data: {            
            'is_interval': is_interval, 
            'id': index,
            'time_min' : time_minutes,
            'quantity' : interval_quantity,
            'time_wait' : time_wait
        },
        success: function(data) {
            console.log('Line ' + branch_names[index] + ' should be active now');
            update_branches(data);
        },
        error: function() {
            alert("Не могу включить " + branch_names[index]);
            console.error("Can't update " + branch_names[index]);
            toogle_checkbox(index, 0); 
            
            set_status_error();
        }
    });
}

function branch_off(index) {
    $.ajax({
        url: server + '/deactivate_branch',
        type: "get",
        data: {
            'id': index
        },
        success: function(data) {
            console.log('Line ' + branch_names[index] + ' should be deactivated now');
            update_branches(data);
        },
        error: function() {
            alert("Не могу выключить " + branch_names[index]);
            console.error("Can't update " + branch_names[index]);
            toogle_checkbox(index, 1); 
            set_status_error();
        }
    });
}

function update_branches_request() {
    $.ajax({
        url: server+'/arduino_status',
        success: function(data) {
            branches = JSON.parse(data);

            toogle_checkbox(16, branches['16']);    
            toogle_checkbox(15, branches['15']);     
            toogle_checkbox(14, branches['14']);     
            toogle_checkbox(13, branches['13']);     
            toogle_checkbox(12, branches['12']);
            toogle_checkbox(11, branches['11']);
            toogle_checkbox(10, branches['10']);
            toogle_checkbox(9, branches['9']);
            toogle_checkbox(8, branches['8']);
            toogle_checkbox(7, branches['7']);
            toogle_checkbox(6, branches['6']);
            toogle_checkbox(5, branches['5']);
            toogle_checkbox(4, branches['4']);
            toogle_checkbox(3, branches['3']);
            toogle_checkbox(2, branches['2']);
            toogle_checkbox(1, branches['1']);
            toogle_checkbox(17, branches['pump']);   
        },
        error: function() {
            console.error("Branches statuses are out-of-date");
            set_status_error();
        }
    });
}

function update_branches(json) {
    branches = JSON.parse(json);
    toogle_checkbox(16, branches['16']);    
    toogle_checkbox(15, branches['15']);     
    toogle_checkbox(14, branches['14']);     
    toogle_checkbox(13, branches['13']);     
    toogle_checkbox(12, branches['12']);
    toogle_checkbox(11, branches['11']);
    toogle_checkbox(10, branches['10']);
    toogle_checkbox(9, branches['9']);
    toogle_checkbox(8, branches['8']);
    toogle_checkbox(7, branches['7']);
    toogle_checkbox(6, branches['6']);
    toogle_checkbox(5, branches['5']);
    toogle_checkbox(4, branches['4']);
    toogle_checkbox(3, branches['3']);
    toogle_checkbox(2, branches['2']);
    toogle_checkbox(1, branches['1']);   
    toogle_checkbox(17, branches['pump']);     
}

function toogle_checkbox(element_id, branch_state){
    $('#'+element_id).data('user-action', 0);
    $('#'+element_id).bootstrapToggle(get_state(branch_state));
    $('#'+element_id).data('user-action', 1);

    function get_state(i) {
        if (i == 0)
            return 'off';
        else
            return 'on';
    }   
}

function touch_arduino(){
    $.ajax({
            url: server+'/arduino_status',
            beforeSend: function(xhr, opts) {
                $("#arduino_status").text(class_spin.msg);
                $("#button_gif").removeClass().addClass(class_spin.class);
            },
            success: function(data) {
                console.log("connected to arduino");
                set_status_ok();
                update_branches(data);
            },
            error: function() {
                //$('button').setClass('btn btn-primary');
                console.error("Can't connect to arduino");
                set_status_error();
            }
        });
}

function touch_analog_sensor(){
    $.ajax({
            url: server+'/humidity_sensor',
            success: function(data) {
                $("#humidity_text").text(data['text']);
            }
        });
}

// this is for status button
var class_ok = {msg:' Система активна', class: 'fa fa-refresh'}
var class_spin = {msg:' Проверка статуса системы...', class: 'fa fa-refresh fa-spin'}
var class_err = {msg:' Ошибка! Нажмите, чтобы обновить статус', class: 'fa fa-exclamation-circle'}

function set_status_error(){
    // $('#1').bootstrapToggle('disable')
    // $('#2').bootstrapToggle('disable')
    // $('#3').bootstrapToggle('disable')
    // $('#4').bootstrapToggle('disable')
    // $('#7').bootstrapToggle('disable')
    // $('#toggle-demo').bootstrapToggle('disable')
    // $('#toggle-demo').bootstrapToggle('disable')
    // $('#toggle-demo').bootstrapToggle('disable')
    $("#arduino_status").text(class_err.msg);
    $("#button_gif").removeClass().addClass(class_err.class);
    $("#status_button").removeClass().addClass('btn btn-danger btn-md');
}

function set_status_ok(){
    $("#arduino_status").text(class_ok.msg);
    $("#button_gif").removeClass().addClass(class_ok.class);
    $("#status_button").removeClass().addClass('btn btn-default btn-md');

}

function set_status_spinner(){
    $("#arduino_status").text(class_spin.msg);
    $("#button_gif").removeClass().addClass(class_spin.class);
    $("#status_button").removeClass().addClass('btn btn-default btn-md');
}
