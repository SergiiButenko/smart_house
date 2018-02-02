var arduino_check_connect_sec = 60 * 5;
var arduino_check_broken_connect_sec = 60;

var branch = [];

$(document).ready(function() {
    $(".add_rule").on('click', function() {
        $.ajax({
            url: '/branch_settings',
            success: function(data) {
                list = data['list']
                $("#branch_select_plann_modal").find('option').remove();

                for (j in list) {
                    item = list[j]
                    branch[item['id']] = {
                        'name': item['name'],
                        'default_time': parseInt(item['default_time']),
                        'default_interval': parseInt(item['default_interval']),
                        'default_time_wait': parseInt(item['default_time_wait']),
                        'start_time': new Date(item['start_time'])
                    }

                    $("#branch_select_plann_modal").append(
                        "<option value=" + item['id'] + ">" + item['name'] + "</option>"
                    );
                }

                var modal = $('#plann_modal');
                var date = convert_date(new Date());
                $(modal).find($('.irrigation_date_plann_modal')).val(date);
                var index = parseInt($("#branch_select_plann_modal option:selected").val());
                set_branch_defaults(index, modal);

                $('#plann_modal').modal("show");
            }
        });
    });

    $('#branch_select_plann_modal').off().on('change', function(e) {
        modal = $('#plann_modal');
        var index = parseInt($(this).val());
        set_branch_defaults(index, modal);
    });

    $('#irrigation_intervals_plann_modal').on('input', function(e) {
        modal = $('#plann_modal');
        var input = parseInt($(this).val());
        if (input <= 1 || isNaN(input)) {
            $(modal).find('#irrigation_time_wait_group').hide();
        } else {
            $(modal).find('#irrigation_time_wait_group').css('display', 'inline-block');
        }
    });

    $(".plan").click(function() {
        var json = { 'rules': [] }
        var modal = $(this).closest("#plann_modal")
        
        var branch_id = $(modal).find('#branch_select_plann_modal option:selected').val();
        var name = $(modal).find('#branch_select_plann_modal option:selected').text();
        var time = $(modal).find('#irrigation_minutes_plann_modal').val();
        var interval = $(modal).find('#irrigation_intervals_plann_modal').val();
        var time_wait = $(modal).find('#irrigation_time_wait_plann_modal').val();
        var date_start = $(modal).find('.irrigation_date_plann_modal').val();
        var time_start = $(modal).find('.irrigation_time_plann_modal').val();
        json['rules'].push({
                "line_id": branch_id,
                'line_name': name,
                "time": time,
                "intervals": interval,
                "time_wait": time_wait,
                "date_start": date_start,
                'time_start': time_start,
                'end_date': date_start,
                'repeat_value': 4
            });

        $.ajax({
            url: '/add_ongoing_rule',
            type: "post",
            data: JSON.stringify(json),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            beforeSend: function(xhr, opts) {
                set_status_spinner();
            },
            success: function() {
                set_status_ok();
                $('#plann_modal').modal('hide');
            },
            error: function() {
                alert("error");
                set_status_ok();
            }
        });
    });

    //Add arduino touch script to determine if connection is alive
    (function update_weather() {
        $.ajax({
            url: '/weather',
            success: function(data) {
                $("#temp").text(data['temperature']);
                $("#hum").text(data['humidity']);
                $("#rain").text(data['rain']);
                if (data['rain_status'] == 1) {
                    $("#irrigation_status").text("Автоматичний полив дозволений");
                } else {
                    $("#irrigation_status").text("Автоматичний полив заборонений");
                }


                setTimeout(update_weather, 60 * 1000 * 30);
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

    // $(".btn-open-modal").addClass('disabled');
    // $(".btn-start").addClass('disabled');
    $(".btn").addClass('disabled');
    $(".status-span").css('display', 'inline-block');
}

function set_status_ok() {
    $(".btn").removeClass('disabled');
    // $(".card-irrigation").removeClass(class_err.class);
    // $(".card-lighting").removeClass(class_err.class);

    // $(".btn-open-modal").removeClass('disabled');
    // $(".btn-start").removeClass('disabled');
    // $(".stop-lighting").removeClass('disabled');
    // $(".stop-power_outlet").removeClass('disabled');
    // $(".stop-irrigation").removeClass('disabled');
    // $(".cancel-irrigation").removeClass('disabled');

    $(".status-span").hide();
    // $(".btn-open-modal").show();
    // $(".btn-modal").removeClass('disabled');
}

function set_status_spinner() {
    $(".btn").addClass('disabled');
    // $(".btn-open-modal").addClass('disabled');
    // $(".btn-start").addClass('disabled');
    // $(".cancel-irrigation").addClass('disabled');
    

    // $(".stop-lighting").addClass('disabled');
    // $(".stop-power_outlet").addClass('disabled');
    // $(".stop-irrigation").addClass('disabled');
    // $(".btn-modal").addClass('disabled');
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

function convert_date_to_time(date) {
    if (date instanceof Date == false) {
        date = new Date(date);
    }

    // var date = convertDateToUTC(date);

    var hours = ("0" + (date.getHours())).slice(-2);
    var minutest = ("0" + (date.getMinutes())).slice(-2);
    return hours + ":" + minutest;
}


function convert_date_to_time_utc(date) {
    if (date instanceof Date == false) {
        date = new Date(date);
    }

    var date = convertDateToUTC(date);

    var hours = ("0" + (date.getHours())).slice(-2);
    var minutest = ("0" + (date.getMinutes())).slice(-2);
    return hours + ":" + minutest;
}

function convert_date(date) {
    if (date instanceof Date == false) {
        date = new Date(date);
    }
    // var date = convertDateToUTC(date);

    var day = ("0" + date.getDate()).slice(-2);
    var month = ("0" + (date.getMonth() + 1)).slice(-2);

    var res = date.getFullYear() + "-" + (month) + "-" + (day);

    return res;
}

function convert_date_to_local_date(add_to_date) {
    var now = new Date();
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

function daydiff(first, second) {
    date1 = new Date(first.getFullYear(), first.getMonth(), first.getDate());
    date2 = new Date(second.getFullYear(), second.getMonth(), second.getDate());
    return Math.ceil((date2 - date1) / (1000 * 60 * 60 * 24));
}

function convertDateToUTC(date) {
    return new Date(
        date.getUTCFullYear(),
        date.getUTCMonth(),
        date.getUTCDate(),
        date.getUTCHours(),
        date.getUTCMinutes(),
        date.getUTCSeconds());
}

function toogle_time_wait(val, modal) {
    var input = parseInt(val)

    if (modal == undefined) {
        if (input <= 1 || isNaN(input)) {
            $('#irrigation_time_wait_group').hide();
        } else {
            $('#irrigation_time_wait_group').show();
        }
    } else {
        if (input <= 1 || isNaN(input)) {
            $(modal).find('#irrigation_time_wait_group').hide();
        } else {
            $(modal).find('#irrigation_time_wait_group').show();
        }
    }
}

function set_branch_defaults(index, modal) {
    var name = branch[index]['name'];
    var time = branch[index]['default_time'];
    var interval = branch[index]['default_interval'];
    var time_wait = branch[index]['default_time_wait'];
    var default_time_start = branch[index]['start_time']

    if (modal != undefined) {
        $(modal).find('#irrigation_minutes_plann_modal').val(time);
        $(modal).find('#irrigation_intervals_plann_modal').val(interval);
        $(modal).find('#irrigation_time_wait_plann_modal').val(time_wait);
        $(modal).find('.irrigation_time_plann_modal').val(convert_date_to_time(default_time_start));
    } else {
        $('#irrigation_minutes').val(time);
        $('#irrigation_intervals').val(interval);
        $('#irrigation_time_wait').val(time_wait);
        $('.irrigation_time').val(convert_date_to_time(default_time_start));
    }

    toogle_time_wait(interval, modal);
}

function reload_history() {
    console.log(window.location.href.includes('history'));

    if (window.location.href.includes('history')) {
        location.reload();
    }
}