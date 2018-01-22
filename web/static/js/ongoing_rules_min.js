var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
branch = []

$(document).ready(function() {

    var socket = io.connect(server, {
        'sync disconnect on unload': true
    });
    socket.on('connect', function() {
        console.log("connected to websocket");
    });

    socket.on('edit_ongoing_rule', function(msg) {
        console.log('Message received. edit_ongoing_rule. New rule\'s seting: ' + msg.data);
        var msg = JSON.parse(msg.data);
        var rule = msg['rule'];
        $('.top').each(function() {
            if ($(this).data('id') == rule['rule_id']) {
                $(this).find('#irrigation_minutes').val(rule['time']);
                $(this).find('#irrigation_intervals').val(rule['intervals']);
                $(this).find('#irrigation_time_wait').val(rule['time_wait']);
                $(this).find('#schedule_select').val(rule['repeat_value']);
                $(this).find('.irrigation_date').val(convert_date(rule['date_start']));
                $(this).find('.irrigation_time').val(convert_date_to_time_utc(rule['time_start']));
                $(this).find('#end_date').val(convert_date(rule['end_date']));

                form_text($(this).find('#end_date'));
            }
        });

    });

    socket.on('ongoing_rule_state', function(msg) {
        console.log('Message received. ongoing_rule_state. New rule\'s state: ' + msg.data);
        var msg = JSON.parse(msg.data)
        $('.top').each(function() {
            if ($(this).data('id') == msg['rule']['rule_id']) {
                switcher = $(this).find('.active_true_false');
                $(switcher).prop("checked", msg['rule']['status']);
            }
        });
    });

    socket.on('remove_ongoing_rule', function(msg) {
        console.log('Message received. remove_ongoing_rule. Rule to remove: ' + msg.data);
        var msg = JSON.parse(msg.data)
        $('.top').each(function() {
            if ($(this).data('id') == msg['rule']['rule_id']) {
                $(this).remove();
            }
        });
        toogle_no_card();
    });

    socket.on('add_ongoing_rule', function(msg) {
        console.log('Message received. add_ongoing_rule. New rule: ' + msg.data);
        var msg = JSON.parse(msg.data);
        $(msg['rule']['template']).insertBefore('#last_card');
        $('.top').each(function() {
            if ($(this).data('id') == msg['rule']['rule_id']) {

                schedule_select = $(this).find('#schedule_select');
                $(schedule_select).val($(schedule_select).data('value'));

                irrigation_date = $(this).find('.irrigation_date');
                $(irrigation_date).val(convert_date($(irrigation_date).data('value')));

                irrigation_time = $(this).find('.irrigation_time');
                $(irrigation_time).val(convert_date_to_time($(irrigation_time).data('value')));

                irrigation_end_date = $(this).find('.irrigation_end_date');
                $(irrigation_end_date).val(convert_date($(irrigation_end_date).data('value')));

                active_true_false = $(this).find('.active_true_false');
                $(active_true_false).prop("checked", $(active_true_false).data('value'));

                $(this).find('#irrigation_minutes').addClass('disabled');
                $(this).find('#irrigation_intervals').addClass('disabled');
                $(this).find('#irrigation_time_wait').addClass('disabled');
                $(this).find('#schedule_select').addClass('disabled');
                $(this).find('.irrigation_date').addClass('disabled');
                $(this).find('.irrigation_time').addClass('disabled');
                $(this).find('#end_date').addClass('disabled');

                form_text($(this).find('.active_true_false'));
                set_events();
            }
        });
        toogle_no_card();
    });

    //Rename branches
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

                $("#branch_select").append(
                    "<option value=" + item['id'] + ">" + item['name'] + "</option>"
                );
            }
        }
    });

    $(".card-rule").each(function() {
        var schedule_select = $(this).find('#schedule_select');
        schedule_select.val(schedule_select.data('value'));

        var irrigation_date = $(this).find('.irrigation_date');
        irrigation_date.val(convert_date(irrigation_date.data('value')));

        var irrigation_time = $(this).find('.irrigation_time');
        irrigation_time.val(convert_date_to_time(irrigation_time.data('value')));

        var irrigation_end_date = $(this).find('.irrigation_end_date');
        irrigation_end_date.val(convert_date(irrigation_end_date.data('value')));

        var active_true_false = $(this).find('.active_true_false');
        active_true_false.prop("checked", active_true_false.data('value'));

        form_text($(this))
    });
    set_events();
    toogle_no_card();
});

function toogle_no_card() {
    if ($(".card-rule").length > 0) {
        console.log('hide')
        $('#no_card').hide();
    } else {
        console.log('show')
        $('#no_card').show();
    }
}


function form_text(el_in) {
    var card = $(el_in).closest('.top')

    var schedule_text = $(card).find('#schedule_select option:selected').attr('title');
    var schedule_val = $(card).find('#schedule_select option:selected').val();
    var time = $(card).find('.irrigation_time').val();
    var minutes = $(card).find('#irrigation_minutes').val();
    var interval = $(card).find('#irrigation_intervals').val();
    var time_wait = $(card).find('#irrigation_time_wait').val();

    var options_date = {
        weekday: "long",
        month: "short",
        day: "numeric"
    };

    var date = convertDateToUTC(new Date($(card).find("#end_date").val()));
    var now = new Date();
    var text = "";
    if (daydiff(now, date) == 0) {
        text = "сьогодні,";
    } else if (daydiff(now, date) == 1) {
        text = "завтра,";
    } else if (daydiff(now, date) == 2) {
        text = "післязавтра,";
    } else {
        text = date.toLocaleDateString("uk-UA", options_date);
    }

    if (schedule_val == 4) {
        $(card).find("#summary").html(
            schedule_text + ', ' + text + ' o ' + time + '.</br>' +
            interval + ' рази, по ' + minutes + ' хвилин, з інтервалом в ' + time_wait + ' хвилин'
        );
    } else {
        $(card).find("#summary").html(
            schedule_text + ' о ' + time + ', ' + 'до ' + text + ' включно.' + '</br>' +
            interval + ' рази, по ' + minutes + ' хвилин, з інтервалом в ' + time_wait + ' хвилин'
        );
    }



}

function set_events() {
    $('#irrigation_intervals').off().on('input', function(e) {
        toogle_time_wait($(this).val());
    });

    $('.form-text-control').off().on('input', function(e) {
        form_text($(this));
    });

    $('.schedule_select').off().on('change', function(e) {
        if ($(this).val() == 4) {
            var tbody = $(this).closest('.tbody')
            tbody.find('#end_date').val(tbody.find('#start_date').val())
        }
        form_text($(this));
    });


    $('#branch_select').off().on('change', function(e) {
        var index = parseInt($(this).val());
        set_branch_defaults(index);
        form_text($(this));
    });

    $(".btn-open-modal").click(function(e) {
        var modal = $('#irrigate_modal')
        var index = parseInt($(modal).find("#branch_select").val());
        set_branch_defaults(index);
        $(modal).find('.irrigation_date').val(convert_date_to_local_date(0));
        form_text($(modal));
        $(modal).modal('show');
    });

    $(".ongoing-rule-remove").off().click(function(e) {
        var returnVal = confirm("Видалити правило?");
        if (returnVal == false)
            return;

        var id = $(this).data('id');
        $.ajax({
            url: '/remove_ongoing_rule',
            type: "get",
            data: {
                'id': id
            },
            beforeSend: function(xhr, opts) {
                set_status_spinner();
            },
            error: function(data) {
                alert("Сталася помилка. Cпробуйте ще раз");
            },
            complete: function(data) {
                set_status_ok();
            }
        });
    });


    $('.active_true_false').off().change(function(e) {
        var switcher = $(e.target);

        var old_value = !($(switcher).prop("checked"));
        console.log(old_value);
        var returnVal = confirm("Ви впевненні?");
        console.log(returnVal);
        if (returnVal == false) {
            $(switcher).prop("checked", old_value);
            // $(switcher).val($(switcher).old_value);
            return;
        }

        var id = $(switcher).data('id')
        if (old_value == false) {
            $.ajax({
                url: '/activate_ongoing_rule',
                type: "get",
                data: {
                    'id': id
                },
                beforeSend: function(xhr, opts) {
                    set_status_spinner();
                },
                error: function(data) {
                    alert("Сталася помилка. Cпробуйте ще раз");
                },
                complete: function(data) {
                    set_status_ok();
                }
            });
        } else {
            $.ajax({
                url: '/deactivate_ongoing_rule',
                type: "get",
                data: {
                    'id': id
                },
                beforeSend: function(xhr, opts) {
                    set_status_spinner();
                },
                error: function(data) {
                    alert("Сталася помилка. Cпробуйте ще раз");
                },
                complete: function(data) {
                    set_status_ok();
                }
            });
        }
    });


    $('.add-ongoing-rule').off().on('click', function(e) {
        var json = { 'rules': [] }
        var modal = $('#irrigate_modal');

        json['rules'].push({
            'line_id': $(modal).find('#branch_select').val(),
            'line_name': $(modal).find('#branch_select').find("option:selected").text(),
            'time': $(modal).find('#irrigation_minutes').val(),
            'intervals': $(modal).find('#irrigation_intervals').val(),
            'time_wait': $(modal).find('#irrigation_time_wait').val(),
            'repeat_value': $(modal).find('#schedule_select').val(),
            'date_start': $(modal).find('.irrigation_date').val(),
            'time_start': $(modal).find('.irrigation_time').val(),
            'end_date': $(modal).find('#end_date').val(),
        })

        if (json['rules'][0]['end_date'] == '') {
            alert("Сталася помилка. Перевірте дані і спробуйте ще раз");
            console.log(json);
            return;
        }

        $.ajax({
            url: '/add_ongoing_rule',
            type: "post",
            data: JSON.stringify(json),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            beforeSend: function(xhr, opts) {
                $('.add-flow').addClass('disabled');
                set_status_spinner();
            },
            success: function() {
                console.log(json);
                $('#irrigate_modal').modal('hide');
            },
            error: function() {
                alert("Сталася помилка. Перевірте дані і спробуйте ще раз");
                console.log(json);
            },
            complete: function() {
                $('.add-flow').removeClass('disabled');
                set_status_ok();
            }
        });
    });

    $('.ongoing-rule-save').off().on('click', function(e) {
        var json = { 'rules': [] }
        var card = $(e.target).closest('.top')

        json['rules'].push({
            'line_id': $(card).find('#line_id').data('id'),
            'time': $(card).find('#irrigation_minutes').val(),
            'intervals': $(card).find('#irrigation_intervals').val(),
            'time_wait': $(card).find('#irrigation_time_wait').val(),
            'repeat_value': $(card).find('#schedule_select').val(),
            'date_start': $(card).find('.irrigation_date').val(),
            'time_start': $(card).find('.irrigation_time').val(),
            'end_date': $(card).find('#end_date').val(),
            'rule_id': $(e.target).data('id')
        })

        if (json['rules'][0]['end_date'] == '') {
            alert("Сталася помилка. Перевірте дані і спробуйте ще раз");
            console.log(json);
            return;
        }

        $.ajax({
            url: '/edit_ongoing_rule',
            type: "put",
            data: JSON.stringify(json),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            beforeSend: function(xhr, opts) {
                $('.edit-flow').addClass('disabled');
                $('.show-flow').addClass('disabled');
                set_status_spinner();
            },
            success: function() {
                console.log(json);
                collapse = $(card).find('#' + $(e.target).data('id'));
                collapse.collapse('hide');
                $(card).find('.edit-flow').hide();
                $(card).find('.show-flow').show();
            },
            error: function() {
                alert("Сталася помилка. Перевірте дані і спробуйте ще раз");
                console.log(json);
            },
            complete: function() {
                $('.edit-flow').removeClass('disabled');
                $('.show-flow').removeClass('disabled');
                set_status_ok();
            }
        });
    });


    $('.collapse').off().on('hidden.bs.collapse', function(e) {
        var card = $(e.target).closest('.top')

        $(card).find('.if-collapsed').show();
        $(card).find('.if-not-collapsed').hide();
    })

    $('.collapse').on('show.bs.collapse', function(e) {
        var card = $(e.target).closest('.top')

        $(card).find('.if-collapsed').hide();
        $(card).find('.if-not-collapsed').show();
    })

    var rule = {}
    $(".ongoing-rule-edit").off().click(function(e) {
        var card = $(e.target).closest('.top')
        var collapse = $(card).find('#' + $(e.target).data('id'))

        rule = {}
        rule['start_values'] = {
            'time': $(card).find('#irrigation_minutes').val(),
            'intervals': $(card).find('#irrigation_intervals').val(),
            'time_wait': $(card).find('#irrigation_time_wait').val(),
            'repeat_value': $(card).find('#schedule_select').val(),
            'date_start': $(card).find('.irrigation_date').val(),
            'time_start': $(card).find('.irrigation_time').val(),
            'end_date': $(card).find('#end_date').val(),
        }

        $(card).find('#irrigation_minutes').removeClass('disabled');
        $(card).find('#irrigation_intervals').removeClass('disabled');
        $(card).find('#irrigation_time_wait').removeClass('disabled');
        $(card).find('#schedule_select').removeClass('disabled');
        $(card).find('.irrigation_date').removeClass('disabled');
        $(card).find('.irrigation_time').removeClass('disabled');
        $(card).find('#end_date').removeClass('disabled');

        collapse.collapse('show');
        $(card).find('.edit-flow').show();
        $(card).find('.show-flow').hide();
    });

    $(".ongoing-rule-cancel").off().click(function(e) {
        var card = $(e.target).closest('.top')
        var collapse = $(card).find('#' + $(e.target).data('id'))

        collapse.collapse('hide');
        $(card).find('.edit-flow').hide();
        $(card).find('.show-flow').show();

        $(card).find('#irrigation_minutes').addClass('disabled');
        $(card).find('#irrigation_intervals').addClass('disabled');
        $(card).find('#irrigation_time_wait').addClass('disabled');
        $(card).find('#schedule_select').addClass('disabled');
        $(card).find('.irrigation_date').addClass('disabled');
        $(card).find('.irrigation_time').addClass('disabled');
        $(card).find('#end_date').addClass('disabled');

        $(card).find('#irrigation_minutes').val(rule['start_values']['time']);
        $(card).find('#irrigation_intervals').val(rule['start_values']['intervals'])
        $(card).find('#irrigation_time_wait').val(rule['start_values']['time_wait'])
        $(card).find('#schedule_select').val(rule['start_values']['repeat_value'])
        $(card).find('.irrigation_date').val(rule['start_values']['date_start'])
        $(card).find('.irrigation_time').val(rule['start_values']['time_start'])
        $(card).find('#end_date').val(rule['start_values']['end_date'])
        form_text($(card).find('#end_date'))
    });
}