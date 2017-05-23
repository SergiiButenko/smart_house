var server = 'http://185.20.216.94:7542';

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

    $.ajax({
        url: server + "/weather",
        success: function(data) {
            $("#temp_header").text("Температура воздуха - " + data['temperature'] + " C*");
        }
    });

    //Add arduino touch script to determine if connection is alive
    (function worker() {
        $.ajax({
            url: server+'/arduino_status',
            beforeSend: function(xhr, opts) {
                $("#arduino_status").text(" Проверка статуса системы");
                $("#button_gif").addClass("fa-spin");

                if ($('#time_modal').hasClass('in')) {
                    xhr.abort();
                }
            },
            success: function(data) {
                $('#loader').hide();
                console.log("connected to arduino");
                $("#arduino_status").text(" Система активна");
                update_branches(data);
                setTimeout(worker, arduino_check_connect_sec * 1000);
            },
            error: function() {
                console.error("Can't connect to arduino");
                $("#arduino_status").text(" Ошбика в системе");
                $('#loader').show()
                setTimeout(worker, arduino_check_broken_connect_sec * 1000);
            },
            complete: function(){$("#button_gif").removeClass("fa-spin");}
        });
    })();

    //Print list of rules
    (function update_rules() {
        $.ajax({
            url: server,
            success: function(data) {
                $("#rules_list").text("Список правил: "+data);
                setTimeout(update_rules, 5 * 1000);
                }
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
        type: "put",
        data: {
            'id': index,
            'time' : time_min
        },
        success: function(data) {
        		data = JSON.parse(data);

            if (data['return_value'] == 0) {
                alert("Не могу включить " + branch_names[index]);
                console.error('Line ' + index + ' cannot be activated');
            }

            if (data['return_value'] == 1) {
                console.log('Line ' + index + ' activated');
            }
        },
        error: function() {
            alert("Не могу включить " + branch_names[index]);
            console.error("Can't update " + branch_names[index]);
        },
        complete: function() {
            update_branches_request();
        }
    });
}

function branch_off(index) {
    $.ajax({
        url: server + '/off',
        type: "get",
        data: {
            'id': index
        },
        success: function(data) {
        	  data = JSON.parse(data);

            if (data['return_value'] == 1) {
                alert("Не могу включить " + branch_names[index]);
                console.error('Line ' + index + ' cannot be deactivated');
            }

            if (data['return_value'] == 0) {
                console.log('Line ' + index + ' deactivated');
            }

        },
        error: function() {
            alert("Не могу включить " + branch_names[index]);
            console.error("Can't update " + branch_names[index]);
        },
        complete: function() {
            update_branches_request();
        }
    });
}

function update_branches_request() {
    $.ajax({
        url: server+'/arduino_status',
        success: function(data) {
        	  data = JSON.parse(data);

            branches = data['variables'];
            console.log(data['variables']);
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

            $('#7').data('user-action', 0);
            $('#7').bootstrapToggle(get_state(branches['pump']));
            $('#7').data('user-action', 1);

            function get_state(i) {
                if (i == 0)
                    return 'off';
                else
                    return 'on';
            }
        },
        error: function() {
            console.error("Branches statuses are out-of-date");
            $("#arduino_status").text("Branches statuses are out-of-date");
        }
    });
}

function update_branches(json) {
	json = JSON.parse(json);
    branches = json['variables'];	  
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

    $('#7').data('user-action', 0);
    $('#7').bootstrapToggle(get_state(branches['pump']));
    $('#7').data('user-action', 1);


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
                $("#arduino_status").text(" Проверка статуса системы");
                $("#button_gif").addClass("fa-spin");
            },
            success: function(data) {
                console.log("connected to arduino");
                $("#arduino_status").text(" Система активна");
                update_branches(data);
            },
            error: function() {
                console.error("Can't connect to arduino");
                $("#arduino_status").text(" Ошибка в системе");
            },
            complete: function(){$("#button_gif").removeClass("fa-spin");}
        });
}