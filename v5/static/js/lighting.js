var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');

var arduino_check_connect_sec = 60 * 5;
var arduino_check_broken_connect_sec = 60;

var branch = [];

$(document).ready(function() {

    //Rename branches
    $.ajax({
        url: server + '/lighting_names',
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
            url: server + '/arduino_status',
            beforeSend: function(xhr, opts) {
                set_status_spinner();

                if ($('#lighting_modal').hasClass('in')) {
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

    var socket = io.connect(server, {
        'sync disconnect on unload': true
    });
    socket.on('connect', function() {
        console.log("connected to websocket");
    });

    socket.on('lighting_status', function(msg) {
        console.log('Message received. New brach status: ' + msg.data);
        update_branches(JSON.parse(msg.data));
    });


    // http://rosskevin.github.io/bootstrap-material-design/components/card/

    $('#irrigate_modal').on('hidden.bs.modal', function() {
        update_branches_request();
    })

    $(".btn-open-modal").click(function() {
        index = $(this).data('id');
        name = branch[index]['name'];
        time = branch[index]['default_time'];

        $('#lighting_minutes').val(time);
        $('#irrigate_modal').data('id', index);

        $('.modal-title').html(name);
        $('#irrigate_modal').modal('show');
    });

    //Function to start lighting
    $(".start-lighting").click(function() {
        index = $('#irrigate_modal').data('id');
        time = parseInt($("#lighting_minutes").val());
        if (time == 0 || isNaN(time)) {
            $('#lighting_minutes_group').addClass("has-danger");
        } else {
            $('#lighting_minutes_group').removeClass("has-danger");
        }


        if ($('#lighting_minutes_group').hasClass("has-danger")) {
            console.log("Fill in form correctly");
        } else {
            console.log(branch[index]['name'] + " will be activated on " + time + " minutes ");
            branch_on(index, time);
            $('#irrigate_modal').modal('hide');
        }
    });

    $(".btn-start").click(function() {
        index = $(this).data('id');
        console.log(branch[index]['name'] + " will be activated on " + branch[index]['default_time'] + " minutes ");
        branch_off(index, branch[index]['default_time']);
    });

    //Function to stop lighting
    $(".stop-lighting").click(function() {
        index = $(this).data('id');
        console.log(branch[index]['name'] + " will be deactivated now");
        branch_off(index);
    });


});

function branch_on(index, time_minutes) {
    $.ajax({
        url: server + '/lighting_on',
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
        url: server + '/lighting_off',
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