branch = []

$(document).ready(function() {

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
        schedule_select = $(this).find('#schedule_select');
        schedule_select.val(schedule_select.data('value'));

        irrigation_date = $(this).find('.irrigation_date');
        irrigation_date.val(convert_date(irrigation_date.data('value')));

        irrigation_time = $(this).find('.irrigation_time');
        irrigation_time.val(convert_date_to_time(irrigation_time.data('value')));

        irrigation_end_date = $(this).find('.irrigation_end_date');
        irrigation_end_date.val(convert_date(irrigation_end_date.data('value')));

        active_true_false = $(this).find('.active_true_false');
        active_true_false.prop("checked", active_true_false.data('value'));

        form_text($(this))
    });

    $('#irrigation_intervals').on('input', function(e) {
        toogle_time_wait($(this).val());
    });

    $('.form-text-control').on('input', function(e) {
        form_text($(this));
    });

    $('#branch_select').on('change', function(e) {
        index = parseInt($(this).val());
        set_branch_defaults(index);
        form_text($(this));
    });

    $(".btn-open-modal").click(function(e) {
        modal = $('#irrigate_modal')
        index = parseInt($(modal).find("#branch_select").val());
        set_branch_defaults(index);
        $(modal).find('.irrigation_date').val(convert_date_to_local_date(0));
        form_text($(modal));
        $(modal).modal('show');
    });

    $(".ongoing-rule-remove").click(function(e) {
        id = $(this).data('id');
        $.ajax({
            url: '/remove_ongoing_rule',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                $('#confirm_modal').modal('hide');
            },
            error: function(data) {
                alert("Сталася помилка. Cпробуйте ще раз");
            }
        });
    });


    $('.active_true_false').change(function(e) {        
        console.log($(e));
        console.log($(e.target));

        var old_value = !($(this).prop("checked"))
        console.log(old_value);
        var returnVal = confirm("Ви впевненні?");
        console.log(returnVal);
        if (returnVal == false) {
            $(this).prop("checked", old_value);
            $(this).val(this.old_value);
            return;
        }

        $(this).prop("checked", returnVal);
        $(this).val(this.checked);

        id = $(this).data('id')
        if (old_value == false) {
            $.ajax({
                url: '/activate_ongoing_rule',
                type: "get",
                data: {
                    'id': id
                },
                success: function(data) {
                    $('#confirm_modal').modal('hide');
                },
                error: function(data) {
                    alert("Сталася помилка. Cпробуйте ще раз");
                }
            });
        } else {
            $.ajax({
                url: '/deactivate_ongoing_rule',
                type: "get",
                data: {
                    'id': id
                },
                success: function(data) {
                    $('#dismiss_modal').modal('hide');
                },
                error: function(data) {
                    alert("Сталася помилка. Cпробуйте ще раз");
                }
            });
        }
    });


    $('.add-ongoing-rule').on('click', function(e) {
        json = { 'rule': {} }
        modal = $('#irrigate_modal');

        json['rule'] = {
            'line_id': $(modal).find('#branch_select').val(),
            'time': $(modal).find('#irrigation_minutes').val(),
            'intervals': $(modal).find('#irrigation_intervals').val(),
            'time_wait': $(modal).find('#irrigation_time_wait').val(),
            'repeat_value': $(modal).find('#schedule_select').val(),
            'date_start': $(modal).find('.irrigation_date').val(),
            'time_start': $(modal).find('.irrigation_time').val(),
            'end_date': $(modal).find('#end_date').val(),
        }

        if (json['rule']['end_date'] == '') {
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
            success: function() {
                console.log(json);
                $('#irrigate_modal').modal('hide');
            },
            error: function() {
                alert("Сталася помилка. Перевірте дані і спробуйте ще раз");
                console.log(json);
            }
        });
    });


    $('.collapse').on('hidden.bs.collapse', function(e) {
        var card = $(e.target).closest('.top')
        
        $(card).find('.if-collapsed').show();
        $(card).find('.if-not-collapsed').hide();
    })

    $('.collapse').on('show.bs.collapse', function(e) {
        var card = $(e.target).closest('.top')
        
        $(card).find('.if-collapsed').hide();
        $(card).find('.if-not-collapsed').show();
    })

});


function form_text(el_in) {
    var card = $(el_in).closest('.top')

    schedule_text = $(card).find('#schedule_select option:selected').attr('title');
    time = $(card).find('.irrigation_time').val();
    minutes = $(card).find('.irrigation_minutes').val();
    interval = $(card).find('.irrigation_intervals').val();

    var options = {
        weekday: "long",
        month: "short",
        day: "numeric"
    };

    now = new Date($(card).find("#end_date").val());
    text = 'до ' + now.toLocaleDateString("uk-UA", options) + ' включно.'

    $(card).find("#summary").innerHTML(
        schedule_text + ' о ' + time + ', ' + text + '.</br>' +
        intervals + ' рази, по ' + minutes + ' хвилин'
        );
}





function remove_rule(that) {
    id = $(that).data('id');
    $.ajax({
        url: '/remove_ongoing_rule',
        type: "get",
        data: {
            'id': id
        },
        success: function(data) {
            $("#rules_table").html(data);
        }
    });
}

function toogle_time_wait(val) {
    var input = parseInt(val)
    if (input <= 1 || isNaN(input)) {
        $('#irrigation_time_wait_group').hide();
    } else {
        $('#irrigation_time_wait_group').show();
    }
}

function set_branch_defaults(index) {
    name = branch[index]['name'];
    time = branch[index]['default_time'];
    interval = branch[index]['default_interval'];
    time_wait = branch[index]['default_time_wait'];
    default_time_start = branch[index]['start_time']


    $('#irrigation_minutes').val(time);
    $('#irrigation_intervals').val(interval);
    $('#irrigation_time_wait').val(time_wait);
    $('.irrigation_time').val(convert_date_to_time(default_time_start));

    toogle_time_wait(index);
}