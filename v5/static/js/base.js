var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');

var arduino_check_connect_sec = 60 * 5;
var arduino_check_broken_connect_sec = 60;

var branch = [];

$(document).ready(function() {
    $(".list-group-item").click(function() {
        // $(this).parent().children().removeClass("active");
        // $(this).addClass("active");
        $('.navbar-toggler').click();
    });

    $('#irrigate_tommorow').on('click', function() {
        $('#confirm_modal-body').html("Почати полив завтра?");
        $('#irrigate_modal').data('date', 1);
        $('#confirm_modal').modal('show');
    });

    $('#irrigate_today').on('click', function() {
        $('#confirm_modal-body').html("Почати полив сьогодні?");
        $('#irrigate_modal').data('date', 0);
        $('#confirm_modal').modal('show');
    });

    $(".irrigate-all").on('click', function() {
        data = $('#irrigate_modal').data('date');
        $.ajax({
            url: server + '/irrigate_all',
            type: "get",
            data: {
                'add_to_date': data
            },
            success: function(data) {
                $('#confirm_modal').modal('hide');
            },
            error: function(data) {
                $('#confirm_modal-body').html("Сталася помилка. Спробуйте ще раз");
            }
        });
    });

    //Add arduino touch script to determine if connection is alive
    (function update_weather() {
        $.ajax({
            url: server + '/weather',
            success: function(data) {
                $("#temp").text("Температура повітря: " + data['temperature'] + " C*");
                setTimeout(update_weather, 60 * 1000 * 30);
            }
        });
    })();


    // touch_analog_sensor();

    // Add arduino touch script to determine if connection is alive
    (function worker() {
        $.ajax({
            url: server + '/arduino_status',
            beforeSend: function(xhr, opts) {
                set_status_spinner();

                if ($('#irrigate_modal').hasClass('in')) {
                    xhr.abort();
                }
            },
            success: function(data) {
                console.log("connected to arduino");

                set_status_ok();

                update_branches(data);
                setTimeout(worker, arduino_check_connect_sec * 1000);
            },
            error: function() {
                console.error("Can't connect to arduino");

                set_status_error();
                setTimeout(worker, arduino_check_broken_connect_sec * 1000);
            }
        });
    })();
    // http://rosskevin.github.io/bootstrap-material-design/components/card/


    //comming from template
    var buttons = ["drawer-f-l", "drawer-f-r", "drawer-f-t", "drawer-f-b"]

    $.each(buttons, function(index, position) {
        $('#' + position).click(function() {
            setDrawerPosition('bmd-' + position)
        })
    })

    // add a toggle for drawer visibility that shows anytime
    $('#drawer-visibility').click(function() {
        var $container = $('.bmd-layout-container')

        // once clicked, just do away with responsive marker
        //$container.removeClass('bmd-drawer-in-md')

        var $btn = $(this)
        var $icon = $btn.find('.material-icons')
        if ($icon.text() == 'visibility') {
            $container.addClass('bmd-drawer-out') // demo only, regardless of the responsive class, we want to force it close
            $icon.text('visibility_off')
            $btn.attr('title', 'Drawer allow responsive opening')
        } else {
            $container.removeClass('bmd-drawer-out') // demo only, regardless of the responsive class, we want to force it open
            $icon.text('visibility')
            $btn.attr('title', 'Drawer force closed')
        }
    })

});


function touch_arduino() {
    $.ajax({
        url: server + '/arduino_status',
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
            console.error("Can't connect to arduino");
            set_status_error();
        }
    });
}

function touch_analog_sensor() {
    $.ajax({
        url: server + '/humidity_sensor',
        success: function(data) {
            $("#humidity_text").text(data['text']);
        }
    });
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
    $("#system_status").text(class_err.msg);
    $(".card").addClass(class_err.class);
    $(".btn-open-modal").addClass('disabled');
    $(".status-span").css('display', 'inline-block');
}

function set_status_ok() {
    $("#system_status").text(class_ok.msg);

    $(".card").removeClass(class_err.class);

    $(".btn-open-modal").removeClass('disabled');
    $(".status-span").hide();
    $(".btn-open-modal").show();

    $(".alert").alert('close')

}

function set_status_spinner() {
    $("#system_status").text(class_spin.msg);
    $(".btn-open-modal").addClass('disabled');
}



// Comming from template
function clearDrawerClasses($container) {
    var classes = ["bmd-drawer-f-l", "bmd-drawer-f-r", "bmd-drawer-f-t", "bmd-drawer-f-b"];

    $.each(classes, function(index, value) {
        $container.removeClass(value)
    })
}

function setDrawerPosition(position) {
    var $container = $('.bmd-layout-container')

    clearDrawerClasses($container)
    $container.addClass(position)
}