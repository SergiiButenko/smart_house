var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');

$(document).ready(function() {
    $(".card-rule").each(function() {
        form_text($(this))
    });
    set_events();
});


function form_text(el_in) {
    var card = $(el_in).closest('.top');

    var time = convertDateToUTC(new Date($(card).data('timer')));
    var minutes = $(card).data('time');
    var interval = $(card).data('intervals');
    var time_wait = $(card).data('time_wait');

    var options_time = {
        hour: "2-digit",
        minute: "2-digit"
    };

    $(card).find("#summary").html(
        'O ' + time.toLocaleTimeString("uk-UA", options_time) + ', ' +
        interval + ' рази, по ' + minutes + ' хвилин, з інтервалом в ' + time_wait + ' хвилин'
    );
}


function set_events() {
    $('.close').off().change(function(e) {
        var switcher = $(e.target);
        var returnVal = confirm("Видалити правило?");
        if (returnVal == false) {
            return;
        }
        console.log('remove')
        $.ajax({
            url: '/cancel_rule',
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
}