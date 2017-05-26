var server = 'http://mozart.hopto.org:7542';
//var server = 'http://127.0.0.1:5000';

var arduino_check_connect_sec = 60*5;
var arduino_check_broken_connect_sec = 60;

var branch_names = ['', // Arduino stars numeration from 1. So skiping 0 index
    'Первая ветка',
    'Вторая ветка',
    'Третья ветка',
    'Четвертая ветка',
    '',
    '',
    'Насос'
];

$(document).ready(function() {
    //Rename branches
    for (var i = 1; i < branch_names.length; i++) {
        $('#title-' + i + " span").text(branch_names[i]);
    }

    var $loading = $('#loader').hide();
    $(document)
        .ajaxStart(function() {
            $loading.show();
        })
        .ajaxStop(function() {
            $loading.hide();
    });
    
    var socket = io.connect(server);
    socket.heartbeatTimeout = 5000;
    socket.on('connect', function() {
        console.log("connected to websocket")
    });

    socket.on('branch_status', function(msg) {
               console.log('Message received. New brach status: '  + msg.data);
               update_branches(msg.data);
            });

    //Add arduino touch script to determine if connection is alive
    (function worker2() {
        $.ajax({
            url: server+'/weather',
            success: function(data) {
                $("#temp_header").text("Температура воздуха: " + data['temperature'] + " C*");
                setTimeout(worker2, 60 * 1000 * 30);
            }
        });
    })();

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


    //Assign onClick for close buttons on Modal window
    $(".modal_close").click(function() {
        update_branches_request();
    });

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
        time = $("#time_buttons input:radio:checked").data("value");
        console.log(branch_names[index]+" will be activated on "+time+" minutes");
        branch_on(index, time);
    });

});

function branch_on(index, time_min) {
    $.ajax({
        url: server + '/activate_branch',
        type: "get",
        data: {
            'id': index,
            'time' : time_min
        },
        success: function(data) {
            console.log('Line ' + branch_names[index] + ' should be activated now');
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
        	data = JSON.parse(data);
            branches = data['variables'];

            toogle_checkbox(1, branches['1']);    
            toogle_checkbox(2, branches['2']);     
            toogle_checkbox(3, branches['3']);     
            toogle_checkbox(4, branches['4']);     
            toogle_checkbox(7, branches['pump']);   
        },
        error: function() {
            console.error("Branches statuses are out-of-date");
            
            set_status_error();
        }
    });
}

function update_branches(json) {
	json = JSON.parse(json);
    branches = json['variables'];
    toogle_checkbox(1, branches['1']);	  
    toogle_checkbox(2, branches['2']);     
    toogle_checkbox(3, branches['3']);     
    toogle_checkbox(4, branches['4']);     
    toogle_checkbox(7, branches['pump']);     
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

// this is for status button
var class_ok = {msg:' Система активна.', class: 'fa fa-refresh'}
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