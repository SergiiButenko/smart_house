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



    $('.add-ongoing-rule').on('click', function(e) {
        json = { 'rule': {} }
        modal = $('#irrigate_modal');

        json['rule'] = {
            'line_id': $(modal).find('#branch_select').val(),
            'time': $(modal).find('#irrigation_minutes').val(),
            'intervals': $(modal).find('#irrigation_intervals').val(),
            'time_wait': $(modal).find('#irrigation_time_wait').val(),
            'repeat_value': $(modal).find('#schedule_select').val(),
            'dow': '',
            'date_start': $(modal).find('.irrigation_date').val(),
            'time_start': $(modal).find('.irrigation_time').val(),
            'end_value': $(modal).find('.form-group input:checked').val(),
            'end_date': $(modal).find('#date').val(),
            'end_repeat_quantity': $(modal).find('#quantity').val()
        }

        $("#checkboxes input:checked").each(function() {
            json['rule']['dow'] = json['rule']['dow'] + $(this).val() + ';'
        });

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
                alert("error");
                console.log(json);
            }
        });


    });


    $('#irrigation_intervals').on('input', function(e) {
        toogle_time_wait($(this).val());
    });

    $('#date').on('input', function(e) {
        form_text($(this));
    });

    $('#quantity').on('input', function(e) {
        form_text($(this));
    });

    $('.irrigation_date').on('input', function(e) {
        form_text($(this));
    });

    $('.irrigation_time').on('input', function(e) {
        form_text($(this));
    });

    $('#branch_select').on('change', function(e) {
        index = parseInt($(this).val());
        set_branch(index);
        form_text($(this));
    });

    $('#schedule_select').on('change', function(e) {
        toogle_week_schedule($(this));
    });

    $(".btn-open-modal2").click(function() {
        modal = $('#irrigate_modal')
        index = parseInt($(modal).find("#branch_select").val());
        set_branch(index);
        $(modal).find('.irrigation_date').val(convert_date_to_local_date(0));
        form_text($(modal));
        $(modal).modal('show');
    });


    $("input[name='optionsRadios']").change(function() {
        radio = $(".form-group input:checked")
        if (radio.val() == 3) {
            $("#date").val(convert_date_to_local_date(1));
        } else {
            $("#date").val('');
        }

        if (radio.val() == 2) {
            $("#quantity").val(1);
        } else {
            $("#quantity").val('');
        }

        form_text($(this));
    });
    
    $("#checkboxes :checkbox").click(function() {
        form_text($(this));
    });

    $(".radio_input").focus(function() {
        $(this).closest('.radio').find(":radio").click();
        form_text($(this));
    });

});


function activate_rule(that) {
    id = $(that).data('id');
    $.ajax({
        url: '/activate_ongoing_rule',
        type: "get",
        data: {
            'id': id
        },
        success: function(data) {
            $("#rules_table").html(data);
        }
    });
}

function deactivate_rule(that) {
    id = $(that).data('id');
    $.ajax({
        url: '/deactivate_ongoing_rule',
        type: "get",
        data: {
            'id': id
        },
        success: function(data) {
            $("#rules_table").html(data);
        }
    });
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

function form_text(el_in) {   
    el = $(el_in).closest('.top')

    schedule_text = $(el).find('#schedule_select option:selected').attr('title');
    schedule_val = $(el).find('#schedule_select option:selected').val();
    weekdays = []

    if (schedule_val == 8) {
        $(el).find("#checkboxes input:checked").each(function() {
            weekdays.push($(this).attr('title'));
        });

        schedule_text = schedule_text + ": " + weekdays.join(',')
    }

    time = $(el).find('.irrigation_time').val();

    var options = {
        weekday: "long",
        month: "short",
        day: "numeric"
        // timeZone: 'UTC'
    };

    radio = $(el).find(".form-group input:checked")
    radio_text = ''
    date_new = $(el).find('.irrigation_date').val();
    if (radio.val() == 1) {
        now = new Date(date_new);
        now.setMonth(now.getMonth() + 1);
        radio_text = 'до ' + now.toLocaleDateString("uk-UA", options) + ' включно.'
    }


    if (radio.val() == 2) {
        val = $("#quantity").val();
        radio_text = "кількість повторів: " + val;
    }

    if (radio.val() == 3) {
        now = new Date($("#date").val());
        radio_text = 'до ' + now.toLocaleDateString("uk-UA", options) + ' включно.'
    }

    $(el).find("#summary").text(schedule_text + ' о ' + time + ', ' + radio_text);
}

function toogle_week_schedule(el_in) {
    val = $(el_in).val()
    el = $(el_in).closest('.top')

    if (val != 8 || isNaN(val)) {
        $(el).find('#week_schedule').hide();
    } else {
        $(el).find('#week_schedule').show();
    }

    form_text(el);
}

function toogle_time_wait(val) {
    var input = parseInt(val)
    if (input <= 1 || isNaN(input)) {
        $('#irrigation_time_wait_group').hide();
    } else {
        $('#irrigation_time_wait_group').show();
    }
}

function set_branch(index) {
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
