var arduino_check_connect_sec = 60 * 5;
var arduino_check_broken_connect_sec = 60;

var branch = [];

$(document).ready(function() {

    //Rename branches
    $.ajax({
        url: '/power_outlets_settings',
        success: function(data) {
            list = data['list']
            for (j in list) {
                item = list[j]
                branch[item['id']] = {
                    'name': item['name'],
                    'default_time': parseInt(item['default_time'])
                }
            }
        }
    });


    (function worker2() {
        $.ajax({
            url: '/arduino_small_house_status',
            beforeSend: function(xhr, opts) {
                if ($('#power_outle_modal').hasClass('in')) {
                    xhr.abort();
                }
            },
            success: function(data) {
                console.log("connected to raspberry");

                update_branches(data);

                set_status_ok();
                setTimeout(worker2, arduino_check_connect_sec * 1000);
            },
            error: function() {
                console.error("Can't connect to raspberry");

                set_status_error();
                setTimeout(worker2, arduino_check_broken_connect_sec * 1000);
            }
        });
    })();

    var socket = io.connect(server, {
        'sync disconnect on unload': true
    });
    socket.on('connect', function() {
        console.log("connected to websocket");
    });

    socket.on('power_outlet_status', function(msg) {
        console.log('Message received. New brach status: ' + msg.data);
        update_branches(JSON.parse(msg.data));
    });


    // http://rosskevin.github.io/bootstrap-material-design/components/card/

    $('#power_outlet_modal').on('hidden.bs.modal', function() {
        update_branches_request();
    })

    $(".btn-open-modal").click(function() {
        index = $(this).data('id');
        name = branch[index]['name'];
        time = branch[index]['default_time'];

        $('#power_outlet_minutes').val(time);
        $('#power_outlet_modal').data('id', index);

        $('.modal-title').html(name);
        $('#power_outlet_modal').modal('show');
    });

    //Function to start lighting
    $(".start-power_outlet").click(function() {
        index = $('#power_outlet_modal').data('id');
        time = parseInt($("#power_outlet_minutes").val());
        if (time == 0 || isNaN(time)) {
            $('#power_outlet_minutes_group').addClass("has-danger");
        } else {
            $('#power_outlet_minutes_group').removeClass("has-danger");
        }


        if ($('#power_outlet_minutes_group').hasClass("has-danger")) {
            console.log("Fill in form correctly");
        } else {
            console.log(branch[index]['name'] + " will be activated on " + time + " minutes ");
            branch_on(index, time);
            $('#power_outlet_modal').modal('hide');
        }
    });

    $(".btn-start").click(function() {
        index = $(this).data('id');
        console.log(branch[index]['name'] + " will be activated on " + branch[index]['default_time'] + " minutes ");
        branch_on(index, branch[index]['default_time']);
    });

    //Function to stop lighting
    $(".stop-power_outlet").click(function() {
        index = $(this).data('id');
        console.log(branch[index]['name'] + " will be deactivated now");
        branch_off(index);
    });


});

function branch_on(index, time_minutes) {
    $.ajax({
        url: '/activate_branch',
        type: "get",
        data: {
            'id': index,
            'time_min': time_minutes
        },
        success: function(data) {
            console.log('Line ' + branch[index]['name'] + ' should be actived now');
            update_branches(data);
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
            'id': index
        },
        success: function(data) {
            console.log('Line ' + branch[index]['name'] + ' should be deactivated now');
            update_branches(data);
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
        url: server + '/arduino_small_house_status',
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
        $('#btn-start-with-options-' + element_id).hide().addClass("hidden");
        $('#btn-stop-' + element_id).css('display', 'inline-block').removeClass("hidden");
    } else {
        $('#card-' + element_id).removeClass("card-irrigate-active");
        $('#btn-stop-' + element_id).hide().addClass("hidden");
        $('#btn-start-' + element_id).css('display', 'inline-block').removeClass("hidden");
        $('#btn-start-with-options-' + element_id).css('display', 'inline-block').removeClass("hidden");
    }
}

// this is for status button
var class_ok = {
    msg: ' Система активна',
    class: 'fa fa-refresh'
}
var class_spin = {
    msg: ' Перевірка статусу системи...',
    class: 'fa fa-refresh fa-spin'
}
var class_err = {
    msg: ' В системі помилка',
    class: 'status-error'
}

function set_status_error() {
    $(".card-power").addClass(class_err.class);

    $(".btn-open-modal").addClass('disabled');
    $(".btn-start").addClass('disabled');
    $(".stop-power_outlet").addClass('disabled');

    $(".status-span").css('display', 'inline-block');
}

function set_status_ok() {
    $(".card-power").removeClass(class_err.class);

    $(".btn-open-modal").removeClass('disabled');
    $(".btn-start").removeClass('disabled');
    $(".stop-power_outlet").removeClass('disabled');

    $(".status-span").hide();
    $(".btn-open-modal").show();
}
