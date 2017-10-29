var arduino_check_connect_sec = 60 * 5;
var arduino_check_broken_connect_sec = 60;

var branch = [];

$(document).ready(function() {
    // $("#my-drawer .list-group-item").click(function() {
    //     // $(this).parent().children().removeClass("active");
    //     // $(this).addClass("active");
    //     $('.navbar-toggler').click();
    // });

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
            url: '/irrigate_all',
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
            url: '/weather',
            success: function(data) {
                $("#temp").html("Температура повітря: " + data['temperature'] + " &#8451;");
                $("#hum").html("Вологість: " + data['humidity'] + " %");
                setTimeout(update_weather, 60 * 1000 * 30);
            }
        });
    })();


    // touch_analog_sensor();

    // Add arduino touch script to determine if connection is alive
    // (function worker() {
    //     $.ajax({
    //         url: '/irrigation_lighting_status',
    //         beforeSend: function(xhr, opts) {
    //             set_status_spinner();

    //             if ($('#irrigate_modal').hasClass('in')) {
    //                 xhr.abort();
    //             }
    //         },
    //         success: function(data) {
    //             console.log("connected to arduino");

    //             set_status_ok();
    //             setTimeout(worker, arduino_check_connect_sec * 1000);
    //         },
    //         error: function() {
    //             console.error("Can't connect to arduino");

    //             set_status_error();
    //             setTimeout(worker, arduino_check_broken_connect_sec * 1000);
    //         }
    //     });
    // })();
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
    $(".card-irrigation").addClass(class_err.class);
    $(".card-lighting").addClass(class_err.class);
    
    $(".btn-open-modal").addClass('disabled');
    $(".btn-start").addClass('disabled');

    $(".status-span").css('display', 'inline-block');
}

function set_status_ok() {
    $(".card-irrigation").removeClass(class_err.class);
    $(".card-lighting").removeClass(class_err.class);

    $(".btn-open-modal").removeClass('disabled');
    $(".btn-start").removeClass('disabled');
    $(".stop-lighting").removeClass('disabled');
    $(".stop-power_outlet").removeClass('disabled');
    $(".stop-irrigation").removeClass('disabled');

    $(".status-span").hide();
    $(".btn-open-modal").show();

    $(".alert").alert('close')

}

function set_status_spinner() {
    $(".btn-open-modal").addClass('disabled');
    $(".btn-start").addClass('disabled');
    
    $(".stop-lighting").addClass('disabled');
    $(".stop-power_outlet").addClass('disabled');
    $(".stop-irrigation").addClass('disabled');
    
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

function convert_date_to_time(date_str) {
    date = new Date(date_str);
    hours = ("0" + (date.getHours())).slice(-2);
    minutest = ("0" + (date.getMinutes())).slice(-2);
    return hours + ":" + minutest;
}

function convert_date(date_str) {
    date = new Date(date_str);
    var day = ("0" + date.getDate()).slice(-2);
    var month = ("0" + (date.getMonth() + 1)).slice(-2);

    var res = date.getFullYear() + "-" + (month) + "-" + (day);

    return res;
}

function convert_date_to_local_date(add_to_date) {
    now = new Date();
    now.setDate(now.getDate() + parseInt(add_to_date));

    var day = ("0" + now.getDate()).slice(-2);
    var month = ("0" + (now.getMonth() + 1)).slice(-2);

    var today = now.getFullYear() + "-" + (month) + "-" + (day);

    return today;
}

function get_parameter_by_name(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}