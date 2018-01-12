var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
var branch = [];

$(document).ready(function() {
    $(".card").each(function() {
        group = $(this).find('#irrigation_time_wait_group')
        interval = $(this).find('.irrigation_intervals').val();
        if (interval <= 1 || isNaN(interval)) {
            group.hide();
        } else {
            group.show();
        }
    });

    $('.irrigation_intervals').on('input', function(e) {
        var input = parseInt($(this).val());
        card = $(this).closest(".card")
        group = card.find('#irrigation_time_wait_group')
        if (input <= 1 || isNaN(input)) {
            group.hide();
        } else {
            group.show();
        }
    });

    $(".remove_card").click(function() {
        $(this).closest(".card").parent().remove();
    });

    $("#go_plan").click(function() {
        json = { 'list': {} }

        $(".card").each(function() {
            branch_id = $(this).data('branch_id');
            time = $(this).find('.irrigation_minutes').val();
            interval = $(this).find('.irrigation_intervals').val();
            time_wait = $(this).find('.irrigation_time_wait').val();
            date_start = $(this).find('.irrigation_date').val();
            time_start = $(this).find('.irrigation_time').val();
            json.list[branch_id] = {
                "branch_id": branch_id,
                "time": time,
                "interval": interval,
                "time_wait": time_wait,
                "datetime_start": date_start + " " + time_start
            }
        });

        $.ajax({
            url: '/add_rule',
            type: "post",
            data: JSON.stringify(json),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            beforeSend: function(xhr, opts) {
                $('#go_plan').addClass("disabled");
            },
            success: function() {
                $('#go_plan').removeClass("disabled");
                window.location.replace("/#");
            },
            error: function() {
                alert("error");
                $('#go_plan').removeClass("disabled");
            }
        });
    });
});