var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
var branch = [];

$(document).ready(function() {
    $(".card").each(function() {
        var group = $(this).find('#irrigation_time_wait_group')
        var interval = $(this).find('.irrigation_intervals').val();
        if (interval <= 1 || isNaN(interval)) {
            group.hide();
        } else {
            group.show();
        }
    });

    $('.irrigation_intervals').on('input', function(e) {
        var input = parseInt($(this).val());
        var card = $(this).closest(".card")
        var group = card.find('#irrigation_time_wait_group')
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
        var json = { 'rules': {} }

        $(".card").each(function() {
            var branch_id = $(this).data('branch_id');
            var name = $(this).find('h4:first').text();
            var time = $(this).find('.irrigation_minutes').val();
            var interval = $(this).find('.irrigation_intervals').val();
            var time_wait = $(this).find('.irrigation_time_wait').val();
            var date_start = $(this).find('.irrigation_date').val();
            var time_start = $(this).find('.irrigation_time').val();
            json['rules'].push({
                "line_id": branch_id,
                'line_name': name,
                "time": time,
                "interval": interval,
                "time_wait": time_wait,
                "date_start": date_start,
                'time_start': time_start,
                'end_date': date_start
            });
        });
        console.log(json);
        // $.ajax({
        //     url: '/add_ongoing_rule',
        //     type: "post",
        //     data: JSON.stringify(json),
        //     contentType: "application/json; charset=utf-8",
        //     dataType: "json",
        //     beforeSend: function(xhr, opts) {
        //         $('#go_plan').addClass("disabled");
        //     },
        //     success: function() {
        //         $('#go_plan').removeClass("disabled");
        //         window.location.replace("/#");
        //     },
        //     error: function() {
        //         alert("error");
        //         $('#go_plan').removeClass("disabled");
        //     }
        // });
    });
});