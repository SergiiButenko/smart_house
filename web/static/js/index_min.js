var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');

var arduino_check_connect_sec = 60 * 5;
var arduino_check_broken_connect_sec = 60;

var branch = [];

$(document).ready(function() {

    var socket = io.connect(server, {
        'sync disconnect on unload': true
    });
    socket.on('connect', function() {
        console.log("connected to websocket");
    });

    socket.on('branch_status', function(msg) {
        console.log('Message received. New brach status: ' + msg.data);
        update_branches(JSON.parse(msg.data));
    });


    $.ajax({
        url: '/branch_settings',
        success: function(data) {
            list = data['list']
            for (j in list) {
                item = list[j]
                branch[item['id']] = {
                    'name': item['name'],
                    'default_time': parseInt(item['default_time']),
                    'default_interval': parseInt(item['default_interval']),
                    'default_time_wait': parseInt(item['default_time_wait']),
                    'start_time': new Date(item['start_time'])
                }
            }
        }
    });


    (function worker2() {
        $.ajax({
            url: '/irrigation_lighting_status',
            beforeSend: function(xhr, opts) {
                set_status_spinner();

                if ($('#irrigate_modal').hasClass('in')) {
                    xhr.abort();
                }
            },
            success: function(data) {
                console.log("connected to arduino");

                update_branches(data);

                set_status_ok();
                setTimeout(worker2, arduino_check_connect_sec * 1000);
            },
            error: function() {
                console.error("Can't connect to arduino");

                set_status_error();
                setTimeout(worker2, arduino_check_broken_connect_sec * 1000);
            }
        });
    })();

    $('#irrigation_intervals').on('input', function(e) {
        var input = parseInt($(this).val());
        if (input <= 1 || isNaN(input)) {
            $('#irrigation_time_wait_group').hide();
        } else {
            $('#irrigation_time_wait_group').css('display', 'inline-block');
        }
    });

    // http://rosskevin.github.io/bootstrap-material-design/components/card/

    $(".btn-open-modal").click(function() {
        index = $(this).data('id');
        name = branch[index]['name'];
        time = branch[index]['default_time'];
        interval = branch[index]['default_interval'];
        time_wait = branch[index]['default_time_wait'];

        $('#irrigation_minutes').val(time);
        $('#irrigation_intervals').val(interval);
        $('#irrigation_time_wait').val(time_wait);
        $('#irrigate_modal').data('id', index);

        if (interval <= 1) {
            $('#irrigation_time_wait_group').hide();
        } else {
            $('#irrigation_time_wait_group').css('display', 'inline-block');
        }

        $('.modal-title').html(name);
        $('#irrigate_modal').modal('show');
    });

    //Function to start irrigation
    $(".start-irrigation").click(function() {
        index = $('#irrigate_modal').data('id');
        time = parseInt($("#irrigation_minutes").val());
        if (time == 0 || isNaN(time)) {
            $('#irrigation_minutes_group').addClass("has-danger");
        } else {
            $('#irrigation_minutes_group').removeClass("has-danger");
        }

        interval_quantity = parseInt($("#irrigation_intervals").val());
        if (interval_quantity == 0 || isNaN(interval_quantity)) {
            $('#irrigation_intervals_group').addClass("has-danger");
        } else {
            $('#irrigation_intervals_group').removeClass("has-danger");
        }

        time_wait = parseInt($("#irrigation_time_wait").val());
        if (time_wait == 0 || isNaN(time_wait)) {
            $('#irrigation_time_wait_group').addClass("has-danger");
        } else {
            $('#irrigation_time_wait_group').removeClass("has-danger");
        }

        if ($('#irrigation_minutes_group').hasClass("has-danger") ||
            $('#irrigation_intervals_group').hasClass("has-danger") ||
            $('#irrigation_time_wait_group').hasClass("has-danger")) {
            console.log("Fill in form correctly");
        } else {
            console.log(branch[index]['name'] + " will be activated on " + time + " minutes, " + interval_quantity + " times with " + time_wait + " period");
            branch_on(index, time, interval_quantity, time_wait);
            $('#irrigate_modal').modal('hide');
        }
    });

    //Function to stop irrigation
    $(".stop-irrigation").click(function() {
        index = $(this).data('id');
        console.log(branch[index]['name'] + " will be deactivated now");
        branch_off(index);
    });

    //Function to stop irrigation
    $(".cancel-irrigation").click(function() {
        var interval_id = $(this).data('id');
        console.log(interval_id + " irrigation schedule will be canceled");

        $.ajax({
            url: server + '/cancel_rule',
            type: "post",
            data: JSON.stringify( { 'list': [interval_id] } ),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            beforeSend: function(xhr, opts) {
                set_status_spinner();
            },
            success: function(data) {                                
                set_status_ok();
            },
            error: function() {
                set_status_ok();
            }
        });
    });

});

function branch_on(index, time_minutes, interval_quantity, time_wait) {
    if (interval_quantity == 1) {
        mode = 'single'
    } else {
        mode = 'interval'
    }

    $.ajax({
        url: '/activate_branch',
        type: "get",
        data: {
            'mode': mode,
            'id': index,
            'time_min': time_minutes,
            'quantity': interval_quantity,
            'time_wait': time_wait
        },
        beforeSend: function(xhr, opts) {
            set_status_spinner();
        },
        success: function(data) {
            console.log('Line ' + branch[index]['name'] + ' should be active now');
            update_branches(data);
            set_status_ok();
        },
        error: function() {
            console.error("Can't update " + branch[index]['name']);
            toogle_card(index, 0);

            set_status_error();
        }
    });
}

function branch_off(index) {
    $.ajax({
        url: '/deactivate_branch',
        type: "get",
        data: {
            'id': index,
            'mode': 'manually'
        },
        beforeSend: function(xhr, opts) {
            set_status_spinner();
        },
        success: function(data) {
            console.log('Line ' + branch[index]['name'] + ' should be deactivated now');
            update_branches(data);
            set_status_ok();
        },
        error: function() {
            console.error("Can't update " + branch[index]['name']);
            toogle_card(index, 1);
            set_status_error();
        }
    });
}

function update_branches_request() {
    $.ajax({
        url: '/irrigation_lighting_status',
        success: function(data) {
            update_branches(data);
        },
        error: function() {
            console.error("Branches statuses are out-of-date");
            set_status_error();
        }
    });
}

function update_branches(json) {
    arr = json['branches']

    for (var i = 0; i <= arr.length; i++) {
        toogle_card(i, arr[i]);
    }
}

function toogle_card(element_id, branch) {
    if (branch == null)
        return;

    branch_state = branch['status']
    if (branch_state == 1) {
        $('#card-' + element_id).addClass("card-irrigate-active");
        $('#btn-start-' + element_id).hide().addClass("hidden");
        $('#btn-stop-' + element_id).css('display', 'inline-block').removeClass("hidden");
    } else {
        $('#card-' + element_id).removeClass("card-irrigate-active");
        $('#btn-stop-' + element_id).hide().addClass("hidden");
        $('#btn-start-' + element_id).css('display', 'inline-block').removeClass("hidden");
    }

    var options_datetime = {
        weekday: "long",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    };

    var options_time = {
        hour: "2-digit",
        minute: "2-digit"
    };

    var now = new Date();
    if (branch['last_rule']) {
        last_rule = convertDateToUTC(new Date(branch['last_rule']['timer']))
        if (daydiff(now, last_rule) == 0) {
            last_rule = "сьогодні, о " + last_rule.toLocaleTimeString("uk-UA", options_time);
        } else if (daydiff(now, last_rule) == -1) {
            last_rule = "вчора, о " + last_rule.toLocaleTimeString("uk-UA", options_time);
        } else {
            last_rule = last_rule.toLocaleTimeString("uk-UA", options_datetime);
        }
    } else {
        last_rule = "немає запису"
    }
    $('#last-' + element_id).text("Останній полив: " + last_rule)

    if (branch['next_rule'] && branch['next_rule']['rule_id'] == 1) {
        next_rule =  convertDateToUTC(new Date(branch['next_rule']['timer']))
        if (daydiff(now, next_rule) == 0) {
            next_rule = "сьогодні, о " + next_rule.toLocaleTimeString("uk-UA", options_time);
        } else if (daydiff(now, next_rule) == 1) {
            next_rule = "завтра, о " + next_rule.toLocaleTimeString("uk-UA", options_time);
        } else if (daydiff(now, next_rule) == 2) {
            next_rule = "післязавтра, о " + next_rule.toLocaleTimeString("uk-UA", options_time);
        } else {
            next_rule = next_rule.toLocaleTimeString("uk-UA", options_datetime);
        }

        $('#next-' + element_id).css('display', 'inline-block').removeClass("hidden");
        $('#next-' + element_id).html("</br>Наступний полив: " + next_rule);

        $('#btn-cancel-' + element_id).data('id', branch['next_rule']['interval_id'])
        $('#btn-cancel-' + element_id).css('display', 'inline-block').removeClass("hidden");
    } else if (branch['next_rule'] && branch['next_rule']['rule_id'] == 2) {
        next_rule =  convertDateToUTC(new Date(branch['next_rule']['timer']))
        if (daydiff(now, next_rule) == 0) {
            next_rule = "сьогодні, о " + next_rule.toLocaleTimeString("uk-UA", options_time);
        } else if (daydiff(now, next_rule) == 1) {
            next_rule = "завтра, о " + next_rule.toLocaleTimeString("uk-UA", options_time);
        } else if (daydiff(now, next_rule) == 2) {
            next_rule = "післязавтра, о " + next_rule.toLocaleTimeString("uk-UA", options_time);
        } else {
            next_rule = next_rule.toLocaleTimeString("uk-UA", options_datetime);
        }

        $('#next-' + element_id).css('display', 'inline-block').removeClass("hidden");
        $('#next-' + element_id).html("</br>Полив зупиниться: " + next_rule);
        $('#btn-cancel-' + element_id).hide().addClass("hidden");
    } else {
        $('#next-' + element_id).html("</br>Наступний полив: немає запису");
        $('#next-' + element_id).hide().addClass("hidden");
        $('#btn-cancel-' + element_id).hide().addClass("hidden");
    }
}