var branch_names = [];

$(document).ready(function() {

    //Rename branches
    $.ajax({
        url: server + '/branches_names',
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



    $('#irrigation_intervals').on('input', function(e) {
        toogle_time_wait($(this).val());
    });

    $('#date').on('input', function(e) {
        form_text();
    });

    $('#quantity').on('input', function(e) {
        form_text();
    });

    $('.irrigation_date').on('input', function(e) {
        form_text();
    });

    function set_branch(index) {
        name = branch[index]['name'];
        time = branch[index]['default_time'];
        interval = branch[index]['default_interval'];
        time_wait = branch[index]['default_time_wait'];


        $('#irrigation_minutes').val(time);
        $('#irrigation_intervals').val(interval);
        $('#irrigation_time_wait').val(time_wait);

        toogle_time_wait(index);
    }

    $('#branch_select').on('change', function(e) {
        index = parseInt($(this).val());
        set_branch(index);
    });

    $('#schedule_select').on('change', function(e) {
        toogle_week_schedule($(this).val());
    });

    function toogle_week_schedule(val) {
        val = parseInt(val);

        if (val != 8 || isNaN(val)) {
            $('#week_schedule').hide();
            form_text();
        } else {
            $('#week_schedule').show();
        }
    }

    function toogle_time_wait(val) {
        var input = parseInt(val)
        if (input <= 1 || isNaN(input)) {
            $('#irrigation_time_wait_group').hide();
        } else {
            $('#irrigation_time_wait_group').show();
        }
    }

    $(".radio_input").focus(function() {
        $(this).closest('.radio').find(":radio").click();
        form_text();
    });


    $(".btn-open-modal2").click(function() {
        index = parseInt($("#branch_select").val());
        set_branch(index);
        $('.irrigation_date').val(convert_date_to_local_date(0));
        form_text();
        $('#irrigate_modal').modal('show');
    });


    $("input[name='optionsRadios']").change(form_text);
    $("#checkboxes :checkbox").click(form_text);

});


function activate_rule(that) {
    id = $(that).data('id');
    $.ajax({
        url: server + '/activate_ongoing_rule',
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
        url: server + '/deactivate_ongoing_rule',
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
        url: server + '/remove_ongoing_rule',
        type: "get",
        data: {
            'id': id
        },
        success: function(data) {
            $("#rules_table").html(data);
        }
    });
}

function form_text() {



    schedule_text = $('#schedule_select option:selected').attr('title');
    schedule_val = $('#schedule_select option:selected').val();
    weekdays = []

    if (schedule_val == 8) {
        $("#checkboxes input:checked").each(function() {
            weekdays.push($(this).attr('title'));
        });

        schedule_text = schedule_text + ": " + weekdays.join(',')
    }

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

    radio_text = ''


    var options = {
        weekday: "long",
        month: "short",
        day: "numeric",
        timeZone: 'UTC'
    };

    date_new = $('.irrigation_date').val();
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

    $("#summary").text(schedule_text + ', ' + radio_text);
}